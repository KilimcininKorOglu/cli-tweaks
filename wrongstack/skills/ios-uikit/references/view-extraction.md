# View Extraction Patterns in UIKit

## 1. Extracting Custom Views

When a view controller's `viewDidLoad` grows large, extract visual components into their own `UIView` subclass. Follow the **flush-to-container** principle: the extracted view does not decide its own position or size -- the parent pins it into place.

### Flush-to-Container Principle

```swift
class ProfileView: UIView {

    // The view only builds its *internal* layout.
    // It NEVER sets its own frame, center, or external constraints.

    private let avatarImageView = UIImageView()
    private let nameLabel = UILabel()
    private let bioLabel = UILabel()

    override init(frame: CGRect) {
        super.init(frame: frame)
        style()
        layout()
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    private func style() {
        avatarImageView.contentMode = .scaleAspectFill
        avatarImageView.clipsToBounds = true
        avatarImageView.layer.cornerRadius = 40

        nameLabel.font = .preferredFont(forTextStyle: .headline)
        nameLabel.textColor = .label

        bioLabel.font = .preferredFont(forTextStyle: .body)
        bioLabel.textColor = .secondaryLabel
        bioLabel.numberOfLines = 0
    }

    private func layout() {
        avatarImageView.translatesAutoresizingMaskIntoConstraints = false
        nameLabel.translatesAutoresizingMaskIntoConstraints = false
        bioLabel.translatesAutoresizingMaskIntoConstraints = false

        addSubview(avatarImageView)
        addSubview(nameLabel)
        addSubview(bioLabel)

        NSLayoutConstraint.activate([
            avatarImageView.topAnchor.constraint(equalTo: topAnchor, constant: 16),
            avatarImageView.centerXAnchor.constraint(equalTo: centerXAnchor),
            avatarImageView.widthAnchor.constraint(equalToConstant: 80),
            avatarImageView.heightAnchor.constraint(equalToConstant: 80),

            nameLabel.topAnchor.constraint(equalTo: avatarImageView.bottomAnchor, constant: 12),
            nameLabel.centerXAnchor.constraint(equalTo: centerXAnchor),

            bioLabel.topAnchor.constraint(equalTo: nameLabel.bottomAnchor, constant: 8),
            bioLabel.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            bioLabel.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),
            bioLabel.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -16),
        ])
    }
}
```

The parent pins it flush:

```swift
class ProfileViewController: UIViewController {

    let profileView = ProfileView()

    override func viewDidLoad() {
        super.viewDidLoad()

        profileView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(profileView)

        // Flush to container -- the parent decides position and size
        NSLayoutConstraint.activate([
            profileView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            profileView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            profileView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            // bottomAnchor intentionally omitted: the view sizes itself via internal constraints
        ])
    }
}
```

### didSet Property Observer for Data Binding

Use `didSet` to push data into a custom view without the caller knowing about internal labels:

```swift
class WeatherView: UIView {

    private let temperatureLabel = UILabel()
    private let conditionLabel = UILabel()
    private let iconImageView = UIImageView()

    // Public data property with didSet binding
    var temperature: String = "" {
        didSet {
            temperatureLabel.text = temperature
        }
    }

    var condition: String = "" {
        didSet {
            conditionLabel.text = condition
            iconImageView.image = UIImage(systemName: iconName(for: condition))
        }
    }

    override init(frame: CGRect) {
        super.init(frame: frame)
        style()
        layout()
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    private func iconName(for condition: String) -> String {
        switch condition.lowercased() {
        case "sunny":  return "sun.max.fill"
        case "cloudy": return "cloud.fill"
        case "rainy":  return "cloud.rain.fill"
        default:       return "questionmark"
        }
    }

    private func style() {
        temperatureLabel.font = .systemFont(ofSize: 48, weight: .bold)
        conditionLabel.font = .preferredFont(forTextStyle: .title2)
        iconImageView.contentMode = .scaleAspectFit
        iconImageView.tintColor = .systemYellow
    }

    private func layout() {
        let stack = UIStackView(arrangedSubviews: [iconImageView, temperatureLabel, conditionLabel])
        stack.axis = .vertical
        stack.alignment = .center
        stack.spacing = 8
        stack.translatesAutoresizingMaskIntoConstraints = false

        addSubview(stack)

        NSLayoutConstraint.activate([
            stack.topAnchor.constraint(equalTo: topAnchor, constant: 24),
            stack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),
            stack.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -24),

            iconImageView.heightAnchor.constraint(equalToConstant: 64),
            iconImageView.widthAnchor.constraint(equalToConstant: 64),
        ])
    }
}

// Usage in a VC
let weatherView = WeatherView()
weatherView.temperature = "72F"
weatherView.condition = "Sunny"
```

### Lazy Properties

Use `lazy` when a subview needs access to `self` or should only be created on first access:

```swift
class FormView: UIView {

    lazy var submitButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("Submit", for: .normal)
        button.titleLabel?.font = .preferredFont(forTextStyle: .headline)
        button.backgroundColor = .systemBlue
        button.setTitleColor(.white, for: .normal)
        button.layer.cornerRadius = 8
        button.translatesAutoresizingMaskIntoConstraints = false
        // Can reference `self` because it is lazy
        button.addTarget(self, action: #selector(submitTapped), for: .touchUpInside)
        return button
    }()

    lazy var emailField: UITextField = {
        let field = UITextField()
        field.placeholder = "Email"
        field.borderStyle = .roundedRect
        field.keyboardType = .emailAddress
        field.autocapitalizationType = .none
        field.translatesAutoresizingMaskIntoConstraints = false
        return field
    }()

    @objc private func submitTapped() {
        print("Submitted: \(emailField.text ?? "")")
    }
}
```

---

## 2. Extracting Child View Controllers

When a section of screen has its own logic (networking, user interaction, state), extract it into a **child view controller** rather than just a view.

### 3-Step Lifecycle

```swift
class DashboardViewController: UIViewController {

    let statsVC = StatsViewController()

    override func viewDidLoad() {
        super.viewDidLoad()
        installStats()
    }

    private func installStats() {
        // Step 1: Register parent-child relationship
        addChild(statsVC)

        // Step 2: Insert into the view hierarchy
        view.addSubview(statsVC.view)
        statsVC.view.translatesAutoresizingMaskIntoConstraints = false

        NSLayoutConstraint.activate([
            statsVC.view.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            statsVC.view.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            statsVC.view.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            statsVC.view.heightAnchor.constraint(equalToConstant: 200),
        ])

        // Step 3: Notify the child the move is complete
        statsVC.didMove(toParent: self)
    }
}
```

### loadView() Override to Fill Entire VC

When a child VC is fully represented by a single custom view, override `loadView()` so the custom view **becomes** the VC's `view`:

```swift
class StatsViewController: UIViewController {

    let statsView = StatsView()

    // Replace the default UIView with our custom view
    override func loadView() {
        view = statsView
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        fetchStats()
    }

    private func fetchStats() {
        // After fetching data, push it into the view
        statsView.totalUsers = "12,345"
        statsView.activeToday = "1,024"
    }
}
```

```swift
class StatsView: UIView {

    private let totalUsersLabel = UILabel()
    private let activeTodayLabel = UILabel()

    var totalUsers: String = "" {
        didSet { totalUsersLabel.text = "Total Users: \(totalUsers)" }
    }

    var activeToday: String = "" {
        didSet { activeTodayLabel.text = "Active Today: \(activeToday)" }
    }

    override init(frame: CGRect) {
        super.init(frame: frame)
        backgroundColor = .secondarySystemBackground
        layer.cornerRadius = 12

        let stack = UIStackView(arrangedSubviews: [totalUsersLabel, activeTodayLabel])
        stack.axis = .vertical
        stack.spacing = 8
        stack.translatesAutoresizingMaskIntoConstraints = false

        addSubview(stack)
        NSLayoutConstraint.activate([
            stack.centerXAnchor.constraint(equalTo: centerXAnchor),
            stack.centerYAnchor.constraint(equalTo: centerYAnchor),
        ])
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
}
```

### Constraint Pinning Helper

A small extension to reduce boilerplate when pinning child views flush to a container:

```swift
extension UIView {

    /// Pin all four edges to another view (or its superview by default).
    func pinTo(_ target: UIView, padding: CGFloat = 0) {
        translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            topAnchor.constraint(equalTo: target.topAnchor, constant: padding),
            leadingAnchor.constraint(equalTo: target.leadingAnchor, constant: padding),
            trailingAnchor.constraint(equalTo: target.trailingAnchor, constant: -padding),
            bottomAnchor.constraint(equalTo: target.bottomAnchor, constant: -padding),
        ])
    }
}

// Usage
statsVC.view.pinTo(containerView)
```

---

## 3. View-ViewController Communication

### Closure-Based Handler Pattern

The extracted view exposes closures. The view controller sets them to handle events. This keeps the view free of business logic and the VC free of UI details.

```swift
class LoginView: UIView {

    // MARK: - Closures the VC will set

    var onLoginTapped: ((String, String) -> Void)?
    var onForgotPasswordTapped: (() -> Void)?

    // MARK: - Subviews

    private let usernameField = UITextField()
    private let passwordField = UITextField()

    private lazy var loginButton: UIButton = {
        let btn = UIButton(type: .system)
        btn.setTitle("Log In", for: .normal)
        btn.addTarget(self, action: #selector(loginTapped), for: .touchUpInside)
        return btn
    }()

    private lazy var forgotButton: UIButton = {
        let btn = UIButton(type: .system)
        btn.setTitle("Forgot Password?", for: .normal)
        btn.addTarget(self, action: #selector(forgotTapped), for: .touchUpInside)
        return btn
    }()

    // MARK: - Actions

    @objc private func loginTapped() {
        let user = usernameField.text ?? ""
        let pass = passwordField.text ?? ""
        onLoginTapped?(user, pass)
    }

    @objc private func forgotTapped() {
        onForgotPasswordTapped?()
    }

    // MARK: - Init

    override init(frame: CGRect) {
        super.init(frame: frame)
        style()
        layout()
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    private func style() {
        usernameField.placeholder = "Username"
        usernameField.borderStyle = .roundedRect

        passwordField.placeholder = "Password"
        passwordField.borderStyle = .roundedRect
        passwordField.isSecureTextEntry = true
    }

    private func layout() {
        let stack = UIStackView(arrangedSubviews: [
            usernameField, passwordField, loginButton, forgotButton
        ])
        stack.axis = .vertical
        stack.spacing = 12
        stack.translatesAutoresizingMaskIntoConstraints = false

        addSubview(stack)
        NSLayoutConstraint.activate([
            stack.centerYAnchor.constraint(equalTo: centerYAnchor),
            stack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 24),
            stack.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -24),
        ])
    }
}
```

```swift
class LoginViewController: UIViewController {

    let loginView = LoginView()

    override func loadView() {
        view = loginView
    }

    override func viewDidLoad() {
        super.viewDidLoad()

        loginView.onLoginTapped = { [weak self] username, password in
            self?.performLogin(username: username, password: password)
        }

        loginView.onForgotPasswordTapped = { [weak self] in
            let resetVC = PasswordResetViewController()
            self?.navigationController?.pushViewController(resetVC, animated: true)
        }
    }

    private func performLogin(username: String, password: String) {
        print("Logging in \(username)...")
        // Networking, validation, etc.
    }
}
```

---

## 4. Style-Layout Extension Pattern

Organize a view controller's setup code by splitting **styling** and **layout** into separate extensions. This keeps `viewDidLoad` concise and each concern easy to find.

```swift
class SettingsViewController: UIViewController {

    let headerLabel = UILabel()
    let darkModeSwitch = UISwitch()
    let darkModeLabel = UILabel()
    let notificationsSwitch = UISwitch()
    let notificationsLabel = UILabel()
    let saveButton = UIButton(type: .system)

    override func viewDidLoad() {
        super.viewDidLoad()
        style()
        layout()
    }
}

// MARK: - Style
extension SettingsViewController {

    func style() {
        view.backgroundColor = .systemBackground

        headerLabel.text = "Settings"
        headerLabel.font = .preferredFont(forTextStyle: .largeTitle)

        darkModeLabel.text = "Dark Mode"
        darkModeLabel.font = .preferredFont(forTextStyle: .body)

        notificationsLabel.text = "Notifications"
        notificationsLabel.font = .preferredFont(forTextStyle: .body)

        saveButton.setTitle("Save", for: .normal)
        saveButton.titleLabel?.font = .preferredFont(forTextStyle: .headline)
        saveButton.backgroundColor = .systemGreen
        saveButton.setTitleColor(.white, for: .normal)
        saveButton.layer.cornerRadius = 8
        saveButton.addTarget(self, action: #selector(saveTapped), for: .touchUpInside)
    }

    @objc func saveTapped() {
        print("Settings saved")
    }
}

// MARK: - Layout
extension SettingsViewController {

    func layout() {
        let darkModeRow = makeRow(label: darkModeLabel, control: darkModeSwitch)
        let notificationsRow = makeRow(label: notificationsLabel, control: notificationsSwitch)

        let stack = UIStackView(arrangedSubviews: [
            headerLabel, darkModeRow, notificationsRow, saveButton
        ])
        stack.axis = .vertical
        stack.spacing = 20
        stack.translatesAutoresizingMaskIntoConstraints = false

        view.addSubview(stack)

        NSLayoutConstraint.activate([
            stack.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 24),
            stack.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 20),
            stack.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -20),

            saveButton.heightAnchor.constraint(equalToConstant: 48),
        ])
    }

    private func makeRow(label: UILabel, control: UIView) -> UIStackView {
        let row = UIStackView(arrangedSubviews: [label, control])
        row.axis = .horizontal
        row.distribution = .equalSpacing
        return row
    }
}
```

---

## 5. GameView Example

A complete extracted view that uses a stack view, an image, labels, and `didSet` data binding.

### The Extracted View

```swift
class GameView: UIView {

    // MARK: - Subviews

    private let heroImageView = UIImageView()
    private let titleLabel = UILabel()
    private let genreLabel = UILabel()
    private let ratingLabel = UILabel()
    private let descriptionLabel = UILabel()

    private lazy var infoStack: UIStackView = {
        let stack = UIStackView(arrangedSubviews: [
            titleLabel, genreLabel, ratingLabel, descriptionLabel
        ])
        stack.axis = .vertical
        stack.spacing = 8
        stack.alignment = .leading
        return stack
    }()

    private lazy var mainStack: UIStackView = {
        let stack = UIStackView(arrangedSubviews: [heroImageView, infoStack])
        stack.axis = .vertical
        stack.spacing = 16
        stack.alignment = .fill
        return stack
    }()

    // MARK: - Data Binding via didSet

    var gameName: String = "" {
        didSet { titleLabel.text = gameName }
    }

    var genre: String = "" {
        didSet { genreLabel.text = genre }
    }

    var rating: Double = 0 {
        didSet {
            let stars = String(repeating: "★", count: Int(rating))
                      + String(repeating: "☆", count: 5 - Int(rating))
            ratingLabel.text = stars + "  \(String(format: "%.1f", rating))"
        }
    }

    var gameDescription: String = "" {
        didSet { descriptionLabel.text = gameDescription }
    }

    var heroImage: UIImage? {
        didSet { heroImageView.image = heroImage }
    }

    // MARK: - Closures for communication

    var onPlayTapped: (() -> Void)?

    // MARK: - Init

    override init(frame: CGRect) {
        super.init(frame: frame)
        style()
        layout()
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    // MARK: - Style

    private func style() {
        backgroundColor = .systemBackground

        heroImageView.contentMode = .scaleAspectFill
        heroImageView.clipsToBounds = true
        heroImageView.layer.cornerRadius = 12
        heroImageView.backgroundColor = .systemGray5

        titleLabel.font = .systemFont(ofSize: 28, weight: .bold)
        titleLabel.textColor = .label

        genreLabel.font = .preferredFont(forTextStyle: .subheadline)
        genreLabel.textColor = .secondaryLabel

        ratingLabel.font = .preferredFont(forTextStyle: .body)
        ratingLabel.textColor = .systemOrange

        descriptionLabel.font = .preferredFont(forTextStyle: .body)
        descriptionLabel.textColor = .label
        descriptionLabel.numberOfLines = 0
    }

    // MARK: - Layout

    private func layout() {
        mainStack.translatesAutoresizingMaskIntoConstraints = false
        addSubview(mainStack)

        let playButton = makePlayButton()
        addSubview(playButton)

        NSLayoutConstraint.activate([
            heroImageView.heightAnchor.constraint(equalToConstant: 220),

            mainStack.topAnchor.constraint(equalTo: topAnchor, constant: 16),
            mainStack.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            mainStack.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),

            playButton.topAnchor.constraint(equalTo: mainStack.bottomAnchor, constant: 24),
            playButton.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            playButton.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),
            playButton.heightAnchor.constraint(equalToConstant: 50),
            playButton.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -16),
        ])
    }

    private func makePlayButton() -> UIButton {
        let button = UIButton(type: .system)
        button.setTitle("Play Now", for: .normal)
        button.titleLabel?.font = .systemFont(ofSize: 18, weight: .semibold)
        button.backgroundColor = .systemIndigo
        button.setTitleColor(.white, for: .normal)
        button.layer.cornerRadius = 10
        button.translatesAutoresizingMaskIntoConstraints = false
        button.addTarget(self, action: #selector(playTapped), for: .touchUpInside)
        return button
    }

    @objc private func playTapped() {
        onPlayTapped?()
    }
}
```

### The View Controller

```swift
class GameViewController: UIViewController {

    let gameView = GameView()

    override func loadView() {
        view = gameView
    }

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Game Detail"
        configureView()
        setupActions()
    }

    private func configureView() {
        // Data binding -- each didSet updates the corresponding label/image
        gameView.heroImage = UIImage(named: "zelda-hero")
        gameView.gameName = "The Legend of Zelda: Tears of the Kingdom"
        gameView.genre = "Action-Adventure"
        gameView.rating = 4.8
        gameView.gameDescription = """
            An epic adventure across the land and skies of Hyrule awaits. \
            Explore a massive open world, craft weapons, and uncover the secrets \
            of the ancient kingdom.
            """
    }

    private func setupActions() {
        gameView.onPlayTapped = { [weak self] in
            let launchVC = GameLaunchViewController()
            self?.navigationController?.pushViewController(launchVC, animated: true)
        }
    }
}
```
