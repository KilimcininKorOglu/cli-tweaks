# Nib Patterns

## ContentView Pattern for Custom Views Loaded from Nib

The standard pattern for loading a xib into a reusable UIView subclass. The nib's root view becomes a `contentView` that fills the custom view.

```swift
import UIKit

class PaymentCardView: UIView {

    @IBOutlet var contentView: UIView!
    @IBOutlet weak var cardNumberLabel: UILabel!
    @IBOutlet weak var expiryLabel: UILabel!
    @IBOutlet weak var nameLabel: UILabel!

    override init(frame: CGRect) {
        super.init(frame: frame)
        commonInit()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        commonInit()
    }

    private func commonInit() {
        // 1. Load the nib -- File's Owner is set to this class in Interface Builder
        Bundle.main.loadNibNamed("PaymentCardView", owner: self, options: nil)

        // 2. Add the content view and pin it to all edges
        contentView.translatesAutoresizingMaskIntoConstraints = false
        addSubview(contentView)

        NSLayoutConstraint.activate([
            contentView.topAnchor.constraint(equalTo: topAnchor),
            contentView.leadingAnchor.constraint(equalTo: leadingAnchor),
            contentView.trailingAnchor.constraint(equalTo: trailingAnchor),
            contentView.bottomAnchor.constraint(equalTo: bottomAnchor),
        ])
    }

    func configure(cardNumber: String, expiry: String, name: String) {
        cardNumberLabel.text = cardNumber
        expiryLabel.text = expiry
        nameLabel.text = name
    }
}
```

### Interface Builder Setup (File's Owner approach)

1. Create `PaymentCardView.xib`.
2. Select **File's Owner** in the document outline.
3. Set its Custom Class to `PaymentCardView`.
4. Connect the root view to the `contentView` outlet on File's Owner.
5. Connect other outlets (labels, buttons) to File's Owner.
6. Do NOT set the root view's Custom Class -- leave it as plain UIView.

### Usage

```swift
// Programmatic
let cardView = PaymentCardView()
cardView.configure(cardNumber: "**** 4242", expiry: "12/26", name: "John Doe")

// Or from another nib / storyboard via IBOutlet
@IBOutlet weak var cardView: PaymentCardView!
```

## Programmatic Nib Loading

Load a nib directly without the contentView pattern.

```swift
func loadBannerView() -> BannerView? {
    let nib = Bundle.main.loadNibNamed("BannerView", owner: nil, options: nil)
    return nib?.first as? BannerView
}
```

## IBDesignable + IBInspectable

Lets Interface Builder render a live preview of your custom view and exposes properties in the attributes inspector.

```swift
import UIKit

@IBDesignable
class RoundedCardView: UIView {

    @IBInspectable var cornerRadius: CGFloat = 12 {
        didSet {
            layer.cornerRadius = cornerRadius
        }
    }

    @IBInspectable var shadowOpacity: Float = 0.15 {
        didSet {
            layer.shadowOpacity = shadowOpacity
        }
    }

    @IBInspectable var borderColor: UIColor = .separator {
        didSet {
            layer.borderColor = borderColor.cgColor
        }
    }

    @IBInspectable var borderWidth: CGFloat = 0.5 {
        didSet {
            layer.borderWidth = borderWidth
        }
    }

    override init(frame: CGRect) {
        super.init(frame: frame)
        commonInit()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        commonInit()
    }

    private func commonInit() {
        layer.cornerRadius = cornerRadius
        layer.shadowOpacity = shadowOpacity
        layer.shadowOffset = CGSize(width: 0, height: 2)
        layer.shadowRadius = 4
        layer.borderColor = borderColor.cgColor
        layer.borderWidth = borderWidth
    }

    override func prepareForInterfaceBuilder() {
        super.prepareForInterfaceBuilder()
        commonInit()
    }
}
```

## TableViewCell Nib Pattern

For table view cells, set the **Custom Class** on the cell itself (not File's Owner). This is different from the contentView pattern above.

### Cell Class

```swift
import UIKit

class TransactionCell: UITableViewCell {

    @IBOutlet weak var iconImageView: UIImageView!
    @IBOutlet weak var titleLabel: UILabel!
    @IBOutlet weak var amountLabel: UILabel!
    @IBOutlet weak var dateLabel: UILabel!

    static let reuseIdentifier = "TransactionCell"
    static let nibName = "TransactionCell"

    override func awakeFromNib() {
        super.awakeFromNib()
        iconImageView.layer.cornerRadius = 20
        iconImageView.clipsToBounds = true
    }

    func configure(title: String, amount: String, date: String, isCredit: Bool) {
        titleLabel.text = title
        amountLabel.text = amount
        amountLabel.textColor = isCredit ? .systemGreen : .label
        dateLabel.text = date
    }
}
```

### Interface Builder Setup (Custom Class approach)

1. Create `TransactionCell.xib`.
2. Delete the default view. Drag in a **Table View Cell** from the object library.
3. Select the cell and set its **Custom Class** to `TransactionCell`.
4. Connect outlets directly to the cell (NOT to File's Owner).
5. Set the reuse identifier in the attributes inspector.

### Registration and Dequeue

```swift
class TransactionListViewController: UIViewController, UITableViewDataSource {

    let tableView = UITableView()

    override func viewDidLoad() {
        super.viewDidLoad()

        // Register the nib
        let nib = UINib(nibName: TransactionCell.nibName, bundle: nil)
        tableView.register(nib, forCellReuseIdentifier: TransactionCell.reuseIdentifier)

        tableView.dataSource = self
    }

    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return 10
    }

    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(
            withIdentifier: TransactionCell.reuseIdentifier,
            for: indexPath
        ) as! TransactionCell

        cell.configure(
            title: "Coffee Shop",
            amount: "-$4.50",
            date: "Jan 15",
            isCredit: false
        )

        return cell
    }
}
```

## ReusableView Protocol for Generic Cell Dequeue

Eliminate stringly-typed identifiers with a protocol-based approach.

```swift
import UIKit

protocol ReusableView {
    static var reuseIdentifier: String { get }
}

extension ReusableView {
    static var reuseIdentifier: String {
        return String(describing: self)
    }
}

protocol NibLoadable {
    static var nibName: String { get }
}

extension NibLoadable {
    static var nibName: String {
        return String(describing: self)
    }
}

// Conform cells to both protocols
extension TransactionCell: ReusableView, NibLoadable {}

// Extend UITableView for type-safe registration and dequeue
extension UITableView {

    func register<T: UITableViewCell>(_ cellType: T.Type)
        where T: ReusableView & NibLoadable
    {
        let nib = UINib(nibName: T.nibName, bundle: nil)
        register(nib, forCellReuseIdentifier: T.reuseIdentifier)
    }

    func dequeueReusableCell<T: UITableViewCell>(for indexPath: IndexPath) -> T
        where T: ReusableView
    {
        guard let cell = dequeueReusableCell(withIdentifier: T.reuseIdentifier, for: indexPath) as? T else {
            fatalError("Could not dequeue cell with identifier: \(T.reuseIdentifier)")
        }
        return cell
    }
}
```

### Usage

```swift
// Registration -- no string identifiers
tableView.register(TransactionCell.self)

// Dequeue -- type-safe, no casting
func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
    let cell: TransactionCell = tableView.dequeueReusableCell(for: indexPath)
    cell.configure(title: "Groceries", amount: "-$52.30", date: "Jan 16", isCredit: false)
    return cell
}
```

## intrinsicContentSize for Nib-Loaded Views

Override `intrinsicContentSize` when a nib-loaded view needs to communicate its preferred size to Auto Layout (e.g., when embedded in a stack view).

```swift
class RatingBadgeView: UIView {

    @IBOutlet var contentView: UIView!
    @IBOutlet weak var starLabel: UILabel!
    @IBOutlet weak var ratingLabel: UILabel!

    override init(frame: CGRect) {
        super.init(frame: frame)
        commonInit()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        commonInit()
    }

    private func commonInit() {
        Bundle.main.loadNibNamed("RatingBadgeView", owner: self, options: nil)
        contentView.translatesAutoresizingMaskIntoConstraints = false
        addSubview(contentView)
        NSLayoutConstraint.activate([
            contentView.topAnchor.constraint(equalTo: topAnchor),
            contentView.leadingAnchor.constraint(equalTo: leadingAnchor),
            contentView.trailingAnchor.constraint(equalTo: trailingAnchor),
            contentView.bottomAnchor.constraint(equalTo: bottomAnchor),
        ])
    }

    override var intrinsicContentSize: CGSize {
        return CGSize(width: 80, height: 32)
    }
}
```

## Header/Footer Nib Registration

### Section Header View

```swift
import UIKit

class SectionHeaderView: UITableViewHeaderFooterView {

    @IBOutlet weak var titleLabel: UILabel!
    @IBOutlet weak var actionButton: UIButton!

    static let reuseIdentifier = "SectionHeaderView"
    static let nibName = "SectionHeaderView"
}
```

### Interface Builder Setup

1. Create `SectionHeaderView.xib`.
2. Delete the default view. Drag in a **Table View Header Footer View**.
3. Set its Custom Class to `SectionHeaderView`.
4. Connect outlets to the header view (not File's Owner).

### Registration

```swift
override func viewDidLoad() {
    super.viewDidLoad()

    let headerNib = UINib(nibName: SectionHeaderView.nibName, bundle: nil)
    tableView.register(headerNib, forHeaderFooterViewReuseIdentifier: SectionHeaderView.reuseIdentifier)
}

func tableView(_ tableView: UITableView, viewForHeaderInSection section: Int) -> UIView? {
    let header = tableView.dequeueReusableHeaderFooterView(
        withIdentifier: SectionHeaderView.reuseIdentifier
    ) as! SectionHeaderView

    header.titleLabel.text = "Recent Transactions"
    header.actionButton.setTitle("See All", for: .normal)
    return header
}

func tableView(_ tableView: UITableView, heightForHeaderInSection section: Int) -> CGFloat {
    return 44
}
```

### Extending ReusableView for Headers/Footers

```swift
extension SectionHeaderView: ReusableView, NibLoadable {}

extension UITableView {

    func registerHeaderFooter<T: UITableViewHeaderFooterView>(_ viewType: T.Type)
        where T: ReusableView & NibLoadable
    {
        let nib = UINib(nibName: T.nibName, bundle: nil)
        register(nib, forHeaderFooterViewReuseIdentifier: T.reuseIdentifier)
    }

    func dequeueReusableHeaderFooterView<T: UITableViewHeaderFooterView>() -> T
        where T: ReusableView
    {
        guard let view = dequeueReusableHeaderFooterView(withIdentifier: T.reuseIdentifier) as? T else {
            fatalError("Could not dequeue header/footer with identifier: \(T.reuseIdentifier)")
        }
        return view
    }
}

// Usage
tableView.registerHeaderFooter(SectionHeaderView.self)
let header: SectionHeaderView = tableView.dequeueReusableHeaderFooterView()
```
