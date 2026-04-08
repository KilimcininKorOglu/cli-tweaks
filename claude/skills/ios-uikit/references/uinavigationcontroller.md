# UINavigationController Reference

## 1. Large Titles

Large titles display a prominent, scrollable title that collapses into the standard navigation bar title when the user scrolls down.

### Enable Large Titles

```swift
class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?

    func scene(_ scene: UIScene,
               willConnectTo session: UISceneSession,
               options connectionOptions: UIScene.ConnectionOptions) {

        guard let windowScene = scene as? UIWindowScene else { return }
        let window = UIWindow(windowScene: windowScene)

        let rootVC = HomeViewController()
        let navController = UINavigationController(rootViewController: rootVC)

        // Enable large titles on the navigation bar itself
        navController.navigationBar.prefersLargeTitles = true

        window.rootViewController = navController
        window.makeKeyAndVisible()
        self.window = window
    }
}
```

### Per-ViewController Control

Each view controller can opt in or out of the large title via `largeTitleDisplayMode`:

```swift
class HomeViewController: UIViewController {

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Home"

        // .always   - always show large title on this VC
        // .never    - always show standard title on this VC
        // .automatic - inherit from the previous VC in the stack (default)
        navigationItem.largeTitleDisplayMode = .always
    }
}

class DetailViewController: UIViewController {

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Detail"
        navigationItem.largeTitleDisplayMode = .never
    }
}
```

### Styling Large Titles with NSAttributedString

```swift
class HomeViewController: UIViewController {

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Library"
        navigationItem.largeTitleDisplayMode = .always
        configureLargeTitleAppearance()
    }

    private func configureLargeTitleAppearance() {
        guard let navBar = navigationController?.navigationBar else { return }

        let appearance = UINavigationBarAppearance()
        appearance.configureWithOpaqueBackground()

        // Large title attributes
        appearance.largeTitleTextAttributes = [
            .foregroundColor: UIColor.systemIndigo,
            .font: UIFont.systemFont(ofSize: 36, weight: .black),
        ]

        // Standard (collapsed) title attributes
        appearance.titleTextAttributes = [
            .foregroundColor: UIColor.systemIndigo,
            .font: UIFont.systemFont(ofSize: 18, weight: .bold),
        ]

        navBar.standardAppearance = appearance
        navBar.scrollEdgeAppearance = appearance   // appearance when fully expanded
        navBar.compactAppearance = appearance       // landscape on smaller iPhones
    }
}
```

### Custom Shadow and Background

```swift
private func configureAppearance() {
    let appearance = UINavigationBarAppearance()
    appearance.configureWithOpaqueBackground()
    appearance.backgroundColor = .systemBackground

    // Remove the bottom shadow line
    appearance.shadowColor = .clear

    // Or set a custom shadow color
    // appearance.shadowColor = .separator

    appearance.largeTitleTextAttributes = [
        .foregroundColor: UIColor.label,
        .font: UIFont.systemFont(ofSize: 34, weight: .heavy),
    ]

    navigationController?.navigationBar.standardAppearance = appearance
    navigationController?.navigationBar.scrollEdgeAppearance = appearance
}
```

---

## 2. Hide on Interaction

UINavigationController can automatically hide the navigation bar when the user swipes or taps.

### Hide Bars on Swipe

Useful for content-heavy screens (e.g., reading, scrolling feeds):

```swift
class ArticleViewController: UIViewController {

    let textView = UITextView()

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Article"

        // The nav bar slides away when the user swipes up, returns on swipe down
        navigationController?.hidesBarsOnSwipe = true

        setupTextView()
    }

    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        // Reset so the next VC in the stack is not affected
        navigationController?.hidesBarsOnSwipe = false
    }

    private func setupTextView() {
        textView.translatesAutoresizingMaskIntoConstraints = false
        textView.font = .preferredFont(forTextStyle: .body)
        textView.text = String(repeating: "Lorem ipsum dolor sit amet. ", count: 200)
        view.addSubview(textView)

        NSLayoutConstraint.activate([
            textView.topAnchor.constraint(equalTo: view.topAnchor),
            textView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            textView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            textView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
        ])
    }
}
```

### Hide Bars on Tap

Useful for image viewers or media players:

```swift
class PhotoViewController: UIViewController {

    let imageView = UIImageView()

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Photo"

        // Tap anywhere to toggle the nav bar
        navigationController?.hidesBarsOnTap = true

        imageView.image = UIImage(named: "landscape")
        imageView.contentMode = .scaleAspectFit
        imageView.frame = view.bounds
        imageView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        view.addSubview(imageView)
    }

    override func viewWillDisappear(_ animated: Bool) {
        super.viewWillDisappear(animated)
        navigationController?.hidesBarsOnTap = false
        // Ensure the bar is visible for the next VC
        navigationController?.setNavigationBarHidden(false, animated: animated)
    }
}
```

### Programmatic Show/Hide

```swift
class GalleryViewController: UIViewController {

    private var isBarsHidden = false

    @objc func toggleBars() {
        isBarsHidden.toggle()
        navigationController?.setNavigationBarHidden(isBarsHidden, animated: true)
    }
}
```

---

## 3. Bar Button Items

### Creating Bar Button Items

```swift
class EditorViewController: UIViewController {

    // MARK: - Lazy Bar Button Items

    lazy var saveButton: UIBarButtonItem = {
        let button = UIBarButtonItem(
            title: "Save",
            style: .done,                                           // bold text
            target: self,
            action: #selector(saveTapped)
        )
        button.tintColor = .systemGreen
        return button
    }()

    lazy var cancelButton: UIBarButtonItem = {
        UIBarButtonItem(
            barButtonSystemItem: .cancel,
            target: self,
            action: #selector(cancelTapped)
        )
    }()

    lazy var shareButton: UIBarButtonItem = {
        UIBarButtonItem(
            image: UIImage(systemName: "square.and.arrow.up"),
            style: .plain,
            target: self,
            action: #selector(shareTapped)
        )
    }()

    lazy var addButton: UIBarButtonItem = {
        UIBarButtonItem(
            barButtonSystemItem: .add,
            target: self,
            action: #selector(addTapped)
        )
    }()

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Editor"

        // Left side items
        navigationItem.leftBarButtonItems = [cancelButton]

        // Right side items (displayed right-to-left)
        navigationItem.rightBarButtonItems = [saveButton, shareButton, addButton]
    }

    // MARK: - Actions

    @objc func saveTapped() {
        print("Saved")
    }

    @objc func cancelTapped() {
        dismiss(animated: true)
    }

    @objc func shareTapped() {
        let activityVC = UIActivityViewController(
            activityItems: ["Check out this content!"],
            applicationActivities: nil
        )
        present(activityVC, animated: true)
    }

    @objc func addTapped() {
        print("Add new item")
    }
}
```

### Custom View as a Bar Button Item

```swift
class SearchViewController: UIViewController {

    lazy var profileButton: UIBarButtonItem = {
        let imageView = UIImageView(image: UIImage(systemName: "person.crop.circle.fill"))
        imageView.tintColor = .systemBlue
        imageView.contentMode = .scaleAspectFit

        NSLayoutConstraint.activate([
            imageView.widthAnchor.constraint(equalToConstant: 32),
            imageView.heightAnchor.constraint(equalToConstant: 32),
        ])

        let tap = UITapGestureRecognizer(target: self, action: #selector(profileTapped))
        imageView.isUserInteractionEnabled = true
        imageView.addGestureRecognizer(tap)

        return UIBarButtonItem(customView: imageView)
    }()

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Search"
        navigationItem.rightBarButtonItem = profileButton
    }

    @objc func profileTapped() {
        let profileVC = ProfileViewController()
        navigationController?.pushViewController(profileVC, animated: true)
    }
}
```

### UIMenu-Based Bar Button (iOS 14+)

```swift
class ListViewController: UIViewController {

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Items"
        setupMenuButton()
    }

    private func setupMenuButton() {
        let sortByName = UIAction(title: "Name",
                                   image: UIImage(systemName: "textformat")) { _ in
            print("Sort by name")
        }

        let sortByDate = UIAction(title: "Date",
                                   image: UIImage(systemName: "calendar")) { _ in
            print("Sort by date")
        }

        let sortBySize = UIAction(title: "Size",
                                   image: UIImage(systemName: "arrow.up.arrow.down")) { _ in
            print("Sort by size")
        }

        let menu = UIMenu(title: "Sort By", children: [sortByName, sortByDate, sortBySize])

        let menuButton = UIBarButtonItem(
            image: UIImage(systemName: "line.3.horizontal.decrease.circle"),
            menu: menu
        )

        navigationItem.rightBarButtonItem = menuButton
    }
}
```

---

## 4. Navigation Styling

### Tint Color

The tint color affects bar button items and the back button:

```swift
class AppDelegate: UIResponder, UIApplicationDelegate {

    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {

        // Global tint affects all nav bars in the app
        UINavigationBar.appearance().tintColor = .systemPurple

        return true
    }
}
```

Per-navigation-controller tint:

```swift
override func viewDidLoad() {
    super.viewDidLoad()
    navigationController?.navigationBar.tintColor = .systemRed
}
```

### Background Color via UINavigationBarAppearance

```swift
class ThemedViewController: UIViewController {

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Themed"
        configureNavBarAppearance()
    }

    private func configureNavBarAppearance() {
        let appearance = UINavigationBarAppearance()

        // Opaque background (solid color, no blur)
        appearance.configureWithOpaqueBackground()
        appearance.backgroundColor = UIColor.systemTeal

        // Title color
        appearance.titleTextAttributes = [
            .foregroundColor: UIColor.white,
            .font: UIFont.systemFont(ofSize: 18, weight: .semibold),
        ]

        appearance.largeTitleTextAttributes = [
            .foregroundColor: UIColor.white,
        ]

        // Button appearance
        let buttonAppearance = UIBarButtonItemAppearance()
        buttonAppearance.normal.titleTextAttributes = [.foregroundColor: UIColor.white]
        appearance.buttonAppearance = buttonAppearance
        appearance.doneButtonAppearance = buttonAppearance

        // Back button indicator
        appearance.setBackIndicatorImage(
            UIImage(systemName: "chevron.backward"),
            transitionMaskImage: UIImage(systemName: "chevron.backward")
        )

        guard let navBar = navigationController?.navigationBar else { return }
        navBar.standardAppearance = appearance
        navBar.scrollEdgeAppearance = appearance
        navBar.compactAppearance = appearance
        navBar.tintColor = .white   // back button and bar button tint
    }
}
```

### Transparent / Blurred Navigation Bar

```swift
private func configureTransparentNavBar() {
    let appearance = UINavigationBarAppearance()

    // Transparent background with default blur
    appearance.configureWithDefaultBackground()
    appearance.backgroundEffect = UIBlurEffect(style: .systemUltraThinMaterial)
    appearance.backgroundColor = UIColor.systemBackground.withAlphaComponent(0.7)

    appearance.titleTextAttributes = [.foregroundColor: UIColor.label]

    navigationController?.navigationBar.standardAppearance = appearance
    navigationController?.navigationBar.scrollEdgeAppearance = appearance
}
```

### Fully Transparent (No Background at All)

```swift
private func configureInvisibleNavBar() {
    let appearance = UINavigationBarAppearance()
    appearance.configureWithTransparentBackground()

    // No shadow line
    appearance.shadowColor = .clear

    appearance.titleTextAttributes = [.foregroundColor: UIColor.white]

    navigationController?.navigationBar.standardAppearance = appearance
    navigationController?.navigationBar.scrollEdgeAppearance = appearance
    navigationController?.navigationBar.tintColor = .white
}
```

### Complete App-Wide Styling Example

```swift
class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?

    func scene(_ scene: UIScene,
               willConnectTo session: UISceneSession,
               options connectionOptions: UIScene.ConnectionOptions) {

        guard let windowScene = scene as? UIWindowScene else { return }
        let window = UIWindow(windowScene: windowScene)

        // -- App-wide navigation bar styling --
        let navBarAppearance = UINavigationBarAppearance()
        navBarAppearance.configureWithOpaqueBackground()
        navBarAppearance.backgroundColor = UIColor(red: 0.1, green: 0.1, blue: 0.2, alpha: 1)
        navBarAppearance.titleTextAttributes = [
            .foregroundColor: UIColor.white,
            .font: UIFont.systemFont(ofSize: 17, weight: .semibold),
        ]
        navBarAppearance.largeTitleTextAttributes = [
            .foregroundColor: UIColor.white,
            .font: UIFont.systemFont(ofSize: 34, weight: .bold),
        ]
        navBarAppearance.shadowColor = .clear

        UINavigationBar.appearance().standardAppearance = navBarAppearance
        UINavigationBar.appearance().scrollEdgeAppearance = navBarAppearance
        UINavigationBar.appearance().compactAppearance = navBarAppearance
        UINavigationBar.appearance().tintColor = .systemYellow

        // -- Tab bar styling --
        let tabBarAppearance = UITabBarAppearance()
        tabBarAppearance.configureWithOpaqueBackground()
        tabBarAppearance.backgroundColor = UIColor(red: 0.1, green: 0.1, blue: 0.2, alpha: 1)

        UITabBar.appearance().standardAppearance = tabBarAppearance
        if #available(iOS 15.0, *) {
            UITabBar.appearance().scrollEdgeAppearance = tabBarAppearance
        }
        UITabBar.appearance().tintColor = .systemYellow

        // -- Build the VC hierarchy --
        let homeVC = HomeViewController()
        homeVC.title = "Home"
        let navController = UINavigationController(rootViewController: homeVC)
        navController.navigationBar.prefersLargeTitles = true

        window.rootViewController = navController
        window.makeKeyAndVisible()
        self.window = window
    }
}
```

### Resetting to Default Appearance

```swift
private func resetNavBarToDefault() {
    let defaultAppearance = UINavigationBarAppearance()
    defaultAppearance.configureWithDefaultBackground()

    navigationController?.navigationBar.standardAppearance = defaultAppearance
    navigationController?.navigationBar.scrollEdgeAppearance = nil  // nil = use standardAppearance
    navigationController?.navigationBar.compactAppearance = nil
    navigationController?.navigationBar.tintColor = nil             // revert to system default
}
```
