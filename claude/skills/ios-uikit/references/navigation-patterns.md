# Navigation Patterns in UIKit

## 1. Modal Navigation

Modal navigation presents a view controller on top of the current context. The presenting VC is responsible for dismissing it (though the presented VC can call `dismiss` as a convenience).

### Present

```swift
class HomeViewController: UIViewController {

    @objc func showProfile() {
        let profileVC = ProfileViewController()

        // Optional: choose a presentation style
        profileVC.modalPresentationStyle = .fullScreen      // covers entire screen
        // profileVC.modalPresentationStyle = .pageSheet    // default on iPhone 13+
        // profileVC.modalPresentationStyle = .overCurrentContext

        // Optional: choose a transition style
        profileVC.modalTransitionStyle = .coverVertical     // default
        // profileVC.modalTransitionStyle = .crossDissolve
        // profileVC.modalTransitionStyle = .flipHorizontal

        present(profileVC, animated: true)
    }
}
```

### Dismiss

```swift
class ProfileViewController: UIViewController {

    @objc func closeTapped() {
        // The presented VC asks itself to dismiss.
        // UIKit forwards this to the presenting VC behind the scenes.
        dismiss(animated: true)
    }
}
```

### Present with Completion

```swift
present(profileVC, animated: true) {
    print("Profile is now fully visible on screen.")
}
```

### Passing Data Back with a Delegate

```swift
protocol ProfileDelegate: AnyObject {
    func profileDidUpdate(name: String)
}

class ProfileViewController: UIViewController {
    weak var delegate: ProfileDelegate?

    @objc func saveTapped() {
        delegate?.profileDidUpdate(name: "Alice")
        dismiss(animated: true)
    }
}

// In the presenting VC
class HomeViewController: UIViewController, ProfileDelegate {

    @objc func showProfile() {
        let profileVC = ProfileViewController()
        profileVC.delegate = self
        profileVC.modalPresentationStyle = .fullScreen
        present(profileVC, animated: true)
    }

    func profileDidUpdate(name: String) {
        print("User changed name to \(name)")
    }
}
```

---

## 2. Container Navigation

### UINavigationController - Push / Pop

A `UINavigationController` manages a stack of view controllers and provides a built-in navigation bar.

#### Setup in SceneDelegate

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

        window.rootViewController = navController
        window.makeKeyAndVisible()
        self.window = window
    }
}
```

#### Push

```swift
class HomeViewController: UIViewController {

    @objc func showDetail() {
        let detailVC = DetailViewController()
        detailVC.title = "Detail"

        // Push onto the navigation stack
        navigationController?.pushViewController(detailVC, animated: true)
    }
}
```

#### Pop

```swift
class DetailViewController: UIViewController {

    @objc func goBack() {
        // Pop the top VC off the stack
        navigationController?.popViewController(animated: true)
    }

    @objc func goToRoot() {
        // Pop everything and go back to the root VC
        navigationController?.popToRootViewController(animated: true)
    }
}
```

### UITabBarController

A `UITabBarController` manages a set of view controllers accessible through tabs at the bottom of the screen.

```swift
class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?

    func scene(_ scene: UIScene,
               willConnectTo session: UISceneSession,
               options connectionOptions: UIScene.ConnectionOptions) {

        guard let windowScene = scene as? UIWindowScene else { return }

        let window = UIWindow(windowScene: windowScene)

        let tabBarController = UITabBarController()

        // Each tab gets its own navigation controller
        let homeVC = UINavigationController(rootViewController: HomeViewController())
        homeVC.tabBarItem = UITabBarItem(title: "Home",
                                         image: UIImage(systemName: "house"),
                                         tag: 0)

        let searchVC = UINavigationController(rootViewController: SearchViewController())
        searchVC.tabBarItem = UITabBarItem(title: "Search",
                                           image: UIImage(systemName: "magnifyingglass"),
                                           tag: 1)

        let settingsVC = UINavigationController(rootViewController: SettingsViewController())
        settingsVC.tabBarItem = UITabBarItem(title: "Settings",
                                             image: UIImage(systemName: "gear"),
                                             tag: 2)

        tabBarController.viewControllers = [homeVC, searchVC, settingsVC]
        tabBarController.selectedIndex = 0

        window.rootViewController = tabBarController
        window.makeKeyAndVisible()
        self.window = window
    }
}
```

#### Customizing the Tab Bar Appearance

```swift
let appearance = UITabBarAppearance()
appearance.configureWithOpaqueBackground()
appearance.backgroundColor = .systemBackground

tabBarController.tabBar.standardAppearance = appearance
if #available(iOS 15.0, *) {
    tabBarController.tabBar.scrollEdgeAppearance = appearance
}
tabBarController.tabBar.tintColor = .systemBlue
```

---

## 3. Custom Container View Controller

When you need to embed one view controller inside another (e.g., swapping content areas), you must follow the **three-step add** and **three-step remove** lifecycle to keep UIKit's parent-child bookkeeping correct.

### Adding a Child (3 Steps)

```swift
class DashboardViewController: UIViewController {

    let containerView = UIView()

    func displayContent(_ childVC: UIViewController) {
        // Step 1 - Tell UIKit about the parent-child relationship
        addChild(childVC)

        // Step 2 - Add the child's view to your view hierarchy
        containerView.addSubview(childVC.view)

        // Pin the child's view to fill the container
        childVC.view.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            childVC.view.topAnchor.constraint(equalTo: containerView.topAnchor),
            childVC.view.leadingAnchor.constraint(equalTo: containerView.leadingAnchor),
            childVC.view.trailingAnchor.constraint(equalTo: containerView.trailingAnchor),
            childVC.view.bottomAnchor.constraint(equalTo: containerView.bottomAnchor),
        ])

        // Step 3 - Notify the child that the move is complete
        childVC.didMove(toParent: self)
    }
}
```

### Removing a Child (3 Steps)

```swift
extension DashboardViewController {

    func removeContent(_ childVC: UIViewController) {
        // Step 1 - Notify the child it is about to be removed
        childVC.willMove(toParent: nil)

        // Step 2 - Remove the child's view from the hierarchy
        childVC.view.removeFromSuperview()

        // Step 3 - Sever the parent-child relationship
        childVC.removeFromParent()
    }
}
```

### Swapping Children with Animation

```swift
extension DashboardViewController {

    func transition(from oldVC: UIViewController, to newVC: UIViewController) {
        oldVC.willMove(toParent: nil)
        addChild(newVC)

        newVC.view.frame = containerView.bounds
        newVC.view.alpha = 0

        transition(
            from: oldVC,
            to: newVC,
            duration: 0.3,
            options: .transitionCrossDissolve,
            animations: {
                newVC.view.alpha = 1
            },
            completion: { _ in
                oldVC.removeFromParent()
                newVC.didMove(toParent: self)
            }
        )
    }
}
```

---

## 4. MainViewController Pattern

A centralized navigation architecture where a single **MainViewController** acts as the app's root container. Child view controllers communicate navigation intent up the Responder Chain using a custom protocol.

### The Responder Protocol

```swift
protocol StarbucksResponder: AnyObject {
    func didTapHome()
    func didTapScan()
    func didTapOrder()
    func didTapGift()
    func didTapProfile()
}
```

### MainViewController

```swift
class MainViewController: UITabBarController, StarbucksResponder {

    override func viewDidLoad() {
        super.viewDidLoad()
        setupTabs()
    }

    private func setupTabs() {
        let homeVC = HomeViewController()
        homeVC.tabBarItem = UITabBarItem(title: "Home",
                                         image: UIImage(systemName: "house"),
                                         tag: 0)

        let scanVC = ScanViewController()
        scanVC.tabBarItem = UITabBarItem(title: "Scan",
                                         image: UIImage(systemName: "qrcode"),
                                         tag: 1)

        let orderVC = OrderViewController()
        orderVC.tabBarItem = UITabBarItem(title: "Order",
                                          image: UIImage(systemName: "cart"),
                                          tag: 2)

        viewControllers = [homeVC, scanVC, orderVC].map {
            UINavigationController(rootViewController: $0)
        }
    }

    // MARK: - StarbucksResponder

    func didTapHome() {
        selectedIndex = 0
    }

    func didTapScan() {
        selectedIndex = 1
    }

    func didTapOrder() {
        selectedIndex = 2
    }

    func didTapGift() {
        let giftVC = GiftViewController()
        giftVC.modalPresentationStyle = .fullScreen
        present(giftVC, animated: true)
    }

    func didTapProfile() {
        let profileVC = ProfileViewController()
        if let navVC = selectedViewController as? UINavigationController {
            navVC.pushViewController(profileVC, animated: true)
        }
    }
}
```

### Firing Events Up the Responder Chain

Any child VC (or deeply nested child) can find the responder without holding a direct reference:

```swift
// UIResponder extension to walk the chain
extension UIResponder {

    /// Walk the responder chain until we find an object conforming to the protocol.
    func findResponder<T>(ofType type: T.Type) -> T? {
        var current: UIResponder? = self
        while let responder = current {
            if let match = responder as? T {
                return match
            }
            current = responder.next
        }
        return nil
    }
}
```

```swift
class HomeViewController: UIViewController {

    @objc func orderButtonTapped() {
        // Walk up the responder chain to find the MainViewController
        if let responder = findResponder(ofType: StarbucksResponder.self) {
            responder.didTapOrder()
        }
    }

    @objc func giftButtonTapped() {
        findResponder(ofType: StarbucksResponder.self)?.didTapGift()
    }
}
```

This pattern keeps child VCs completely decoupled from the navigation structure. They never need to know about `UITabBarController`, `UINavigationController`, or the specific container they live in.

---

## 5. Child View Controller Management

### Full Example: Adding a Child VC (3 Steps)

```swift
class ContainerViewController: UIViewController {

    private let headerVC = HeaderViewController()
    private let contentVC = ContentViewController()

    override func viewDidLoad() {
        super.viewDidLoad()
        add(headerVC, to: view)
        add(contentVC, to: view)
        layoutChildren()
    }

    /// Reusable helper that performs the 3-step add.
    private func add(_ child: UIViewController, to containerView: UIView) {
        // 1. Register the child
        addChild(child)

        // 2. Insert the view
        containerView.addSubview(child.view)
        child.view.translatesAutoresizingMaskIntoConstraints = false

        // 3. Notify completion
        child.didMove(toParent: self)
    }

    private func layoutChildren() {
        NSLayoutConstraint.activate([
            headerVC.view.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            headerVC.view.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            headerVC.view.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            headerVC.view.heightAnchor.constraint(equalToConstant: 120),

            contentVC.view.topAnchor.constraint(equalTo: headerVC.view.bottomAnchor),
            contentVC.view.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            contentVC.view.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            contentVC.view.bottomAnchor.constraint(equalTo: view.bottomAnchor),
        ])
    }
}
```

### Full Example: Removing a Child VC

```swift
extension ContainerViewController {

    /// Reusable helper that performs the 3-step remove.
    private func remove(_ child: UIViewController) {
        // 1. Notify the child it will leave
        child.willMove(toParent: nil)

        // 2. Remove its view
        child.view.removeFromSuperview()

        // 3. Sever the relationship
        child.removeFromParent()
    }

    func replaceContent(with newVC: UIViewController) {
        remove(contentVC)
        add(newVC, to: view)

        // Re-layout for the new child
        NSLayoutConstraint.activate([
            newVC.view.topAnchor.constraint(equalTo: headerVC.view.bottomAnchor),
            newVC.view.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            newVC.view.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            newVC.view.bottomAnchor.constraint(equalTo: view.bottomAnchor),
        ])
    }
}
```

### Lifecycle Methods Received by the Child

When you follow the 3-step pattern correctly, UIKit automatically forwards these to the child:

| Parent Action             | Child Receives                                   |
|---------------------------|--------------------------------------------------|
| `addChild(_:)`            | `willMove(toParent: parentVC)` (called by UIKit) |
| `didMove(toParent:)`      | `viewWillAppear`, `viewDidAppear`                |
| `willMove(toParent: nil)` | `viewWillDisappear`                              |
| `removeFromParent()`      | `viewDidDisappear`, `didMove(toParent: nil)`     |
