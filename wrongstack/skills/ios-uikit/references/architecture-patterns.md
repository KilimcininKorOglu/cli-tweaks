# Architecture Patterns in UIKit

## 1. Default UIKit Architecture (4-Layer)

The standard architecture follows a clean separation: **Service -> ViewModel -> ViewController -> View**.

```
+-----------+      +-------------+      +------------------+      +--------+
|  Service  | ---> |  ViewModel  | ---> |  ViewController  | ---> |  View  |
+-----------+      +-------------+      +------------------+      +--------+
  Network /          Transforms           Owns ViewModel,          UIKit
  Persistence        raw data into         binds state to           components
                     display-ready         view updates
                     ViewData
```

### Service Layer

Handles networking, persistence, and external data sources. Returns raw model objects.

```swift
struct Weather {
    let city: String
    let temperatureCelsius: Double
    let condition: String
}

protocol WeatherServiceProtocol {
    func fetchWeather(for city: String, completion: @escaping (Result<Weather, Error>) -> Void)
}

final class WeatherService: WeatherServiceProtocol {

    private let session: URLSession

    init(session: URLSession = .shared) {
        self.session = session
    }

    func fetchWeather(for city: String, completion: @escaping (Result<Weather, Error>) -> Void) {
        guard let url = URL(string: "https://api.example.com/weather?city=\(city)") else {
            completion(.failure(WeatherError.invalidURL))
            return
        }

        session.dataTask(with: url) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }

            guard let data = data else {
                completion(.failure(WeatherError.noData))
                return
            }

            do {
                let weather = try JSONDecoder().decode(Weather.self, from: data)
                completion(.success(weather))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
}

enum WeatherError: LocalizedError {
    case invalidURL
    case noData

    var errorDescription: String? {
        switch self {
        case .invalidURL: return "The URL is invalid."
        case .noData:     return "No data was returned."
        }
    }
}
```

### ViewModel Layer

Transforms raw model data into display-ready values. Contains no UIKit imports.

```swift
struct WeatherViewData {
    let cityName: String
    let temperature: String
    let conditionIcon: String
    let backgroundColor: String   // hex color, not UIColor
}

final class WeatherViewModel {

    // MARK: - Published State

    private(set) var viewData: WeatherViewData?
    private(set) var isLoading: Bool = false
    private(set) var errorMessage: String?

    /// Called whenever any published state changes.
    var onStateChanged: (() -> Void)?

    // MARK: - Dependencies

    private let service: WeatherServiceProtocol

    init(service: WeatherServiceProtocol = WeatherService()) {
        self.service = service
    }

    // MARK: - Actions

    func loadWeather(for city: String) {
        isLoading = true
        errorMessage = nil
        onStateChanged?()

        service.fetchWeather(for: city) { [weak self] result in
            guard let self = self else { return }

            DispatchQueue.main.async {
                self.isLoading = false

                switch result {
                case .success(let weather):
                    self.viewData = self.transform(weather)
                case .failure(let error):
                    self.errorMessage = error.localizedDescription
                }

                self.onStateChanged?()
            }
        }
    }

    // MARK: - Private

    private func transform(_ weather: Weather) -> WeatherViewData {
        let icon: String
        switch weather.condition.lowercased() {
        case "sunny":  icon = "sun.max.fill"
        case "cloudy": icon = "cloud.fill"
        case "rainy":  icon = "cloud.rain.fill"
        default:       icon = "questionmark.circle"
        }

        return WeatherViewData(
            cityName: weather.city.uppercased(),
            temperature: String(format: "%.0f\u{00B0}C", weather.temperatureCelsius),
            conditionIcon: icon,
            backgroundColor: weather.temperatureCelsius > 25 ? "#FF6B35" : "#4A90D9"
        )
    }
}
```

### ViewController Layer

Owns the ViewModel, binds state changes to view updates, and forwards user actions to the ViewModel.

```swift
import UIKit

final class WeatherViewController: UIViewController {

    // MARK: - UI

    private let weatherView = WeatherDisplayView()

    // MARK: - Dependencies

    private let viewModel: WeatherViewModel

    // MARK: - Init

    init(viewModel: WeatherViewModel = WeatherViewModel()) {
        self.viewModel = viewModel
        super.init(nibName: nil, bundle: nil)
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    // MARK: - Lifecycle

    override func loadView() {
        view = weatherView
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        bindViewModel()
        weatherView.searchBar.delegate = self
    }

    // MARK: - Binding

    private func bindViewModel() {
        viewModel.onStateChanged = { [weak self] in
            guard let self = self else { return }

            if self.viewModel.isLoading {
                self.weatherView.showLoading()
                return
            }

            if let error = self.viewModel.errorMessage {
                self.weatherView.showError(error)
                return
            }

            if let data = self.viewModel.viewData {
                self.weatherView.configure(with: data)
            }
        }
    }
}

// MARK: - UISearchBarDelegate

extension WeatherViewController: UISearchBarDelegate {
    func searchBarSearchButtonClicked(_ searchBar: UISearchBar) {
        guard let city = searchBar.text, !city.isEmpty else { return }
        searchBar.resignFirstResponder()
        viewModel.loadWeather(for: city)
    }
}
```

### View Layer

Pure UIKit. Knows nothing about models or view models. Receives `ViewData` structs.

```swift
import UIKit

final class WeatherDisplayView: UIView {

    // MARK: - Subviews

    let searchBar: UISearchBar = {
        let bar = UISearchBar()
        bar.placeholder = "Enter city name"
        bar.translatesAutoresizingMaskIntoConstraints = false
        return bar
    }()

    private let cityLabel: UILabel = {
        let label = UILabel()
        label.font = .systemFont(ofSize: 28, weight: .bold)
        label.textAlignment = .center
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()

    private let temperatureLabel: UILabel = {
        let label = UILabel()
        label.font = .monospacedDigitSystemFont(ofSize: 64, weight: .medium)
        label.textAlignment = .center
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()

    private let conditionImageView: UIImageView = {
        let iv = UIImageView()
        iv.contentMode = .scaleAspectFit
        iv.tintColor = .white
        iv.translatesAutoresizingMaskIntoConstraints = false
        return iv
    }()

    private let activityIndicator: UIActivityIndicatorView = {
        let ai = UIActivityIndicatorView(style: .large)
        ai.hidesWhenStopped = true
        ai.translatesAutoresizingMaskIntoConstraints = false
        return ai
    }()

    private let errorLabel: UILabel = {
        let label = UILabel()
        label.font = .systemFont(ofSize: 16)
        label.textColor = .systemRed
        label.textAlignment = .center
        label.numberOfLines = 0
        label.isHidden = true
        label.translatesAutoresizingMaskIntoConstraints = false
        return label
    }()

    // MARK: - Init

    override init(frame: CGRect) {
        super.init(frame: frame)
        backgroundColor = .systemBackground
        setupLayout()
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    // MARK: - Layout

    private func setupLayout() {
        let stack = UIStackView(arrangedSubviews: [
            searchBar,
            conditionImageView,
            temperatureLabel,
            cityLabel,
            errorLabel
        ])
        stack.axis = .vertical
        stack.spacing = 16
        stack.alignment = .center
        stack.translatesAutoresizingMaskIntoConstraints = false

        addSubview(stack)
        addSubview(activityIndicator)

        NSLayoutConstraint.activate([
            stack.centerXAnchor.constraint(equalTo: centerXAnchor),
            stack.centerYAnchor.constraint(equalTo: centerYAnchor, constant: -40),
            stack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 20),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -20),

            conditionImageView.widthAnchor.constraint(equalToConstant: 100),
            conditionImageView.heightAnchor.constraint(equalToConstant: 100),

            activityIndicator.centerXAnchor.constraint(equalTo: centerXAnchor),
            activityIndicator.centerYAnchor.constraint(equalTo: centerYAnchor),
        ])
    }

    // MARK: - Public API

    func configure(with data: WeatherViewData) {
        activityIndicator.stopAnimating()
        errorLabel.isHidden = true

        cityLabel.text = data.cityName
        temperatureLabel.text = data.temperature
        conditionImageView.image = UIImage(systemName: data.conditionIcon)

        cityLabel.isHidden = false
        temperatureLabel.isHidden = false
        conditionImageView.isHidden = false
    }

    func showLoading() {
        activityIndicator.startAnimating()
        errorLabel.isHidden = true
        cityLabel.isHidden = true
        temperatureLabel.isHidden = true
        conditionImageView.isHidden = true
    }

    func showError(_ message: String) {
        activityIndicator.stopAnimating()
        errorLabel.text = message
        errorLabel.isHidden = false
        cityLabel.isHidden = true
        temperatureLabel.isHidden = true
        conditionImageView.isHidden = true
    }
}
```

---

## 2. Protocol-Delegate Communication

The delegate pattern decouples a service from its consumer using a protocol with `weak` reference to prevent retain cycles.

### Defining the Delegate Protocol

```swift
protocol WeatherServiceDelegate: AnyObject {
    /// Called when weather data is successfully fetched.
    func weatherService(_ service: WeatherService, didFetchWeather weather: Weather)

    /// Called when fetching weather data fails.
    func weatherService(_ service: WeatherService, didFailWithError error: Error)

    /// Called when the download progress updates.
    func weatherService(_ service: WeatherService, didUpdateProgress progress: Double)
}

// Optional methods via default implementations
extension WeatherServiceDelegate {
    func weatherService(_ service: WeatherService, didUpdateProgress progress: Double) {
        // Default: do nothing. Conformers opt in by overriding.
    }
}
```

### The Service with a Weak Delegate

```swift
final class WeatherService {

    // MARK: - Delegate (weak to avoid retain cycle)

    weak var delegate: WeatherServiceDelegate?

    // MARK: - Fetch

    func fetchWeather(for city: String) {
        guard let url = URL(string: "https://api.example.com/weather?city=\(city)") else {
            delegate?.weatherService(self, didFailWithError: WeatherError.invalidURL)
            return
        }

        // Simulate progress
        delegate?.weatherService(self, didUpdateProgress: 0.0)

        URLSession.shared.dataTask(with: url) { [weak self] data, _, error in
            guard let self = self else { return }

            DispatchQueue.main.async {
                if let error = error {
                    self.delegate?.weatherService(self, didFailWithError: error)
                    return
                }

                guard let data = data else {
                    self.delegate?.weatherService(self, didFailWithError: WeatherError.noData)
                    return
                }

                do {
                    let weather = try JSONDecoder().decode(Weather.self, from: data)
                    self.delegate?.weatherService(self, didUpdateProgress: 1.0)
                    self.delegate?.weatherService(self, didFetchWeather: weather)
                } catch {
                    self.delegate?.weatherService(self, didFailWithError: error)
                }
            }
        }.resume()
    }
}
```

### Conforming ViewController

```swift
final class WeatherViewController: UIViewController {

    private let service = WeatherService()
    private let progressView = UIProgressView(progressViewStyle: .default)

    override func viewDidLoad() {
        super.viewDidLoad()
        service.delegate = self   // assign self as delegate
        service.fetchWeather(for: "London")
    }
}

extension WeatherViewController: WeatherServiceDelegate {

    func weatherService(_ service: WeatherService, didFetchWeather weather: Weather) {
        print("Received: \(weather.city) - \(weather.temperatureCelsius)\u{00B0}C")
        // update UI...
    }

    func weatherService(_ service: WeatherService, didFailWithError error: Error) {
        let alert = UIAlertController(
            title: "Error",
            message: error.localizedDescription,
            preferredStyle: .alert
        )
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }

    func weatherService(_ service: WeatherService, didUpdateProgress progress: Double) {
        progressView.setProgress(Float(progress), animated: true)
    }
}
```

### Why `weak var delegate`?

```
ViewController ----strong----> Service
ViewController <---weak------- Service.delegate

Without `weak`:
ViewController ----strong----> Service
ViewController <---strong----- Service.delegate   // RETAIN CYCLE - neither is ever freed
```

---

## 3. Closure-Based Communication

Closures are ideal for one-shot callbacks. They capture context at the call site.

### Result Handler Pattern

```swift
final class WeatherService {

    typealias WeatherResult = Result<Weather, Error>
    typealias WeatherCompletion = (WeatherResult) -> Void

    func fetchWeather(for city: String, completion: @escaping WeatherCompletion) {
        guard let url = URL(string: "https://api.example.com/weather?city=\(city)") else {
            completion(.failure(WeatherError.invalidURL))
            return
        }

        URLSession.shared.dataTask(with: url) { data, _, error in
            if let error = error {
                DispatchQueue.main.async { completion(.failure(error)) }
                return
            }

            guard let data = data else {
                DispatchQueue.main.async { completion(.failure(WeatherError.noData)) }
                return
            }

            do {
                let weather = try JSONDecoder().decode(Weather.self, from: data)
                DispatchQueue.main.async { completion(.success(weather)) }
            } catch {
                DispatchQueue.main.async { completion(.failure(error)) }
            }
        }.resume()
    }
}
```

### Inline Closure (Trailing Closure Syntax)

```swift
final class WeatherViewController: UIViewController {

    private let service = WeatherService()

    func loadWeather() {
        service.fetchWeather(for: "Tokyo") { [weak self] result in
            guard let self = self else { return }

            switch result {
            case .success(let weather):
                self.updateUI(with: weather)
            case .failure(let error):
                self.showError(error)
            }
        }
    }

    private func updateUI(with weather: Weather) { /* ... */ }
    private func showError(_ error: Error) { /* ... */ }
}
```

### Named Closure (Extracted for Readability)

```swift
final class WeatherViewController: UIViewController {

    private let service = WeatherService()

    func loadWeather() {
        service.fetchWeather(for: "Tokyo", completion: handleWeatherResult)
    }

    // Named closure stored as a lazy property (captures self weakly).
    private lazy var handleWeatherResult: (Result<Weather, Error>) -> Void = { [weak self] result in
        guard let self = self else { return }

        switch result {
        case .success(let weather):
            self.updateUI(with: weather)
        case .failure(let error):
            self.showError(error)
        }
    }

    private func updateUI(with weather: Weather) { /* ... */ }
    private func showError(_ error: Error) { /* ... */ }
}
```

### `[weak self]` vs `[unowned self]`

```swift
// SAFE: [weak self] - self becomes nil if deallocated
service.fetchWeather(for: "Berlin") { [weak self] result in
    guard let self = self else { return }   // bail out if self is gone
    self.updateUI(with: result)
}

// DANGEROUS: [unowned self] - crashes if self is deallocated
// Only use when you can GUARANTEE self outlives the closure.
service.fetchWeather(for: "Berlin") { [unowned self] result in
    self.updateUI(with: result)   // crashes if VC was dismissed before callback
}
```

### Closure with Multiple Callbacks (Progress + Completion)

```swift
final class DownloadService {

    func download(
        url: URL,
        onProgress: @escaping (Double) -> Void,
        onCompletion: @escaping (Result<Data, Error>) -> Void
    ) {
        // Simulated incremental progress
        DispatchQueue.global().async {
            for i in 1...10 {
                Thread.sleep(forTimeInterval: 0.1)
                DispatchQueue.main.async { onProgress(Double(i) / 10.0) }
            }
            DispatchQueue.main.async { onCompletion(.success(Data())) }
        }
    }
}

// Usage
let service = DownloadService()
service.download(
    url: someURL,
    onProgress: { progress in
        print("Progress: \(Int(progress * 100))%")
    },
    onCompletion: { [weak self] result in
        guard let self = self else { return }
        switch result {
        case .success(let data): self.process(data)
        case .failure(let error): self.showError(error)
        }
    }
)
```

---

## 4. MVP Pattern

In MVP the **Presenter** owns the business logic and tells the **View** (the UIViewController) what to display through a `PresenterView` protocol.

```
+----------+       +-------------+       +----------------------+
|  Model   | <---- |  Presenter  | ----> |  View (VC)           |
|          |       |             |       |  conforms to         |
|          |       |             |       |  PresenterView       |
+----------+       +-------------+       +----------------------+
                     ^
                     | user actions forwarded
                     | from ViewController
```

### ViewData (Display-Ready Struct)

```swift
struct WeatherViewData {
    let title: String
    let temperature: String
    let iconName: String
}
```

### PresenterView Protocol (What the Presenter Can Tell the View)

```swift
protocol WeatherPresenterView: AnyObject {
    func showLoading()
    func hideLoading()
    func display(_ viewData: WeatherViewData)
    func displayError(_ message: String)
}
```

### Presenter

```swift
final class WeatherPresenter {

    // MARK: - References

    private weak var view: WeatherPresenterView?
    private let service: WeatherServiceProtocol

    // MARK: - Init

    init(view: WeatherPresenterView, service: WeatherServiceProtocol = WeatherService()) {
        self.view = view
        self.service = service
    }

    // MARK: - Actions (called by the ViewController)

    func viewDidLoad() {
        loadWeather(for: "San Francisco")
    }

    func didSearchCity(_ city: String) {
        loadWeather(for: city)
    }

    // MARK: - Private

    private func loadWeather(for city: String) {
        view?.showLoading()

        service.fetchWeather(for: city) { [weak self] result in
            guard let self = self else { return }

            self.view?.hideLoading()

            switch result {
            case .success(let weather):
                let viewData = WeatherViewData(
                    title: weather.city,
                    temperature: String(format: "%.0f\u{00B0}C", weather.temperatureCelsius),
                    iconName: self.iconName(for: weather.condition)
                )
                self.view?.display(viewData)

            case .failure(let error):
                self.view?.displayError(error.localizedDescription)
            }
        }
    }

    private func iconName(for condition: String) -> String {
        switch condition.lowercased() {
        case "sunny":  return "sun.max.fill"
        case "cloudy": return "cloud.fill"
        case "rainy":  return "cloud.rain.fill"
        default:       return "questionmark.circle"
        }
    }
}
```

### View (UIViewController Conforming to PresenterView)

```swift
import UIKit

final class WeatherViewController: UIViewController {

    // MARK: - UI

    private let cityLabel = UILabel()
    private let tempLabel = UILabel()
    private let iconView = UIImageView()
    private let spinner = UIActivityIndicatorView(style: .large)
    private let searchBar = UISearchBar()

    // MARK: - Presenter (strong reference VC -> Presenter)

    private var presenter: WeatherPresenter!

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        presenter = WeatherPresenter(view: self)   // injects self as PresenterView
        searchBar.delegate = self
        setupLayout()
        presenter.viewDidLoad()
    }

    private func setupLayout() { /* Auto Layout setup omitted for brevity */ }
}

// MARK: - WeatherPresenterView

extension WeatherViewController: WeatherPresenterView {

    func showLoading() {
        spinner.startAnimating()
        cityLabel.isHidden = true
        tempLabel.isHidden = true
        iconView.isHidden = true
    }

    func hideLoading() {
        spinner.stopAnimating()
    }

    func display(_ viewData: WeatherViewData) {
        cityLabel.text = viewData.title
        tempLabel.text = viewData.temperature
        iconView.image = UIImage(systemName: viewData.iconName)
        cityLabel.isHidden = false
        tempLabel.isHidden = false
        iconView.isHidden = false
    }

    func displayError(_ message: String) {
        let alert = UIAlertController(title: "Error", message: message, preferredStyle: .alert)
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }
}

// MARK: - UISearchBarDelegate

extension WeatherViewController: UISearchBarDelegate {
    func searchBarSearchButtonClicked(_ searchBar: UISearchBar) {
        guard let city = searchBar.text, !city.isEmpty else { return }
        searchBar.resignFirstResponder()
        presenter.didSearchCity(city)
    }
}
```

### Testing the Presenter (Unit Test)

```swift
import XCTest

final class MockWeatherView: WeatherPresenterView {
    var isLoadingShown = false
    var isLoadingHidden = false
    var displayedViewData: WeatherViewData?
    var displayedError: String?

    func showLoading()                      { isLoadingShown = true }
    func hideLoading()                      { isLoadingHidden = true }
    func display(_ viewData: WeatherViewData) { displayedViewData = viewData }
    func displayError(_ message: String)    { displayedError = message }
}

final class StubWeatherService: WeatherServiceProtocol {
    var stubbedResult: Result<Weather, Error> = .failure(WeatherError.noData)

    func fetchWeather(for city: String, completion: @escaping (Result<Weather, Error>) -> Void) {
        completion(stubbedResult)
    }
}

final class WeatherPresenterTests: XCTestCase {

    func test_viewDidLoad_displaysWeather_onSuccess() {
        let mockView = MockWeatherView()
        let stubService = StubWeatherService()
        stubService.stubbedResult = .success(
            Weather(city: "Paris", temperatureCelsius: 22.0, condition: "sunny")
        )
        let presenter = WeatherPresenter(view: mockView, service: stubService)

        presenter.viewDidLoad()

        XCTAssertTrue(mockView.isLoadingShown)
        XCTAssertTrue(mockView.isLoadingHidden)
        XCTAssertEqual(mockView.displayedViewData?.title, "Paris")
        XCTAssertEqual(mockView.displayedViewData?.temperature, "22\u{00B0}C")
        XCTAssertNil(mockView.displayedError)
    }

    func test_viewDidLoad_displaysError_onFailure() {
        let mockView = MockWeatherView()
        let stubService = StubWeatherService()
        stubService.stubbedResult = .failure(WeatherError.noData)
        let presenter = WeatherPresenter(view: mockView, service: stubService)

        presenter.viewDidLoad()

        XCTAssertNotNil(mockView.displayedError)
        XCTAssertNil(mockView.displayedViewData)
    }
}
```

---

## 5. Comparison Table: Protocol-Delegate vs Closures

| Aspect                | Protocol-Delegate                                                                     | Closures                                                                |
| --------------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **Coupling**          | Low -- communicates through a protocol contract                                       | Slightly higher -- closure captures call-site context                   |
| **Number of methods** | Scales well for many callbacks (multiple delegate methods)                            | Best for 1-2 callbacks; many closures clutter the API                   |
| **Flexibility**       | Single delegate at a time (1:1 relationship)                                          | Each call site can supply a different closure                           |
| **Optional methods**  | Via default protocol extension implementations                                        | Via optional closure properties (`var onProgress: ((Double) -> Void)?`) |
| **Testing**           | Easy -- inject a mock conforming to the protocol                                      | Easy -- pass a closure that records calls                               |
| **Error handling**    | Separate delegate method for errors (`didFailWithError`)                              | `Result` type combines success and error in one callback                |
| **Memory management** | `weak var delegate` prevents retain cycles                                            | `[weak self]` in capture list required to prevent retain cycles         |
| **Readability**       | Clear contract visible at protocol declaration                                        | Logic is inline at call site -- easy to follow for simple cases         |
| **State**             | Delegate object can hold state across multiple callbacks                              | Closures are stateless unless they capture mutable variables            |
| **Best for**          | Sustained, multi-event communication (table view data source, long-lived connections) | One-shot async operations (network calls, animations, alerts)           |

### Rule of Thumb

```
Use DELEGATE when:
  - The object will call back multiple times over its lifetime
  - You need many distinct callback methods
  - Examples: UITableViewDelegate, UITextFieldDelegate, custom services with progress

Use CLOSURES when:
  - You need a single, one-shot callback
  - The callback is tightly coupled to the call site
  - Examples: network completion handlers, animation completions, alert actions
```
