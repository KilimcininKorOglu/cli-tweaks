# Deep Linking

## URL Scheme Setup in Info.plist

Add a custom URL scheme so your app responds to URLs like `myapp://path`.

In `Info.plist`, add under the top-level dict:

```xml
<key>CFBundleURLTypes</key>
<array>
    <dict>
        <key>CFBundleURLSchemes</key>
        <array>
            <string>myapp</string>
        </array>
        <key>CFBundleURLName</key>
        <string>com.example.myapp</string>
    </dict>
</array>
```

## DeepLink Enum with rawValue String

```swift
import Foundation

enum DeepLink: String {
    case home
    case profile
    case settings
    case transaction
    case offers

    init?(path: String) {
        // Strip leading slash: "/profile" -> "profile"
        let cleaned = path.hasPrefix("/") ? String(path.dropFirst()) : path
        self.init(rawValue: cleaned)
    }
}
```

## AppDelegate Open URL Handler with NSURLComponents

```swift
import UIKit

@UIApplicationMain
class AppDelegate: UIResponder, UIApplicationDelegate {

    var window: UIWindow?

    func application(
        _ app: UIApplication,
        open url: URL,
        options: [UIApplication.OpenURLOptionsKey: Any] = [:]
    ) -> Bool {
        return handleDeepLink(url)
    }

    private func handleDeepLink(_ url: URL) -> Bool {
        // Parse: myapp://transaction?id=42&source=push
        guard let components = NSURLComponents(url: url, resolvingAgainstBaseURL: false),
              let host = components.host else {
            return false
        }

        guard let deepLink = DeepLink(path: host) else {
            print("Unknown deep link: \(host)")
            return false
        }

        // Extract query parameters into a dictionary
        var params: [String: String] = [:]
        components.queryItems?.forEach { item in
            params[item.name] = item.value
        }

        route(to: deepLink, params: params)
        return true
    }

    private func route(to deepLink: DeepLink, params: [String: String]) {
        guard let rootVC = window?.rootViewController as? UINavigationController else { return }

        switch deepLink {
        case .home:
            rootVC.popToRootViewController(animated: true)

        case .profile:
            let profileVC = ProfileViewController()
            if let userId = params["userId"] {
                profileVC.userId = userId
            }
            rootVC.pushViewController(profileVC, animated: true)

        case .settings:
            let settingsVC = SettingsViewController()
            rootVC.pushViewController(settingsVC, animated: true)

        case .transaction:
            let transactionVC = TransactionDetailViewController()
            if let transactionId = params["id"] {
                transactionVC.transactionId = transactionId
            }
            rootVC.pushViewController(transactionVC, animated: true)

        case .offers:
            let offersVC = OffersViewController()
            if let category = params["category"] {
                offersVC.filterCategory = category
            }
            rootVC.pushViewController(offersVC, animated: true)
        }
    }
}
```

### Placeholder View Controllers

```swift
class ProfileViewController: UIViewController {
    var userId: String?
}

class SettingsViewController: UIViewController {}

class TransactionDetailViewController: UIViewController {
    var transactionId: String?
}

class OffersViewController: UIViewController {
    var filterCategory: String?
}
```

## SceneDelegate Handling (iOS 13+)

For apps using scenes, handle deep links in `SceneDelegate` instead.

```swift
import UIKit

class SceneDelegate: UIResponder, UIWindowSceneDelegate {

    var window: UIWindow?

    func scene(
        _ scene: UIScene,
        openURLContexts URLContexts: Set<UIOpenURLContext>
    ) {
        guard let url = URLContexts.first?.url else { return }
        handleDeepLink(url)
    }

    func scene(
        _ scene: UIScene,
        willConnectTo session: UISceneSession,
        options connectionOptions: UIScene.ConnectionOptions
    ) {
        // Handle deep link that launched the app
        if let url = connectionOptions.urlContexts.first?.url {
            handleDeepLink(url)
        }
    }

    private func handleDeepLink(_ url: URL) {
        guard let components = NSURLComponents(url: url, resolvingAgainstBaseURL: false),
              let host = components.host,
              let deepLink = DeepLink(path: host) else { return }

        var params: [String: String] = [:]
        components.queryItems?.forEach { item in
            params[item.name] = item.value
        }

        // Route using the same logic as AppDelegate
        print("Deep link: \(deepLink) with params: \(params)")
    }
}
```

## Testing with xcrun simctl openurl

Test deep links from the terminal without building a special test harness.

```bash
# Basic deep link
xcrun simctl openurl booted "myapp://home"

# Deep link with query parameters
xcrun simctl openurl booted "myapp://transaction?id=42&source=push"

# Profile with user ID
xcrun simctl openurl booted "myapp://profile?userId=abc123"

# Offers filtered by category
xcrun simctl openurl booted "myapp://offers?category=electronics"
```

To target a specific simulator by name:

```bash
# List available simulators
xcrun simctl list devices

# Open URL on a specific device
xcrun simctl openurl "iPhone 15 Pro" "myapp://settings"
```
