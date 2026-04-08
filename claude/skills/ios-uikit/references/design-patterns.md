# UIKit Design Patterns Reference

Common UIKit design patterns with complete Swift code examples.

---

## 1. Load and Retry Pattern

A parent view controller manages three states: **loading**, **success (done)**, and **retry** (error). Child content is swapped in and out while a spinner or retry button is displayed.

### State Management

```swift
enum ViewState {
    case loading
    case loaded
    case error
}
```

### Parent View Controller

```swift
class LoadableViewController: UIViewController {

    // MARK: - Child VCs
    private let loadingVC = LoadingViewController()
    private let retryVC = RetryViewController()

    // MARK: - State

    private var state: ViewState = .loading

    // MARK: - Public API

    /// Show the spinner and hide content.
    func setToLoading() {
        state = .loading
        removeChild(retryVC)
        addChild(loadingVC, to: view)
    }

    /// Hide spinner and show content.
    func doneLoading() {
        state = .loaded
        removeChild(loadingVC)
        removeChild(retryVC)
    }

    /// Show the retry button (after a network error, for example).
    func setToRetry() {
        state = .error
        removeChild(loadingVC)
        addChild(retryVC, to: view)
        retryVC.delegate = self
    }

    // MARK: - Helpers

    private func addChild(_ child: UIViewController, to containerView: UIView) {
        addChild(child)
        containerView.addSubview(child.view)
        child.view.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            child.view.topAnchor.constraint(equalTo: containerView.topAnchor),
            child.view.leadingAnchor.constraint(equalTo: containerView.leadingAnchor),
            child.view.trailingAnchor.constraint(equalTo: containerView.trailingAnchor),
            child.view.bottomAnchor.constraint(equalTo: containerView.bottomAnchor),
        ])
        child.didMove(toParent: self)
    }

    private func removeChild(_ child: UIViewController) {
        guard child.parent != nil else { return }
        child.willMove(toParent: nil)
        child.view.removeFromSuperview()
        child.removeFromParent()
    }
}
```

### Loading View Controller

```swift
class LoadingViewController: UIViewController {

    private let spinner = UIActivityIndicatorView(style: .large)

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground

        spinner.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(spinner)
        NSLayoutConstraint.activate([
            spinner.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            spinner.centerYAnchor.constraint(equalTo: view.centerYAnchor),
        ])
        spinner.startAnimating()
    }
}
```

### Retry View Controller

```swift
protocol RetryViewControllerDelegate: AnyObject {
    func didTapRetry()
}

class RetryViewController: UIViewController {

    weak var delegate: RetryViewControllerDelegate?

    private let messageLabel: UILabel = {
        let label = UILabel()
        label.text = "Something went wrong."
        label.textAlignment = .center
        label.font = .preferredFont(forTextStyle: .headline)
        return label
    }()

    private lazy var retryButton: UIButton = {
        let button = UIButton(type: .system)
        button.setTitle("Retry", for: .normal)
        button.titleLabel?.font = .preferredFont(forTextStyle: .body)
        button.addTarget(self, action: #selector(retryTapped), for: .primaryActionTriggered)
        return button
    }()

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground

        let stack = UIStackView(arrangedSubviews: [messageLabel, retryButton])
        stack.axis = .vertical
        stack.spacing = 16
        stack.alignment = .center
        stack.translatesAutoresizingMaskIntoConstraints = false

        view.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            stack.centerYAnchor.constraint(equalTo: view.centerYAnchor),
        ])
    }

    @objc private func retryTapped() {
        delegate?.didTapRetry()
    }
}
```

### Usage in a Feature VC

```swift
class AccountViewController: LoadableViewController {

    override func viewDidLoad() {
        super.viewDidLoad()
        fetchData()
    }

    private func fetchData() {
        setToLoading()
        NetworkManager.shared.fetchAccount { [weak self] result in
            DispatchQueue.main.async {
                switch result {
                case .success:
                    self?.doneLoading()
                case .failure:
                    self?.setToRetry()
                }
            }
        }
    }
}

extension AccountViewController: RetryViewControllerDelegate {
    func didTapRetry() {
        fetchData()
    }
}
```

---

## 2. Custom Badge

Three progressively more advanced approaches for adding notification badges to UIKit views.

### Approach A -- Simple UILabel Badge

The quickest way: a small rounded UILabel pinned to the top-trailing corner.

```swift
class BadgeLabel: UILabel {

    override init(frame: CGRect) {
        super.init(frame: frame)
        configure()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        configure()
    }

    private func configure() {
        translatesAutoresizingMaskIntoConstraints = false
        font = .systemFont(ofSize: 11, weight: .bold)
        textColor = .white
        textAlignment = .center
        backgroundColor = .systemRed
        layer.masksToBounds = true
    }

    override var intrinsicContentSize: CGSize {
        let size = super.intrinsicContentSize
        let side = max(size.width + 8, size.height + 4, 18)
        return CGSize(width: side, height: side)
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        layer.cornerRadius = bounds.height / 2
    }
}

// Usage:
extension UIView {
    func addSimpleBadge(count: Int) {
        let badge = BadgeLabel()
        badge.text = count > 99 ? "99+" : "\(count)"
        badge.tag = 999

        addSubview(badge)
        NSLayoutConstraint.activate([
            badge.topAnchor.constraint(equalTo: topAnchor, constant: -6),
            badge.trailingAnchor.constraint(equalTo: trailingAnchor, constant: 6),
        ])
    }

    func removeSimpleBadge() {
        viewWithTag(999)?.removeFromSuperview()
    }
}
```

### Approach B -- Protocol-Based Badgeable Extension

A protocol that any UIView subclass can conform to.

```swift
protocol Badgeable where Self: UIView {
    var badgeTag: Int { get }
    func showBadge(withCount count: Int)
    func hideBadge()
}

extension Badgeable {

    var badgeTag: Int { 9876 }

    func showBadge(withCount count: Int) {
        hideBadge()

        let badge = UILabel()
        badge.tag = badgeTag
        badge.translatesAutoresizingMaskIntoConstraints = false
        badge.text = count > 99 ? "99+" : "\(count)"
        badge.font = .monospacedDigitSystemFont(ofSize: 11, weight: .bold)
        badge.textColor = .white
        badge.textAlignment = .center
        badge.backgroundColor = .systemRed
        badge.layer.masksToBounds = true

        addSubview(badge)

        let height: CGFloat = 18
        NSLayoutConstraint.activate([
            badge.heightAnchor.constraint(greaterThanOrEqualToConstant: height),
            badge.widthAnchor.constraint(greaterThanOrEqualTo: badge.heightAnchor),
            badge.topAnchor.constraint(equalTo: topAnchor, constant: -height / 2),
            badge.trailingAnchor.constraint(equalTo: trailingAnchor, constant: height / 2),
        ])

        // Round after layout
        badge.layoutIfNeeded()
        badge.layer.cornerRadius = badge.bounds.height / 2
    }

    func hideBadge() {
        viewWithTag(badgeTag)?.removeFromSuperview()
    }
}

// Conformance for any view:
extension UIButton: Badgeable {}
extension UIImageView: Badgeable {}

// Usage:
let profileButton = UIButton(type: .system)
profileButton.showBadge(withCount: 5)
```

### Approach C -- Advanced BadgeHub with Animations

A standalone badge manager inspired by `BadgeHub`. Supports:

- Dynamic frame resizing using `log10` to keep the badge compact as digits grow.
- Pop, bump, and shake animations.

```swift
class BadgeHub {

    // MARK: - Views

    private let redCircle = UIView()
    private let countLabel = UILabel()

    // MARK: - State

    private(set) var count: Int = 0
    private weak var attachedView: UIView?

    // MARK: - Configuration

    var badgeSize: CGFloat = 18
    var badgeColor: UIColor = .systemRed {
        didSet { redCircle.backgroundColor = badgeColor }
    }

    // MARK: - Init

    init(view: UIView) {
        self.attachedView = view
        setupBadge(on: view)
    }

    // MARK: - Setup

    private func setupBadge(on view: UIView) {
        countLabel.text = "0"
        countLabel.textAlignment = .center
        countLabel.textColor = .white
        countLabel.font = .systemFont(ofSize: 11, weight: .bold)

        redCircle.backgroundColor = badgeColor
        redCircle.layer.masksToBounds = true
        redCircle.addSubview(countLabel)
        redCircle.isHidden = true

        view.addSubview(redCircle)
        updateFrameForCount()
    }

    // MARK: - Frame Calculation

    /// Width grows logarithmically so 1-digit, 2-digit, 3-digit counts
    /// do not balloon the badge.
    private func updateFrameForCount() {
        guard let view = attachedView else { return }

        let digitCount = count > 0 ? Int(log10(Double(count))) + 1 : 1
        let extraWidth: CGFloat = CGFloat(max(digitCount - 1, 0)) * 6
        let width = badgeSize + extraWidth
        let height = badgeSize

        let x = view.frame.width - width / 2
        let y: CGFloat = -height / 2

        redCircle.frame = CGRect(x: x, y: y, width: width, height: height)
        redCircle.layer.cornerRadius = height / 2

        countLabel.frame = redCircle.bounds
    }

    // MARK: - Public API

    func setCount(_ newCount: Int) {
        count = max(newCount, 0)
        countLabel.text = "\(count)"
        redCircle.isHidden = count == 0
        updateFrameForCount()
    }

    func increment() {
        setCount(count + 1)
        pop()
    }

    func decrement() {
        setCount(count - 1)
    }

    // MARK: - Animations

    /// Quick scale-up / scale-down "pop".
    func pop() {
        let anim = CAKeyframeAnimation(keyPath: "transform.scale")
        anim.values = [1.0, 1.4, 0.9, 1.1, 1.0]
        anim.keyTimes = [0, 0.2, 0.5, 0.8, 1.0]
        anim.duration = 0.4
        redCircle.layer.add(anim, forKey: "pop")
    }

    /// Gentle vertical bump.
    func bump() {
        let anim = CAKeyframeAnimation(keyPath: "transform.translation.y")
        anim.values = [0, -8, 2, -3, 0]
        anim.keyTimes = [0, 0.25, 0.5, 0.75, 1.0]
        anim.duration = 0.3
        redCircle.layer.add(anim, forKey: "bump")
    }

    /// Horizontal shake.
    func shake() {
        let anim = CAKeyframeAnimation(keyPath: "transform.translation.x")
        anim.values = [0, -6, 6, -4, 4, -2, 0]
        anim.keyTimes = [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
        anim.duration = 0.4
        redCircle.layer.add(anim, forKey: "shake")
    }
}
```

Usage:

```swift
class ProfileViewController: UIViewController {

    let bellButton = UIButton(type: .system)
    var badge: BadgeHub!

    override func viewDidLoad() {
        super.viewDidLoad()

        bellButton.setImage(UIImage(systemName: "bell"), for: .normal)
        bellButton.frame = CGRect(x: 100, y: 100, width: 44, height: 44)
        view.addSubview(bellButton)

        badge = BadgeHub(view: bellButton)
        badge.setCount(3)     // shows "3"
        badge.increment()     // shows "4" with pop animation
        badge.shake()         // horizontal shake
    }
}
```

---

## 3. Bottom Menu Popup (Drawer)

A full-screen overlay view controller presented with `.overCurrentContext` so the presenting VC stays visible behind a translucent black scrim. A UIStackView pins content to the bottom half.

### Delegate Protocol

```swift
protocol BottomMenuDelegate: AnyObject {
    func didSelectMenuItem(_ item: String)
    func didDismissMenu()
}
```

### Bottom Menu View Controller

```swift
class BottomMenuViewController: UIViewController {

    // MARK: - Properties

    weak var delegate: BottomMenuDelegate?
    private let menuItems: [String]

    // MARK: - Views

    private let overlayView: UIView = {
        let v = UIView()
        v.backgroundColor = UIColor.black.withAlphaComponent(0.3)
        return v
    }()

    private let containerStack: UIStackView = {
        let sv = UIStackView()
        sv.axis = .vertical
        sv.spacing = 0
        sv.translatesAutoresizingMaskIntoConstraints = false
        return sv
    }()

    // MARK: - Init

    init(items: [String]) {
        self.menuItems = items
        super.init(nibName: nil, bundle: nil)

        // Critical: this lets the presenting VC show through.
        modalPresentationStyle = .overCurrentContext
        modalTransitionStyle = .crossDissolve
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .clear
        setupOverlay()
        setupStack()
    }

    // MARK: - Setup

    private func setupOverlay() {
        overlayView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(overlayView)
        NSLayoutConstraint.activate([
            overlayView.topAnchor.constraint(equalTo: view.topAnchor),
            overlayView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            overlayView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            overlayView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
        ])

        let tap = UITapGestureRecognizer(target: self, action: #selector(overlayTapped))
        overlayView.addGestureRecognizer(tap)
    }

    private func setupStack() {
        view.addSubview(containerStack)
        NSLayoutConstraint.activate([
            containerStack.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            containerStack.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            containerStack.bottomAnchor.constraint(equalTo: view.bottomAnchor),
        ])

        // Top spacer takes ~50% of screen height, pushing content to the bottom half.
        let spacer = UIView()
        spacer.translatesAutoresizingMaskIntoConstraints = false
        containerStack.addArrangedSubview(spacer)
        spacer.heightAnchor.constraint(equalTo: view.heightAnchor, multiplier: 0.5).isActive = true

        // Menu content area
        let contentView = UIView()
        contentView.backgroundColor = .systemBackground
        contentView.layer.cornerRadius = 16
        contentView.layer.maskedCorners = [.layerMinXMinYCorner, .layerMaxXMinYCorner]
        containerStack.addArrangedSubview(contentView)

        // Build menu items inside the content view.
        let itemStack = UIStackView()
        itemStack.axis = .vertical
        itemStack.spacing = 0
        itemStack.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(itemStack)

        NSLayoutConstraint.activate([
            itemStack.topAnchor.constraint(equalTo: contentView.topAnchor, constant: 20),
            itemStack.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            itemStack.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
            itemStack.bottomAnchor.constraint(equalTo: contentView.safeAreaLayoutGuide.bottomAnchor, constant: -8),
        ])

        // Handle / grabber
        let grabber = UIView()
        grabber.backgroundColor = .systemGray3
        grabber.layer.cornerRadius = 2.5
        grabber.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(grabber)
        NSLayoutConstraint.activate([
            grabber.topAnchor.constraint(equalTo: contentView.topAnchor, constant: 8),
            grabber.centerXAnchor.constraint(equalTo: contentView.centerXAnchor),
            grabber.widthAnchor.constraint(equalToConstant: 36),
            grabber.heightAnchor.constraint(equalToConstant: 5),
        ])

        for (index, title) in menuItems.enumerated() {
            let button = UIButton(type: .system)
            button.setTitle(title, for: .normal)
            button.titleLabel?.font = .preferredFont(forTextStyle: .body)
            button.contentHorizontalAlignment = .leading
            button.contentEdgeInsets = UIEdgeInsets(top: 14, left: 20, bottom: 14, right: 20)
            button.tag = index
            button.addTarget(self, action: #selector(menuItemTapped(_:)), for: .primaryActionTriggered)
            itemStack.addArrangedSubview(button)

            if index < menuItems.count - 1 {
                let separator = UIView()
                separator.backgroundColor = .separator
                separator.translatesAutoresizingMaskIntoConstraints = false
                separator.heightAnchor.constraint(equalToConstant: 1 / UIScreen.main.scale).isActive = true
                itemStack.addArrangedSubview(separator)
            }
        }
    }

    // MARK: - Actions

    @objc private func overlayTapped() {
        dismiss(animated: true) { [weak self] in
            self?.delegate?.didDismissMenu()
        }
    }

    @objc private func menuItemTapped(_ sender: UIButton) {
        let item = menuItems[sender.tag]
        dismiss(animated: true) { [weak self] in
            self?.delegate?.didSelectMenuItem(item)
        }
    }
}
```

### Presenting the Menu

```swift
class SettingsViewController: UIViewController, BottomMenuDelegate {

    @objc func showMenu() {
        let menu = BottomMenuViewController(items: [
            "Edit Profile",
            "Share",
            "Report",
            "Cancel",
        ])
        menu.delegate = self
        present(menu, animated: true)
    }

    // MARK: - BottomMenuDelegate

    func didSelectMenuItem(_ item: String) {
        print("Selected: \(item)")
    }

    func didDismissMenu() {
        print("Menu dismissed")
    }
}
```

---

## 4. Interactive Popup Menu

A drawer/panel whose open and close states are driven by `UIViewPropertyAnimator` and synced to a `UIPanGestureRecognizer`. The user can flick the panel open or closed; momentum (velocity) determines the final resting state.

### State Machine

```swift
enum PopupState {
    case open
    case closed

    var opposite: PopupState {
        switch self {
        case .open: return .closed
        case .closed: return .open
        }
    }
}
```

### InstantPanGestureRecognizer

A pan recognizer that begins immediately (no delay), so the animator tracks the finger from the first touch.

```swift
class InstantPanGestureRecognizer: UIPanGestureRecognizer {

    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent) {
        if state == .began { return }
        super.touchesBegan(touches, with: event)
        state = .began
    }
}
```

### Interactive Popup View Controller

```swift
class InteractivePopupViewController: UIViewController {

    // MARK: - Config

    private let popupHeight: CGFloat = 300
    private let cornerRadius: CGFloat = 16

    // MARK: - State

    private var currentState: PopupState = .closed
    private var runningAnimators: [UIViewPropertyAnimator] = []
    private var animationProgress: [CGFloat] = []

    // MARK: - Views

    private let popupView: UIView = {
        let v = UIView()
        v.backgroundColor = .secondarySystemBackground
        v.layer.cornerRadius = 16
        v.layer.maskedCorners = [.layerMinXMinYCorner, .layerMaxXMinYCorner]
        v.layer.shadowColor = UIColor.black.cgColor
        v.layer.shadowOpacity = 0.15
        v.layer.shadowRadius = 10
        return v
    }()

    private let overlayView: UIView = {
        let v = UIView()
        v.backgroundColor = .black
        v.alpha = 0
        return v
    }()

    // MARK: - Constraints

    private var popupBottomConstraint: NSLayoutConstraint!

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        setupViews()
        setupGesture()
    }

    // MARK: - Setup

    private func setupViews() {
        overlayView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(overlayView)
        NSLayoutConstraint.activate([
            overlayView.topAnchor.constraint(equalTo: view.topAnchor),
            overlayView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            overlayView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            overlayView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
        ])

        popupView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(popupView)

        // When closed the popup sits below the screen; when open it rises up.
        popupBottomConstraint = popupView.bottomAnchor.constraint(
            equalTo: view.bottomAnchor, constant: popupHeight
        )

        NSLayoutConstraint.activate([
            popupView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            popupView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            popupView.heightAnchor.constraint(equalToConstant: popupHeight),
            popupBottomConstraint,
        ])
    }

    private func setupGesture() {
        let pan = InstantPanGestureRecognizer(target: self, action: #selector(handlePan(_:)))
        popupView.addGestureRecognizer(pan)
    }

    // MARK: - Animation

    private func animateTransitionIfNeeded(to state: PopupState, duration: TimeInterval = 0.5) {
        guard runningAnimators.isEmpty else { return }

        // Layout animator
        let frameAnimator = UIViewPropertyAnimator(duration: duration, dampingRatio: 0.9) {
            switch state {
            case .open:
                self.popupBottomConstraint.constant = 0
            case .closed:
                self.popupBottomConstraint.constant = self.popupHeight
            }
            self.view.layoutIfNeeded()
        }

        frameAnimator.addCompletion { position in
            switch position {
            case .end:
                self.currentState = state
            default:
                self.currentState = state.opposite
            }
            self.runningAnimators.removeAll()
        }

        // Overlay animator
        let overlayAnimator = UIViewPropertyAnimator(duration: duration, dampingRatio: 0.9) {
            self.overlayView.alpha = state == .open ? 0.3 : 0
        }

        frameAnimator.startAnimation()
        overlayAnimator.startAnimation()

        runningAnimators = [frameAnimator, overlayAnimator]
    }

    // MARK: - Gesture

    @objc private func handlePan(_ recognizer: UIPanGestureRecognizer) {
        let translation = recognizer.translation(in: popupView)
        // Fraction: dragging up (negative y) when closed -> fraction increases.
        var fraction = -translation.y / popupHeight

        switch recognizer.state {
        case .began:
            // Start the transition toward the opposite state.
            animateTransitionIfNeeded(to: currentState.opposite)
            // Pause all animators so we can scrub manually.
            runningAnimators.forEach { $0.pauseAnimation() }
            animationProgress = runningAnimators.map { $0.fractionComplete }

        case .changed:
            // Reverse fraction when closing.
            if currentState == .open { fraction *= -1 }
            for (index, animator) in runningAnimators.enumerated() {
                animator.fractionComplete = animationProgress[index] + fraction
            }

        case .ended:
            let velocity = recognizer.velocity(in: popupView)
            let shouldClose = velocity.y > 300

            for animator in runningAnimators {
                if shouldClose && currentState == .closed {
                    // User flicked down while opening -> reverse to closed.
                    animator.isReversed = true
                } else if !shouldClose && currentState == .open {
                    // User flicked up while closing -> reverse to open.
                    animator.isReversed = true
                }
                animator.continueAnimation(
                    withTimingParameters: UISpringTimingParameters(dampingRatio: 0.9),
                    durationFactor: 0
                )
            }

        default:
            break
        }
    }
}
```

### How It Works

1. **`.began`** -- Create animators toward the opposite state and immediately pause them.
2. **`.changed`** -- Sync each animator's `fractionComplete` to the pan translation.
3. **`.ended`** -- Check the flick velocity. If the user flicked against the current direction, reverse the animators; otherwise let them finish. `continueAnimation` adds spring momentum automatically.

---

## 5. Simple Onboarding

A `UIPageViewController` with dot indicators, Skip and Next buttons, and constraint-based animation that hides the Skip button on the last page.

### Onboarding Page Model

```swift
struct OnboardingPage {
    let imageName: String
    let title: String
    let description: String
}
```

### Single Page View Controller

```swift
class OnboardingPageContentViewController: UIViewController {

    private let page: OnboardingPage
    let pageIndex: Int

    private let imageView: UIImageView = {
        let iv = UIImageView()
        iv.contentMode = .scaleAspectFit
        iv.tintColor = .label
        iv.translatesAutoresizingMaskIntoConstraints = false
        return iv
    }()

    private let titleLabel: UILabel = {
        let l = UILabel()
        l.font = .preferredFont(forTextStyle: .title1)
        l.textAlignment = .center
        return l
    }()

    private let descriptionLabel: UILabel = {
        let l = UILabel()
        l.font = .preferredFont(forTextStyle: .body)
        l.textAlignment = .center
        l.numberOfLines = 0
        return l
    }()

    init(page: OnboardingPage, index: Int) {
        self.page = page
        self.pageIndex = index
        super.init(nibName: nil, bundle: nil)
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground

        imageView.image = UIImage(systemName: page.imageName)

        titleLabel.text = page.title
        descriptionLabel.text = page.description

        let stack = UIStackView(arrangedSubviews: [imageView, titleLabel, descriptionLabel])
        stack.axis = .vertical
        stack.spacing = 20
        stack.alignment = .center
        stack.translatesAutoresizingMaskIntoConstraints = false

        view.addSubview(stack)
        NSLayoutConstraint.activate([
            imageView.heightAnchor.constraint(equalToConstant: 150),
            imageView.widthAnchor.constraint(equalToConstant: 150),
            stack.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            stack.centerYAnchor.constraint(equalTo: view.centerYAnchor, constant: -40),
            stack.leadingAnchor.constraint(greaterThanOrEqualTo: view.leadingAnchor, constant: 32),
            stack.trailingAnchor.constraint(lessThanOrEqualTo: view.trailingAnchor, constant: -32),
        ])
    }
}
```

### Onboarding Container View Controller

```swift
class OnboardingViewController: UIViewController {

    // MARK: - Data

    private let pages: [OnboardingPage] = [
        OnboardingPage(imageName: "star.fill", title: "Welcome", description: "Discover amazing features."),
        OnboardingPage(imageName: "bolt.fill", title: "Fast", description: "Lightning-fast performance."),
        OnboardingPage(imageName: "heart.fill", title: "Love It", description: "You will love using this app."),
    ]

    // MARK: - Child VCs

    private lazy var pageViewController: UIPageViewController = {
        let pvc = UIPageViewController(
            transitionStyle: .scroll,
            navigationOrientation: .horizontal
        )
        pvc.dataSource = self
        pvc.delegate = self
        return pvc
    }()

    // MARK: - Controls

    private let pageControl: UIPageControl = {
        let pc = UIPageControl()
        pc.currentPageIndicatorTintColor = .label
        pc.pageIndicatorTintColor = .systemGray3
        pc.translatesAutoresizingMaskIntoConstraints = false
        return pc
    }()

    private lazy var skipButton: UIButton = {
        let b = UIButton(type: .system)
        b.setTitle("Skip", for: .normal)
        b.addTarget(self, action: #selector(skipTapped), for: .primaryActionTriggered)
        b.translatesAutoresizingMaskIntoConstraints = false
        return b
    }()

    private lazy var nextButton: UIButton = {
        let b = UIButton(type: .system)
        b.setTitle("Next", for: .normal)
        b.titleLabel?.font = .preferredFont(forTextStyle: .headline)
        b.addTarget(self, action: #selector(nextTapped), for: .primaryActionTriggered)
        b.translatesAutoresizingMaskIntoConstraints = false
        return b
    }()

    // MARK: - Constraints for Animation

    private var skipButtonLeadingConstraint: NSLayoutConstraint!

    // MARK: - State

    private var currentIndex: Int = 0

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground

        addChild(pageViewController)
        view.addSubview(pageViewController.view)
        pageViewController.view.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            pageViewController.view.topAnchor.constraint(equalTo: view.topAnchor),
            pageViewController.view.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            pageViewController.view.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            pageViewController.view.bottomAnchor.constraint(equalTo: view.bottomAnchor),
        ])
        pageViewController.didMove(toParent: self)

        let firstPage = makePageContentVC(for: 0)
        pageViewController.setViewControllers([firstPage], direction: .forward, animated: false)

        pageControl.numberOfPages = pages.count
        view.addSubview(pageControl)
        view.addSubview(skipButton)
        view.addSubview(nextButton)

        skipButtonLeadingConstraint = skipButton.leadingAnchor.constraint(
            equalTo: view.leadingAnchor, constant: 20
        )

        NSLayoutConstraint.activate([
            pageControl.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor, constant: -40),
            pageControl.centerXAnchor.constraint(equalTo: view.centerXAnchor),

            skipButtonLeadingConstraint,
            skipButton.bottomAnchor.constraint(equalTo: pageControl.topAnchor, constant: -20),

            nextButton.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -20),
            nextButton.bottomAnchor.constraint(equalTo: pageControl.topAnchor, constant: -20),
        ])
    }

    // MARK: - Helpers

    private func makePageContentVC(for index: Int) -> OnboardingPageContentViewController {
        OnboardingPageContentViewController(page: pages[index], index: index)
    }

    /// Animate the Skip button off-screen on the last page, back on for others.
    private func updateControlsForPage(at index: Int) {
        currentIndex = index
        pageControl.currentPage = index

        let isLastPage = index == pages.count - 1
        nextButton.setTitle(isLastPage ? "Get Started" : "Next", for: .normal)

        // Animate skip button visibility via constraint.
        skipButtonLeadingConstraint.constant = isLastPage ? -100 : 20
        UIView.animate(withDuration: 0.3) {
            self.skipButton.alpha = isLastPage ? 0 : 1
            self.view.layoutIfNeeded()
        }
    }

    // MARK: - Actions

    @objc private func skipTapped() {
        finishOnboarding()
    }

    @objc private func nextTapped() {
        let nextIndex = currentIndex + 1
        if nextIndex < pages.count {
            let nextVC = makePageContentVC(for: nextIndex)
            pageViewController.setViewControllers([nextVC], direction: .forward, animated: true)
            updateControlsForPage(at: nextIndex)
        } else {
            finishOnboarding()
        }
    }

    private func finishOnboarding() {
        // Dismiss or transition to the main app.
        dismiss(animated: true)
    }
}

// MARK: - UIPageViewControllerDataSource

extension OnboardingViewController: UIPageViewControllerDataSource {

    func pageViewController(
        _ pageViewController: UIPageViewController,
        viewControllerBefore viewController: UIViewController
    ) -> UIViewController? {
        guard let vc = viewController as? OnboardingPageContentViewController else { return nil }
        let prevIndex = vc.pageIndex - 1
        guard prevIndex >= 0 else {
            // Wrap around to the last page.
            return makePageContentVC(for: pages.count - 1)
        }
        return makePageContentVC(for: prevIndex)
    }

    func pageViewController(
        _ pageViewController: UIPageViewController,
        viewControllerAfter viewController: UIViewController
    ) -> UIViewController? {
        guard let vc = viewController as? OnboardingPageContentViewController else { return nil }
        let nextIndex = vc.pageIndex + 1
        guard nextIndex < pages.count else {
            // Wrap around to the first page.
            return makePageContentVC(for: 0)
        }
        return makePageContentVC(for: nextIndex)
    }
}

// MARK: - UIPageViewControllerDelegate

extension OnboardingViewController: UIPageViewControllerDelegate {

    func pageViewController(
        _ pageViewController: UIPageViewController,
        didFinishAnimating finished: Bool,
        previousViewControllers: [UIViewController],
        transitionCompleted completed: Bool
    ) {
        guard completed,
              let currentVC = pageViewController.viewControllers?.first as? OnboardingPageContentViewController
        else { return }
        updateControlsForPage(at: currentVC.pageIndex)
    }
}
```

---

## 6. Collapsible Header

A header view that collapses as the user scrolls a table or collection view. Uses a height constraint and `UIViewPropertyAnimator` with a snap threshold.

### Collapsible Header View Controller

```swift
class CollapsibleHeaderViewController: UIViewController {

    // MARK: - Config

    private let maxHeaderHeight: CGFloat = 200
    private let minHeaderHeight: CGFloat = 64
    private let snapThreshold: CGFloat = 0.5 // fraction at which we snap open or closed

    // MARK: - Views

    private let headerView: UIView = {
        let v = UIView()
        v.backgroundColor = .systemBlue
        v.translatesAutoresizingMaskIntoConstraints = false
        return v
    }()

    private let headerTitleLabel: UILabel = {
        let l = UILabel()
        l.text = "Header"
        l.font = .preferredFont(forTextStyle: .largeTitle)
        l.textColor = .white
        l.translatesAutoresizingMaskIntoConstraints = false
        return l
    }()

    private let tableView: UITableView = {
        let tv = UITableView()
        tv.translatesAutoresizingMaskIntoConstraints = false
        return tv
    }()

    // MARK: - Constraints

    private var headerHeightConstraint: NSLayoutConstraint!

    // MARK: - Animator

    private var headerAnimator: UIViewPropertyAnimator?

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        setupHeader()
        setupTableView()
    }

    // MARK: - Setup

    private func setupHeader() {
        view.addSubview(headerView)
        headerView.addSubview(headerTitleLabel)

        headerHeightConstraint = headerView.heightAnchor.constraint(equalToConstant: maxHeaderHeight)

        NSLayoutConstraint.activate([
            headerView.topAnchor.constraint(equalTo: view.topAnchor),
            headerView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            headerView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            headerHeightConstraint,

            headerTitleLabel.leadingAnchor.constraint(equalTo: headerView.leadingAnchor, constant: 16),
            headerTitleLabel.bottomAnchor.constraint(equalTo: headerView.bottomAnchor, constant: -12),
        ])
    }

    private func setupTableView() {
        tableView.dataSource = self
        tableView.delegate = self
        tableView.register(UITableViewCell.self, forCellReuseIdentifier: "cell")

        view.addSubview(tableView)
        NSLayoutConstraint.activate([
            tableView.topAnchor.constraint(equalTo: headerView.bottomAnchor),
            tableView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            tableView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            tableView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
        ])
    }

    // MARK: - Collapse Logic

    /// Maps scroll offset to a collapse fraction (0 = fully open, 1 = fully collapsed).
    private func collapseFraction(for offset: CGFloat) -> CGFloat {
        let range = maxHeaderHeight - minHeaderHeight
        return min(max(offset / range, 0), 1)
    }

    /// Snaps header to fully open or fully collapsed based on threshold.
    private func snapHeader(fraction: CGFloat) {
        let targetHeight: CGFloat = fraction > snapThreshold ? minHeaderHeight : maxHeaderHeight

        headerAnimator?.stopAnimation(true)
        headerAnimator = UIViewPropertyAnimator(duration: 0.3, dampingRatio: 0.9) {
            self.headerHeightConstraint.constant = targetHeight
            self.headerTitleLabel.alpha = targetHeight == self.maxHeaderHeight ? 1 : 0
            self.view.layoutIfNeeded()
        }
        headerAnimator?.startAnimation()
    }
}

// MARK: - UITableViewDataSource

extension CollapsibleHeaderViewController: UITableViewDataSource {

    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int { 40 }

    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: "cell", for: indexPath)
        cell.textLabel?.text = "Row \(indexPath.row)"
        return cell
    }
}

// MARK: - UITableViewDelegate / UIScrollViewDelegate

extension CollapsibleHeaderViewController: UITableViewDelegate {

    func scrollViewDidScroll(_ scrollView: UIScrollView) {
        let offset = scrollView.contentOffset.y
        let range = maxHeaderHeight - minHeaderHeight
        let fraction = collapseFraction(for: offset)

        let newHeight = maxHeaderHeight - (range * fraction)
        headerHeightConstraint.constant = newHeight

        // Fade the title as the header collapses.
        headerTitleLabel.alpha = 1 - fraction
    }

    func scrollViewDidEndDragging(_ scrollView: UIScrollView, willDecelerate decelerate: Bool) {
        if !decelerate {
            let fraction = collapseFraction(for: scrollView.contentOffset.y)
            snapHeader(fraction: fraction)
        }
    }

    func scrollViewDidEndDecelerating(_ scrollView: UIScrollView) {
        let fraction = collapseFraction(for: scrollView.contentOffset.y)
        snapHeader(fraction: fraction)
    }
}
```

---

## 7. Starbucks Tile Pattern

A `UIScrollView` + `UIStackView` combination where each "tile" is its own child view controller. This mirrors how apps like Starbucks compose their home screen from reusable sections.

### Tile Protocol

```swift
protocol TileViewController: UIViewController {
    /// Height the tile wants. Return UIView.noIntrinsicMetric for self-sizing.
    var desiredHeight: CGFloat { get }
}

extension TileViewController {
    var desiredHeight: CGFloat { UIView.noIntrinsicMetric }
}
```

### Example Tile: Rewards Tile

```swift
class RewardsTileViewController: UIViewController, TileViewController {

    var desiredHeight: CGFloat { 180 }

    private let starCountLabel: UILabel = {
        let l = UILabel()
        l.font = .systemFont(ofSize: 48, weight: .bold)
        l.text = "125"
        return l
    }()

    private let subtitleLabel: UILabel = {
        let l = UILabel()
        l.font = .preferredFont(forTextStyle: .subheadline)
        l.textColor = .secondaryLabel
        l.text = "Star balance"
        return l
    }()

    private let progressView: UIProgressView = {
        let pv = UIProgressView(progressViewStyle: .default)
        pv.progress = 0.5
        pv.trackTintColor = .systemGray5
        pv.progressTintColor = .systemGreen
        return pv
    }()

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground

        let stack = UIStackView(arrangedSubviews: [starCountLabel, subtitleLabel, progressView])
        stack.axis = .vertical
        stack.spacing = 8
        stack.translatesAutoresizingMaskIntoConstraints = false

        view.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.topAnchor.constraint(equalTo: view.topAnchor, constant: 20),
            stack.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 20),
            stack.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -20),
        ])
    }
}
```

### Example Tile: Promo Banner Tile

```swift
class PromoBannerTileViewController: UIViewController, TileViewController {

    var desiredHeight: CGFloat { 220 }

    private let bannerImageView: UIImageView = {
        let iv = UIImageView()
        iv.contentMode = .scaleAspectFill
        iv.clipsToBounds = true
        iv.backgroundColor = .systemOrange.withAlphaComponent(0.15)
        iv.layer.cornerRadius = 12
        iv.translatesAutoresizingMaskIntoConstraints = false
        return iv
    }()

    private let promoLabel: UILabel = {
        let l = UILabel()
        l.text = "Happy Hour -- 2-for-1 Drinks"
        l.font = .preferredFont(forTextStyle: .title2)
        l.translatesAutoresizingMaskIntoConstraints = false
        return l
    }()

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground

        view.addSubview(bannerImageView)
        bannerImageView.addSubview(promoLabel)

        NSLayoutConstraint.activate([
            bannerImageView.topAnchor.constraint(equalTo: view.topAnchor, constant: 12),
            bannerImageView.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 16),
            bannerImageView.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -16),
            bannerImageView.bottomAnchor.constraint(equalTo: view.bottomAnchor, constant: -12),

            promoLabel.leadingAnchor.constraint(equalTo: bannerImageView.leadingAnchor, constant: 16),
            promoLabel.bottomAnchor.constraint(equalTo: bannerImageView.bottomAnchor, constant: -16),
        ])
    }
}
```

### Home (Container) View Controller

```swift
class HomeViewController: UIViewController {

    // MARK: - Views

    private let scrollView: UIScrollView = {
        let sv = UIScrollView()
        sv.translatesAutoresizingMaskIntoConstraints = false
        sv.showsVerticalScrollIndicator = true
        return sv
    }()

    private let stackView: UIStackView = {
        let sv = UIStackView()
        sv.axis = .vertical
        sv.spacing = 0
        sv.translatesAutoresizingMaskIntoConstraints = false
        return sv
    }()

    // MARK: - Tiles

    private var tiles: [UIViewController] = []

    // MARK: - Lifecycle

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Home"
        view.backgroundColor = .systemGroupedBackground
        setupScrollView()
        addTiles()
    }

    // MARK: - Setup

    private func setupScrollView() {
        view.addSubview(scrollView)
        scrollView.addSubview(stackView)

        NSLayoutConstraint.activate([
            scrollView.topAnchor.constraint(equalTo: view.topAnchor),
            scrollView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            scrollView.bottomAnchor.constraint(equalTo: view.bottomAnchor),

            stackView.topAnchor.constraint(equalTo: scrollView.topAnchor),
            stackView.leadingAnchor.constraint(equalTo: scrollView.leadingAnchor),
            stackView.trailingAnchor.constraint(equalTo: scrollView.trailingAnchor),
            stackView.bottomAnchor.constraint(equalTo: scrollView.bottomAnchor),

            // Stack width matches scroll view (vertical scrolling only).
            stackView.widthAnchor.constraint(equalTo: scrollView.widthAnchor),
        ])
    }

    // MARK: - Tile Management

    private func addTiles() {
        let rewardsTile = RewardsTileViewController()
        let promoTile = PromoBannerTileViewController()

        addTile(rewardsTile)
        addSeparator()
        addTile(promoTile)
    }

    private func addTile(_ childVC: UIViewController) {
        addChild(childVC)
        stackView.addArrangedSubview(childVC.view)
        childVC.didMove(toParent: self)
        tiles.append(childVC)

        // Apply explicit height if the tile declares one.
        if let tile = childVC as? TileViewController,
           tile.desiredHeight != UIView.noIntrinsicMetric {
            childVC.view.translatesAutoresizingMaskIntoConstraints = false
            childVC.view.heightAnchor.constraint(equalToConstant: tile.desiredHeight).isActive = true
        }
    }

    private func removeTile(_ childVC: UIViewController) {
        childVC.willMove(toParent: nil)
        stackView.removeArrangedSubview(childVC.view)
        childVC.view.removeFromSuperview()
        childVC.removeFromParent()
        tiles.removeAll { $0 === childVC }
    }

    private func addSeparator() {
        let separator = UIView()
        separator.backgroundColor = .separator
        separator.translatesAutoresizingMaskIntoConstraints = false
        separator.heightAnchor.constraint(equalToConstant: 1 / UIScreen.main.scale).isActive = true
        stackView.addArrangedSubview(separator)
    }
}
```

### Why This Pattern Works

- **Encapsulation** -- Each tile owns its layout, data fetching, and lifecycle.
- **Reuse** -- Tiles can be dropped into any container (home, profile, settings).
- **Composition** -- The parent only coordinates ordering and separators; it knows nothing about tile internals.
- **Memory** -- Tiles that scroll off-screen can be removed and re-added on demand, the same way `UITableView` recycles cells.
