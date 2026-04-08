# Communication Patterns in UIKit

## 1. Protocol-Delegate

The delegate pattern uses a protocol to define a communication contract between two objects. For complex scenarios, split responsibilities into a **Delegate** (events) and a **DataSource** (data supply).

### Two-Protocol Pattern: Delegate + DataSource

```swift
// MARK: - Protocols

/// Events / user actions flow through the delegate.
protocol ItemListDelegate: AnyObject {
    func itemList(_ list: ItemListView, didSelectItemAt index: Int)
    func itemList(_ list: ItemListView, didDeleteItemAt index: Int)
    func itemListDidPullToRefresh(_ list: ItemListView)
}

/// Data supply flows through the data source.
protocol ItemListDataSource: AnyObject {
    func numberOfItems(in list: ItemListView) -> Int
    func itemList(_ list: ItemListView, titleForItemAt index: Int) -> String
    func itemList(_ list: ItemListView, subtitleForItemAt index: Int) -> String?
}

// Optional methods via default implementations
extension ItemListDelegate {
    func itemList(_ list: ItemListView, didDeleteItemAt index: Int) { }
}

extension ItemListDataSource {
    func itemList(_ list: ItemListView, subtitleForItemAt index: Int) -> String? { nil }
}
```

### The View Using Both Protocols

```swift
import UIKit

final class ItemListView: UIView {

    // MARK: - Delegates (both weak)

    weak var delegate: ItemListDelegate?
    weak var dataSource: ItemListDataSource? {
        didSet { reloadData() }
    }

    // MARK: - Subviews

    private let tableView = UITableView()
    private let refreshControl = UIRefreshControl()

    // MARK: - Init

    override init(frame: CGRect) {
        super.init(frame: frame)
        tableView.dataSource = self
        tableView.delegate = self
        tableView.register(UITableViewCell.self, forCellReuseIdentifier: "Cell")

        refreshControl.addTarget(self, action: #selector(didPullToRefresh), for: .valueChanged)
        tableView.refreshControl = refreshControl

        addSubview(tableView)
        tableView.frame = bounds
        tableView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    // MARK: - Public

    func reloadData() {
        tableView.reloadData()
        refreshControl.endRefreshing()
    }

    // MARK: - Actions

    @objc private func didPullToRefresh() {
        delegate?.itemListDidPullToRefresh(self)
    }
}

// MARK: - UITableViewDataSource

extension ItemListView: UITableViewDataSource {

    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        dataSource?.numberOfItems(in: self) ?? 0
    }

    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: "Cell", for: indexPath)
        var config = cell.defaultContentConfiguration()
        config.text = dataSource?.itemList(self, titleForItemAt: indexPath.row)
        config.secondaryText = dataSource?.itemList(self, subtitleForItemAt: indexPath.row)
        cell.contentConfiguration = config
        return cell
    }
}

// MARK: - UITableViewDelegate

extension ItemListView: UITableViewDelegate {

    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        tableView.deselectRow(at: indexPath, animated: true)
        delegate?.itemList(self, didSelectItemAt: indexPath.row)
    }

    func tableView(
        _ tableView: UITableView,
        commit editingStyle: UITableViewCell.EditingStyle,
        forRowAt indexPath: IndexPath
    ) {
        if editingStyle == .delete {
            delegate?.itemList(self, didDeleteItemAt: indexPath.row)
        }
    }
}
```

### ViewController Conforming to Both

```swift
final class ItemListViewController: UIViewController {

    private let listView = ItemListView()
    private var items = ["Alpha", "Bravo", "Charlie", "Delta"]

    override func loadView() {
        view = listView
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        listView.delegate = self
        listView.dataSource = self
    }
}

// MARK: - ItemListDelegate

extension ItemListViewController: ItemListDelegate {

    func itemList(_ list: ItemListView, didSelectItemAt index: Int) {
        print("Selected: \(items[index])")
    }

    func itemList(_ list: ItemListView, didDeleteItemAt index: Int) {
        items.remove(at: index)
        listView.reloadData()
    }

    func itemListDidPullToRefresh(_ list: ItemListView) {
        // Simulate network refresh
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) { [weak self] in
            self?.listView.reloadData()
        }
    }
}

// MARK: - ItemListDataSource

extension ItemListViewController: ItemListDataSource {

    func numberOfItems(in list: ItemListView) -> Int {
        items.count
    }

    func itemList(_ list: ItemListView, titleForItemAt index: Int) -> String {
        items[index]
    }
}
```

---

## 2. Closures

### Simple Completion Closure

```swift
final class ImageLoader {

    func loadImage(from url: URL, completion: @escaping (UIImage?) -> Void) {
        URLSession.shared.dataTask(with: url) { data, _, _ in
            let image = data.flatMap { UIImage(data: $0) }
            DispatchQueue.main.async {
                completion(image)
            }
        }.resume()
    }
}

// Usage
let loader = ImageLoader()
loader.loadImage(from: someURL) { [weak self] image in
    self?.imageView.image = image
}
```

### Returning a Closure (Factory Pattern)

```swift
func makeValidator(minLength: Int) -> (String) -> Bool {
    return { input in
        input.count >= minLength
    }
}

let validatePassword = makeValidator(minLength: 8)
let validateUsername = makeValidator(minLength: 3)

validatePassword("abc")       // false
validatePassword("secure123") // true
validateUsername("ab")        // false
validateUsername("joe")       // true
```

### Closure with `Result` Type

```swift
enum NetworkError: Error {
    case badStatusCode(Int)
    case decodingFailed
    case unknown
}

final class APIClient {

    func fetch<T: Decodable>(
        _ type: T.Type,
        from url: URL,
        completion: @escaping (Result<T, NetworkError>) -> Void
    ) {
        URLSession.shared.dataTask(with: url) { data, response, error in
            DispatchQueue.main.async {
                if error != nil {
                    completion(.failure(.unknown))
                    return
                }

                if let http = response as? HTTPURLResponse, !(200...299).contains(http.statusCode) {
                    completion(.failure(.badStatusCode(http.statusCode)))
                    return
                }

                guard let data = data else {
                    completion(.failure(.unknown))
                    return
                }

                do {
                    let decoded = try JSONDecoder().decode(T.self, from: data)
                    completion(.success(decoded))
                } catch {
                    completion(.failure(.decodingFailed))
                }
            }
        }.resume()
    }
}

// Usage
struct User: Decodable {
    let id: Int
    let name: String
}

let client = APIClient()
client.fetch(User.self, from: usersURL) { result in
    switch result {
    case .success(let user):
        print("Fetched user: \(user.name)")
    case .failure(.badStatusCode(let code)):
        print("Server error: \(code)")
    case .failure(.decodingFailed):
        print("Could not parse response")
    case .failure(.unknown):
        print("Something went wrong")
    }
}
```

### Stored Closure Properties on a View

```swift
final class RatingView: UIView {

    /// Called when the user taps a star.
    var onRatingChanged: ((Int) -> Void)?

    /// Called when the user taps "Submit".
    var onSubmit: (() -> Void)?

    private var currentRating = 0

    @objc private func starTapped(_ sender: UIButton) {
        currentRating = sender.tag
        onRatingChanged?(currentRating)
    }

    @objc private func submitTapped() {
        onSubmit?()
    }
}

// In the ViewController
let ratingView = RatingView()
ratingView.onRatingChanged = { [weak self] rating in
    self?.selectedRating = rating
}
ratingView.onSubmit = { [weak self] in
    self?.submitReview()
}
```

---

## 3. KVO (Key-Value Observing)

KVO lets you observe changes to a property without the observed object knowing about its observers. The property must be `@objc dynamic` and the class must inherit from `NSObject`.

### Requirements

```swift
import Foundation

// The observed class MUST inherit from NSObject.
// The observed property MUST be marked @objc dynamic.
final class DownloadTask: NSObject {

    @objc dynamic var progress: Double = 0.0
    @objc dynamic var state: String = "idle"

    func start() {
        state = "downloading"
        // Simulate download
        DispatchQueue.global().async { [weak self] in
            for i in 1...100 {
                Thread.sleep(forTimeInterval: 0.02)
                DispatchQueue.main.async {
                    self?.progress = Double(i) / 100.0
                }
            }
            DispatchQueue.main.async {
                self?.state = "completed"
            }
        }
    }
}
```

### Observing with KeyPath

```swift
import UIKit

final class DownloadViewController: UIViewController {

    private let task = DownloadTask()
    private let progressView = UIProgressView(progressViewStyle: .default)
    private let statusLabel = UILabel()

    // Hold strong references to observations; they auto-invalidate on deinit.
    private var progressObservation: NSKeyValueObservation?
    private var stateObservation: NSKeyValueObservation?

    override func viewDidLoad() {
        super.viewDidLoad()

        // Observe `progress` using Swift KeyPath syntax
        progressObservation = task.observe(\.progress, options: [.new]) { [weak self] task, change in
            guard let newValue = change.newValue else { return }
            self?.progressView.setProgress(Float(newValue), animated: true)
        }

        // Observe `state` with both old and new values
        stateObservation = task.observe(\.state, options: [.old, .new]) { [weak self] task, change in
            guard let newState = change.newValue else { return }
            let oldState = change.oldValue ?? "unknown"
            print("State changed: \(oldState) -> \(newState)")
            self?.statusLabel.text = newState.capitalized
        }

        task.start()
    }

    deinit {
        // Observations are automatically invalidated when
        // NSKeyValueObservation instances are deallocated,
        // but explicit cleanup is fine for clarity.
        progressObservation?.invalidate()
        stateObservation?.invalidate()
    }
}
```

### Observation Lifecycle Rules

```swift
// 1. Store the observation token -- if it is released, observation stops.
//    BAD: observation dies immediately
task.observe(\.progress, options: [.new]) { _, _ in }  // nobody holds the return value

//    GOOD: stored in a property
self.observation = task.observe(\.progress, options: [.new]) { _, _ in /* ... */ }

// 2. The observation auto-invalidates when the token is deallocated.
//    No need for removeObserver(_:forKeyPath:) with the modern API.

// 3. Always use [weak self] in the closure to prevent retain cycles.
//    The NSKeyValueObservation retains the closure, and if the closure
//    retains self, self will never be released.

// 4. Available options:
//    .old       -- include the previous value in the change dictionary
//    .new       -- include the new value
//    .initial   -- fire the handler immediately with the current value
//    .prior     -- fire before AND after the change
```

### Observing a UIKit Property

```swift
// UIKit scroll offset is KVO-compliant.
final class ScrollTracker: NSObject {

    private var scrollObservation: NSKeyValueObservation?

    func track(_ scrollView: UIScrollView) {
        scrollObservation = scrollView.observe(
            \.contentOffset,
            options: [.new]
        ) { scrollView, change in
            guard let offset = change.newValue else { return }
            print("Scrolled to y: \(offset.y)")
        }
    }
}
```

---

## 4. Responder Chain

The responder chain lets any object in the UIKit hierarchy handle an action without a direct reference to the handler. You send an action to `nil`, and UIKit walks the responder chain until someone responds.

### `addTarget(nil, action:)` Pattern

```swift
import UIKit

// MARK: - Define a selector that any responder can implement

// By convention, create an informal protocol (or @objc method) that
// responders opt into.

@objc protocol FavoriteActionResponder {
    func didTapFavorite(_ sender: Any?)
}

// MARK: - A Cell Deep in the View Hierarchy

final class ItemCell: UITableViewCell {

    private let favoriteButton = UIButton(type: .system)

    override init(style: UITableViewCell.CellStyle, reuseIdentifier: String?) {
        super.init(style: style, reuseIdentifier: reuseIdentifier)

        favoriteButton.setImage(UIImage(systemName: "heart"), for: .normal)
        contentView.addSubview(favoriteButton)

        // TARGET IS nil -- UIKit sends up the responder chain
        favoriteButton.addTarget(nil, action: #selector(FavoriteActionResponder.didTapFavorite(_:)), for: .touchUpInside)
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
```

### Handling the Action in a ViewController

```swift
final class ItemListViewController: UITableViewController {

    private var items = [Item]()

    // This method will be found by the responder chain because
    // UITableViewController is a UIResponder.
    @objc func didTapFavorite(_ sender: Any?) {
        // Determine which cell triggered the action
        guard
            let button = sender as? UIButton,
            let cell = button.closestParent(ofType: UITableViewCell.self),
            let indexPath = tableView.indexPath(for: cell)
        else { return }

        items[indexPath.row].isFavorite.toggle()
        tableView.reloadRows(at: [indexPath], with: .automatic)
    }
}
```

### Helper: Finding the Nearest Parent of a Given Type

```swift
extension UIView {
    /// Walk up the view hierarchy to find the nearest parent of a specific type.
    func closestParent<T: UIView>(ofType type: T.Type) -> T? {
        var current: UIView? = superview
        while let view = current {
            if let match = view as? T { return match }
            current = view.superview
        }
        return nil
    }
}
```

### Passing Data via a Custom Sender

When you need to attach data to the responder chain event, wrap it in a custom sender.

```swift
final class FavoriteAction: NSObject {
    let itemID: String

    init(itemID: String) {
        self.itemID = itemID
    }
}

// In the cell:
final class ItemCell: UITableViewCell {

    var itemID: String = ""

    @objc private func favoriteTapped() {
        let action = FavoriteAction(itemID: itemID)
        // Send through responder chain manually
        UIApplication.shared.sendAction(
            #selector(FavoriteActionResponder.didTapFavorite(_:)),
            to: nil,           // nil = walk the responder chain
            from: action,      // custom sender carries data
            for: nil
        )
    }
}

// In the ViewController:
extension ItemListViewController {

    @objc override func didTapFavorite(_ sender: Any?) {
        guard let action = sender as? FavoriteAction else { return }
        print("Favorited item: \(action.itemID)")
        // toggle favorite for action.itemID ...
    }
}
```

### Selector Signature Variants

```swift
// UIKit accepts these selector signatures for control actions:

// 1. No parameters
@objc func buttonTapped() { }

// 2. Sender only
@objc func buttonTapped(_ sender: UIButton) { }

// 3. Sender + Event
@objc func buttonTapped(_ sender: UIButton, forEvent event: UIEvent) { }
```

---

## 5. Target-Action

The standard UIControl pattern for connecting user interface events to handler methods.

### Basic `addTarget` Usage

```swift
import UIKit

final class LoginViewController: UIViewController {

    private let usernameField = UITextField()
    private let passwordField = UITextField()
    private let loginButton = UIButton(type: .system)
    private let togglePasswordButton = UIButton(type: .system)

    override func viewDidLoad() {
        super.viewDidLoad()

        // Button tap
        loginButton.addTarget(self, action: #selector(loginTapped), for: .touchUpInside)

        // Text field editing events
        usernameField.addTarget(self, action: #selector(textFieldDidChange(_:)), for: .editingChanged)
        passwordField.addTarget(self, action: #selector(textFieldDidChange(_:)), for: .editingChanged)

        // Toggle password visibility
        togglePasswordButton.addTarget(self, action: #selector(togglePassword), for: .touchUpInside)
    }

    // MARK: - Actions

    @objc private func loginTapped() {
        guard let username = usernameField.text,
              let password = passwordField.text else { return }
        print("Logging in: \(username)")
        // perform login...
    }

    @objc private func textFieldDidChange(_ sender: UITextField) {
        let allFilled = !(usernameField.text ?? "").isEmpty
                     && !(passwordField.text ?? "").isEmpty
        loginButton.isEnabled = allFilled
        loginButton.alpha = allFilled ? 1.0 : 0.5
    }

    @objc private func togglePassword() {
        passwordField.isSecureTextEntry.toggle()
        let icon = passwordField.isSecureTextEntry ? "eye.slash" : "eye"
        togglePasswordButton.setImage(UIImage(systemName: icon), for: .normal)
    }
}
```

### Multiple Targets for One Control

```swift
// A single control can have multiple target-action pairs.
let slider = UISlider()

// Analytics tracking
slider.addTarget(analyticsTracker, action: #selector(AnalyticsTracker.sliderChanged(_:)), for: .valueChanged)

// UI update
slider.addTarget(self, action: #selector(updateLabel(_:)), for: .valueChanged)

// Both fire when the slider value changes.
```

### Removing a Target

```swift
// Remove a specific action
loginButton.removeTarget(self, action: #selector(loginTapped), for: .touchUpInside)

// Remove ALL actions for a target
loginButton.removeTarget(self, action: nil, for: .allEvents)

// Remove ALL targets
loginButton.removeTarget(nil, action: nil, for: .allEvents)
```

### UIControl.Event Quick Reference

```swift
// Common UIControl events:
//
// .touchUpInside    -- standard button tap (finger lifted inside control)
// .touchDown        -- finger touched down on control
// .touchUpOutside   -- finger lifted outside control
// .valueChanged     -- UISlider, UISwitch, UISegmentedControl value changed
// .editingChanged   -- UITextField text changed
// .editingDidBegin  -- UITextField became first responder
// .editingDidEnd    -- UITextField resigned first responder
// .primaryActionTriggered -- semantic action (works for UIButton, UITextField return key)
```

### iOS 14+ UIAction-Based Target-Action

```swift
// Modern alternative: UIAction closures (iOS 14+)
let button = UIButton(type: .system, primaryAction: UIAction(title: "Login") { [weak self] _ in
    self?.performLogin()
})

// Adding actions to existing controls
let slider = UISlider()
slider.addAction(UIAction { action in
    guard let slider = action.sender as? UISlider else { return }
    print("Value: \(slider.value)")
}, for: .valueChanged)
```

---

## 6. Ranking: When to Use Which

### Decision Flowchart

```
Is this a one-shot async callback?
  YES --> Use a CLOSURE with Result type
  NO  --> Is this a sustained, multi-event relationship?
            YES --> Use PROTOCOL-DELEGATE
            NO  --> Is this a UI control event?
                      YES --> Use TARGET-ACTION
                      NO  --> Do you need loose coupling across the view hierarchy?
                                YES --> Use RESPONDER CHAIN
                                NO  --> Do you need to observe a property you don't own?
                                          YES --> Use KVO
                                          NO  --> Use a CLOSURE
```

### Ranking by Preference

| Rank | Pattern               | When to Reach for It                                                                                                                                             |
| ---- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | **Closures**          | Default choice. One-shot callbacks, completion handlers, short-lived communication. Simple, inline, and easy to follow.                                          |
| 2    | **Protocol-Delegate** | Sustained multi-event communication. When you need multiple callback methods. When the relationship is long-lived (table views, text fields, custom components). |
| 3    | **Target-Action**     | UIControl events (button taps, slider changes, text edits). The built-in UIKit mechanism for controls.                                                           |
| 4    | **Responder Chain**   | Loose coupling across deep view hierarchies. When a deeply nested view needs to communicate with an ancestor it does not reference.                              |
| 5    | **KVO**               | Last resort for observing properties on objects you do not own (UIScrollView contentOffset, WKWebView estimatedProgress). Requires NSObject + @objc dynamic.     |

### Detailed Guidance

```swift
// ------------------------------------------------------------------
// 1. CLOSURES -- your default tool
// ------------------------------------------------------------------
// Use for: network calls, animations, alerts, any one-shot callback.
// Pros:    inline, contextual, easy to read at the call site.
// Cons:    can nest deeply ("callback hell"), must manage [weak self].

service.fetchUser(id: 42) { [weak self] result in
    // handle result
}

// ------------------------------------------------------------------
// 2. PROTOCOL-DELEGATE -- for sustained relationships
// ------------------------------------------------------------------
// Use for: table/collection views, text fields, custom multi-event components.
// Pros:    clean contract, multiple methods, optional methods via defaults.
// Cons:    more boilerplate, only one delegate at a time.

class MyVC: UIViewController, UITableViewDelegate, UITableViewDataSource {
    // multiple methods, long-lived relationship
}

// ------------------------------------------------------------------
// 3. TARGET-ACTION -- for UIControl events
// ------------------------------------------------------------------
// Use for: buttons, sliders, switches, text field editing events.
// Pros:    built-in UIKit mechanism, zero boilerplate.
// Cons:    requires @objc, limited to UIControl subclasses.

button.addTarget(self, action: #selector(tapped), for: .touchUpInside)

// ------------------------------------------------------------------
// 4. RESPONDER CHAIN -- for deeply nested views
// ------------------------------------------------------------------
// Use for: cell buttons that need to talk to a distant view controller,
//          menu actions, keyboard shortcuts.
// Pros:    zero coupling between sender and receiver.
// Cons:    implicit (hard to trace in code), receiver must be in the chain.

button.addTarget(nil, action: #selector(handleAction(_:)), for: .touchUpInside)

// ------------------------------------------------------------------
// 5. KVO -- observe what you cannot modify
// ------------------------------------------------------------------
// Use for: UIScrollView.contentOffset, WKWebView.estimatedProgress,
//          AVPlayer.status, third-party NSObject properties.
// Pros:    observe any KVO-compliant property without modifying the class.
// Cons:    NSObject + @objc dynamic required, easy to leak observations,
//          surprising ordering, hard to debug.

observation = scrollView.observe(\.contentOffset, options: [.new]) { _, change in
    // react to scroll
}
```

### Anti-Patterns to Avoid

```swift
// BAD: Using KVO when you control the class -- use a closure or delegate instead.
// BAD: Using NotificationCenter for 1:1 communication -- use a closure or delegate.
// BAD: Using a delegate for a single one-shot callback -- use a closure.
// BAD: Using closures for 5+ different callbacks on one object -- use a delegate protocol.
// BAD: Forgetting [weak self] in escaping closures -- causes retain cycles.
// BAD: Forgetting `weak var delegate` -- causes retain cycles.
// BAD: Using responder chain when a direct reference is readily available.
```
