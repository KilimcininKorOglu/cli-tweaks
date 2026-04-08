# UIScrollView

## Key Concepts: Frame, Bounds, and ContentSize

A scroll view works by manipulating its `bounds` origin relative to its `contentSize`.

- **frame** -- The scroll view's position and size in its superview's coordinate system.
- **bounds** -- The visible window into the scroll view's content. Scrolling changes `bounds.origin`.
- **contentSize** -- The total size of the scrollable content area.

```
+--- frame (what the superview sees) ---+
|                                       |
|   +--- bounds (visible window) ---+   |
|   |                               |   |
|   |   Visible content here        |   |
|   |                               |   |
|   +-------------------------------+   |
|                                       |
+---------------------------------------+

contentSize.height (total scrollable height)
|<-------- much taller than frame -------->|
```

When you scroll down, `bounds.origin.y` increases, shifting which slice of content is visible.

## Scrolling by Adjusting Bounds

```swift
// Scrolling is literally just changing bounds.origin
let scrollView = UIScrollView()
scrollView.bounds.origin.y = 100 // scrolled down 100pt
```

## Custom DIY ScrollView with UIPanGestureRecognizer

This demonstrates how UIScrollView works internally.

```swift
import UIKit

class DIYScrollView: UIView {

    let contentView = UIView()

    override init(frame: CGRect) {
        super.init(frame: frame)
        setupContentView()
        setupPanGesture()
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    private func setupContentView() {
        addSubview(contentView)
        clipsToBounds = true
    }

    private func setupPanGesture() {
        let pan = UIPanGestureRecognizer(target: self, action: #selector(handlePan(_:)))
        addGestureRecognizer(pan)
    }

    @objc private func handlePan(_ gesture: UIPanGestureRecognizer) {
        let translation = gesture.translation(in: self)

        // Move the bounds origin in the opposite direction of the drag
        bounds.origin.y -= translation.y

        // Clamp to valid range
        let maxY = contentView.frame.height - frame.height
        bounds.origin.y = max(0, min(bounds.origin.y, maxY))

        gesture.setTranslation(.zero, in: self)
    }
}
```

## Real UIScrollView Setup

```swift
import UIKit

class ScrollViewController: UIViewController {

    let scrollView = UIScrollView()
    let contentView = UIView()

    override func viewDidLoad() {
        super.viewDidLoad()
        setupScrollView()
        setupContent()
    }

    private func setupScrollView() {
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(scrollView)

        NSLayoutConstraint.activate([
            scrollView.topAnchor.constraint(equalTo: view.topAnchor),
            scrollView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            scrollView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
        ])
    }

    private func setupContent() {
        contentView.translatesAutoresizingMaskIntoConstraints = false
        scrollView.addSubview(contentView)

        // Pin content view to scrollView's content layout guide
        NSLayoutConstraint.activate([
            contentView.topAnchor.constraint(equalTo: scrollView.contentLayoutGuide.topAnchor),
            contentView.leadingAnchor.constraint(equalTo: scrollView.contentLayoutGuide.leadingAnchor),
            contentView.trailingAnchor.constraint(equalTo: scrollView.contentLayoutGuide.trailingAnchor),
            contentView.bottomAnchor.constraint(equalTo: scrollView.contentLayoutGuide.bottomAnchor),

            // Width must match the frame layout guide for vertical-only scrolling
            contentView.widthAnchor.constraint(equalTo: scrollView.frameLayoutGuide.widthAnchor),
        ])

        // Add content that exceeds the scroll view's frame height
        let tallView = UIView()
        tallView.backgroundColor = .systemBlue
        tallView.translatesAutoresizingMaskIntoConstraints = false
        contentView.addSubview(tallView)

        NSLayoutConstraint.activate([
            tallView.topAnchor.constraint(equalTo: contentView.topAnchor),
            tallView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            tallView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
            tallView.bottomAnchor.constraint(equalTo: contentView.bottomAnchor),
            tallView.heightAnchor.constraint(equalToConstant: 2000),
        ])
    }
}
```

## Unbroken Constraint Chain: ScrollView + StackView

The recommended pattern for dynamic scrollable content. The stack view defines the content size automatically.

```swift
import UIKit

class ScrollableStackViewController: UIViewController {

    let scrollView = UIScrollView()
    let stackView = UIStackView()

    override func viewDidLoad() {
        super.viewDidLoad()
        style()
        layout()
        addContent()
    }

    private func style() {
        scrollView.translatesAutoresizingMaskIntoConstraints = false

        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.spacing = 16
    }

    private func layout() {
        view.addSubview(scrollView)
        scrollView.addSubview(stackView)

        NSLayoutConstraint.activate([
            // ScrollView pinned to view edges
            scrollView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            scrollView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            scrollView.bottomAnchor.constraint(equalTo: view.bottomAnchor),

            // StackView pinned to scrollView content layout guide
            stackView.topAnchor.constraint(equalTo: scrollView.contentLayoutGuide.topAnchor),
            stackView.leadingAnchor.constraint(equalTo: scrollView.contentLayoutGuide.leadingAnchor),
            stackView.trailingAnchor.constraint(equalTo: scrollView.contentLayoutGuide.trailingAnchor),
            stackView.bottomAnchor.constraint(equalTo: scrollView.contentLayoutGuide.bottomAnchor),

            // Width match prevents horizontal scrolling
            stackView.widthAnchor.constraint(equalTo: scrollView.frameLayoutGuide.widthAnchor),
        ])
    }

    private func addContent() {
        for i in 1...30 {
            let label = UILabel()
            label.text = "Row \(i)"
            label.font = .preferredFont(forTextStyle: .title2)
            label.textAlignment = .center
            label.backgroundColor = .systemGray6
            label.heightAnchor.constraint(equalToConstant: 60).isActive = true
            stackView.addArrangedSubview(label)
        }
    }
}
```

## Custom Scroll Tab View with Centering Logic

A horizontal scrolling tab bar that centers the selected tab, handling left boundary, middle, and right boundary cases.

```swift
import UIKit

protocol ScrollTabViewDelegate: AnyObject {
    func scrollTabView(_ view: ScrollTabView, didSelectTabAt index: Int)
}

class ScrollTabView: UIView {

    weak var delegate: ScrollTabViewDelegate?

    private let scrollView = UIScrollView()
    private let stackView = UIStackView()
    private var buttons: [UIButton] = []
    private var selectedIndex = 0

    private let tabs: [String]

    init(tabs: [String]) {
        self.tabs = tabs
        super.init(frame: .zero)
        setup()
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    private func setup() {
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        scrollView.showsHorizontalScrollIndicator = false
        addSubview(scrollView)

        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .horizontal
        stackView.spacing = 20
        scrollView.addSubview(stackView)

        NSLayoutConstraint.activate([
            scrollView.topAnchor.constraint(equalTo: topAnchor),
            scrollView.leadingAnchor.constraint(equalTo: leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: trailingAnchor),
            scrollView.bottomAnchor.constraint(equalTo: bottomAnchor),

            stackView.topAnchor.constraint(equalTo: scrollView.contentLayoutGuide.topAnchor),
            stackView.leadingAnchor.constraint(equalTo: scrollView.contentLayoutGuide.leadingAnchor, constant: 16),
            stackView.trailingAnchor.constraint(equalTo: scrollView.contentLayoutGuide.trailingAnchor, constant: -16),
            stackView.bottomAnchor.constraint(equalTo: scrollView.contentLayoutGuide.bottomAnchor),
            stackView.heightAnchor.constraint(equalTo: scrollView.frameLayoutGuide.heightAnchor),
        ])

        for (index, title) in tabs.enumerated() {
            let button = UIButton(type: .system)
            button.setTitle(title, for: .normal)
            button.tag = index
            button.addTarget(self, action: #selector(tabTapped(_:)), for: .touchUpInside)
            stackView.addArrangedSubview(button)
            buttons.append(button)
        }

        updateSelection()
    }

    @objc private func tabTapped(_ sender: UIButton) {
        selectedIndex = sender.tag
        updateSelection()
        centerTab(at: selectedIndex, animated: true)
        delegate?.scrollTabView(self, didSelectTabAt: selectedIndex)
    }

    private func updateSelection() {
        for (index, button) in buttons.enumerated() {
            button.titleLabel?.font = index == selectedIndex
                ? .systemFont(ofSize: 16, weight: .bold)
                : .systemFont(ofSize: 16, weight: .regular)
            button.tintColor = index == selectedIndex ? .label : .secondaryLabel
        }
    }

    /// Centers the selected tab, clamping to left/right boundaries.
    private func centerTab(at index: Int, animated: Bool) {
        guard index < buttons.count else { return }
        let button = buttons[index]

        let buttonCenter = button.frame.midX
        let scrollViewWidth = scrollView.bounds.width
        let contentWidth = scrollView.contentSize.width

        // Ideal offset to center the button
        var targetOffsetX = buttonCenter - scrollViewWidth / 2

        // Left boundary -- cannot scroll past the start
        targetOffsetX = max(targetOffsetX, 0)

        // Right boundary -- cannot scroll past the end
        let maxOffsetX = contentWidth - scrollViewWidth
        targetOffsetX = min(targetOffsetX, maxOffsetX)

        scrollView.setContentOffset(CGPoint(x: targetOffsetX, y: 0), animated: animated)
    }
}
```

### Usage

```swift
class TabDemoViewController: UIViewController, ScrollTabViewDelegate {

    override func viewDidLoad() {
        super.viewDidLoad()

        let tabs = ["Home", "Search", "Trending", "Library", "History", "Downloads", "Settings"]
        let tabView = ScrollTabView(tabs: tabs)
        tabView.delegate = self
        tabView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(tabView)

        NSLayoutConstraint.activate([
            tabView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
            tabView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            tabView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            tabView.heightAnchor.constraint(equalToConstant: 44),
        ])
    }

    func scrollTabView(_ view: ScrollTabView, didSelectTabAt index: Int) {
        print("Selected tab: \(index)")
    }
}
```
