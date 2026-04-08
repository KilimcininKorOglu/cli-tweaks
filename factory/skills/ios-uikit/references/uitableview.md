# UITableView Patterns - Programmatic UIKit

## 1. Basic Setup

Programmatic UITableView with register, dataSource, and delegate.

```swift
import UIKit

class BasicTableViewController: UIViewController {

    private let cellReuseIdentifier = "ItemCell"

    private let tableView: UITableView = {
        let tv = UITableView(frame: .zero, style: .plain)
        tv.translatesAutoresizingMaskIntoConstraints = false
        return tv
    }()

    private var items = ["Apple", "Banana", "Cherry", "Date", "Elderberry"]

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Fruits"
        setupTableView()
    }

    private func setupTableView() {
        view.addSubview(tableView)

        NSLayoutConstraint.activate([
            tableView.topAnchor.constraint(equalTo: view.topAnchor),
            tableView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            tableView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            tableView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])

        tableView.register(UITableViewCell.self, forCellReuseIdentifier: cellReuseIdentifier)
        tableView.dataSource = self
        tableView.delegate = self
    }
}

// MARK: - UITableViewDataSource
extension BasicTableViewController: UITableViewDataSource {

    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return items.count
    }

    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: cellReuseIdentifier, for: indexPath)
        cell.textLabel?.text = items[indexPath.row]
        cell.accessoryType = .disclosureIndicator
        return cell
    }
}

// MARK: - UITableViewDelegate
extension BasicTableViewController: UITableViewDelegate {

    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        tableView.deselectRow(at: indexPath, animated: true)
        print("Selected: \(items[indexPath.row])")
    }

    func tableView(_ tableView: UITableView, heightForRowAt indexPath: IndexPath) -> CGFloat {
        return 60
    }
}
```

---

## 2. Reusable View Protocol Pattern

ReusableView and NibLoadableView protocols with generic dequeue extensions for type-safe cell registration and dequeuing.

```swift
import UIKit

// MARK: - Protocols

protocol ReusableView: AnyObject {
    static var reuseIdentifier: String { get }
}

extension ReusableView where Self: UIView {
    static var reuseIdentifier: String {
        return String(describing: self)
    }
}

protocol NibLoadableView: AnyObject {
    static var nibName: String { get }
}

extension NibLoadableView where Self: UIView {
    static var nibName: String {
        return String(describing: self)
    }
}

// MARK: - UITableView Extensions

extension UITableView {

    // Register a cell class (programmatic cells)
    func register<T: UITableViewCell>(_: T.Type) where T: ReusableView {
        register(T.self, forCellReuseIdentifier: T.reuseIdentifier)
    }

    // Register a cell from a nib
    func register<T: UITableViewCell>(_: T.Type) where T: ReusableView, T: NibLoadableView {
        let nib = UINib(nibName: T.nibName, bundle: nil)
        register(nib, forCellReuseIdentifier: T.reuseIdentifier)
    }

    // Generic dequeue — returns the concrete cell type
    func dequeueReusableCell<T: UITableViewCell>(for indexPath: IndexPath) -> T where T: ReusableView {
        guard let cell = dequeueReusableCell(withIdentifier: T.reuseIdentifier, for: indexPath) as? T else {
            fatalError("Could not dequeue cell with identifier: \(T.reuseIdentifier)")
        }
        return cell
    }

    // Register a header/footer view class
    func registerHeaderFooter<T: UITableViewHeaderFooterView>(_: T.Type) where T: ReusableView {
        register(T.self, forHeaderFooterViewReuseIdentifier: T.reuseIdentifier)
    }

    // Register a header/footer view from a nib
    func registerHeaderFooter<T: UITableViewHeaderFooterView>(_: T.Type) where T: ReusableView, T: NibLoadableView {
        let nib = UINib(nibName: T.nibName, bundle: nil)
        register(nib, forHeaderFooterViewReuseIdentifier: T.reuseIdentifier)
    }

    // Generic dequeue for header/footer
    func dequeueReusableHeaderFooterView<T: UITableViewHeaderFooterView>() -> T where T: ReusableView {
        guard let view = dequeueReusableHeaderFooterView(withIdentifier: T.reuseIdentifier) as? T else {
            fatalError("Could not dequeue header/footer with identifier: \(T.reuseIdentifier)")
        }
        return view
    }
}

// MARK: - Usage: Custom Cell

class ProfileCell: UITableViewCell, ReusableView {

    private let nameLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = .systemFont(ofSize: 16, weight: .medium)
        return label
    }()

    private let subtitleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = .systemFont(ofSize: 13, weight: .regular)
        label.textColor = .secondaryLabel
        return label
    }()

    override init(style: UITableViewCell.CellStyle, reuseIdentifier: String?) {
        super.init(style: style, reuseIdentifier: reuseIdentifier)
        setupViews()
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    private func setupViews() {
        contentView.addSubview(nameLabel)
        contentView.addSubview(subtitleLabel)

        NSLayoutConstraint.activate([
            nameLabel.topAnchor.constraint(equalTo: contentView.topAnchor, padding: 12),
            nameLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            nameLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),

            subtitleLabel.topAnchor.constraint(equalTo: nameLabel.bottomAnchor, constant: 4),
            subtitleLabel.leadingAnchor.constraint(equalTo: nameLabel.leadingAnchor),
            subtitleLabel.trailingAnchor.constraint(equalTo: nameLabel.trailingAnchor),
            subtitleLabel.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -12)
        ])
    }

    func configure(name: String, subtitle: String) {
        nameLabel.text = name
        subtitleLabel.text = subtitle
    }
}

// MARK: - Usage in ViewController

class ProfileListViewController: UIViewController {

    private let tableView = UITableView()

    override func viewDidLoad() {
        super.viewDidLoad()

        // Type-safe register — no string identifiers
        tableView.register(ProfileCell.self)

        tableView.dataSource = self
    }
}

extension ProfileListViewController: UITableViewDataSource {

    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return 10
    }

    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        // Type-safe dequeue — returns ProfileCell directly
        let cell: ProfileCell = tableView.dequeueReusableCell(for: indexPath)
        cell.configure(name: "User \(indexPath.row)", subtitle: "Details here")
        return cell
    }
}
```

---

## 3. Custom Header/Footer with Nib (ContentView Pattern)

A reusable pattern for building a custom table header/footer using a standalone UIView loaded from a nib, auto-sized via `intrinsicContentSize` and `systemLayoutSizeFitting`.

```swift
import UIKit

// MARK: - Header Content View (designed in a .xib or programmatically)

class ProfileHeaderContentView: UIView {

    private let avatarImageView: UIImageView = {
        let iv = UIImageView()
        iv.translatesAutoresizingMaskIntoConstraints = false
        iv.contentMode = .scaleAspectFill
        iv.clipsToBounds = true
        iv.backgroundColor = .systemGray5
        iv.layer.cornerRadius = 40
        return iv
    }()

    private let titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = .systemFont(ofSize: 22, weight: .bold)
        label.textAlignment = .center
        return label
    }()

    private let descriptionLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = .systemFont(ofSize: 14)
        label.textColor = .secondaryLabel
        label.textAlignment = .center
        label.numberOfLines = 0
        return label
    }()

    override init(frame: CGRect) {
        super.init(frame: frame)
        setupViews()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        setupViews()
    }

    // Allows the view to size itself based on its content
    override var intrinsicContentSize: CGSize {
        return CGSize(width: UIView.noIntrinsicMetric, height: 180)
    }

    private func setupViews() {
        addSubview(avatarImageView)
        addSubview(titleLabel)
        addSubview(descriptionLabel)

        NSLayoutConstraint.activate([
            avatarImageView.topAnchor.constraint(equalTo: topAnchor, constant: 20),
            avatarImageView.centerXAnchor.constraint(equalTo: centerXAnchor),
            avatarImageView.widthAnchor.constraint(equalToConstant: 80),
            avatarImageView.heightAnchor.constraint(equalToConstant: 80),

            titleLabel.topAnchor.constraint(equalTo: avatarImageView.bottomAnchor, constant: 12),
            titleLabel.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            titleLabel.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),

            descriptionLabel.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 4),
            descriptionLabel.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            descriptionLabel.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),
            descriptionLabel.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -20)
        ])
    }

    func configure(name: String, description: String, image: UIImage?) {
        titleLabel.text = name
        descriptionLabel.text = description
        avatarImageView.image = image
    }
}

// MARK: - ViewController using setupTableViewHeader

class ProfileViewController: UIViewController {

    private let tableView: UITableView = {
        let tv = UITableView(frame: .zero, style: .grouped)
        tv.translatesAutoresizingMaskIntoConstraints = false
        return tv
    }()

    private let headerContentView = ProfileHeaderContentView()

    override func viewDidLoad() {
        super.viewDidLoad()
        view.addSubview(tableView)

        NSLayoutConstraint.activate([
            tableView.topAnchor.constraint(equalTo: view.topAnchor),
            tableView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            tableView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            tableView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])

        headerContentView.configure(
            name: "Jane Appleseed",
            description: "iOS Developer from Cupertino",
            image: UIImage(systemName: "person.circle.fill")
        )

        setupTableViewHeader(headerContentView)
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        // Recalculate on rotation / size changes
        setupTableViewHeader(headerContentView)
    }

    /// Sizes and assigns a content view as the tableHeaderView using Auto Layout.
    /// Call this in viewDidLoad and viewDidLayoutSubviews.
    private func setupTableViewHeader(_ headerView: UIView) {
        headerView.translatesAutoresizingMaskIntoConstraints = false

        // Temporary container so the header can use Auto Layout
        let containerView = UIView()
        containerView.addSubview(headerView)

        NSLayoutConstraint.activate([
            headerView.topAnchor.constraint(equalTo: containerView.topAnchor),
            headerView.leadingAnchor.constraint(equalTo: containerView.leadingAnchor),
            headerView.trailingAnchor.constraint(equalTo: containerView.trailingAnchor),
            headerView.bottomAnchor.constraint(equalTo: containerView.bottomAnchor),
            headerView.widthAnchor.constraint(equalToConstant: tableView.bounds.width)
        ])

        containerView.setNeedsLayout()
        containerView.layoutIfNeeded()

        let size = containerView.systemLayoutSizeFitting(
            CGSize(width: tableView.bounds.width, height: UIView.layoutFittingCompressedSize.height),
            withHorizontalFittingPriority: .required,
            verticalFittingPriority: .fittingSizeLevel
        )

        // Remove from temporary container
        headerView.removeFromSuperview()
        headerView.translatesAutoresizingMaskIntoConstraints = true
        headerView.frame.size = size

        tableView.tableHeaderView = headerView
    }
}

// MARK: - Simpler alternative: direct frame-based header sizing

extension UITableView {

    /// Convenience to auto-size a tableHeaderView after its content changes.
    func sizeHeaderToFit() {
        guard let headerView = tableHeaderView else { return }

        let targetSize = CGSize(width: bounds.width, height: UIView.layoutFittingCompressedSize.height)
        headerView.translatesAutoresizingMaskIntoConstraints = false

        let widthConstraint = headerView.widthAnchor.constraint(equalToConstant: bounds.width)
        widthConstraint.isActive = true

        let size = headerView.systemLayoutSizeFitting(
            targetSize,
            withHorizontalFittingPriority: .required,
            verticalFittingPriority: .fittingSizeLevel
        )

        widthConstraint.isActive = false
        headerView.translatesAutoresizingMaskIntoConstraints = true
        headerView.frame.size.height = size.height

        tableHeaderView = headerView
    }
}
```

---

## 4. Sections with Data Model

Transaction / TransactionSection / TransactionViewModel pattern for grouped table view data.

```swift
import UIKit

// MARK: - Models

struct Transaction {
    let id: String
    let title: String
    let amount: Decimal
    let date: Date
    let category: String
}

struct TransactionSection {
    let title: String
    var transactions: [Transaction]
}

// MARK: - ViewModel

class TransactionViewModel {

    private(set) var sections: [TransactionSection] = []

    private let currencyFormatter: NumberFormatter = {
        let f = NumberFormatter()
        f.numberStyle = .currency
        f.locale = Locale.current
        return f
    }()

    private let sectionDateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "MMMM yyyy"
        return f
    }()

    func load() {
        let allTransactions = [
            Transaction(id: "1", title: "Grocery Store", amount: -52.30, date: makeDate(2025, 3, 15), category: "Food"),
            Transaction(id: "2", title: "Salary", amount: 3200.00, date: makeDate(2025, 3, 1), category: "Income"),
            Transaction(id: "3", title: "Electric Bill", amount: -95.00, date: makeDate(2025, 2, 20), category: "Utilities"),
            Transaction(id: "4", title: "Coffee Shop", amount: -4.50, date: makeDate(2025, 2, 18), category: "Food"),
            Transaction(id: "5", title: "Freelance Payment", amount: 750.00, date: makeDate(2025, 2, 10), category: "Income"),
        ]

        // Group by month
        let grouped = Dictionary(grouping: allTransactions) { transaction in
            sectionDateFormatter.string(from: transaction.date)
        }

        sections = grouped
            .map { TransactionSection(title: $0.key, transactions: $0.value) }
            .sorted { $0.transactions.first!.date > $1.transactions.first!.date }
    }

    func formattedAmount(for transaction: Transaction) -> String {
        return currencyFormatter.string(from: transaction.amount as NSDecimalNumber) ?? ""
    }

    func transaction(at indexPath: IndexPath) -> Transaction {
        return sections[indexPath.section].transactions[indexPath.row]
    }

    private func makeDate(_ year: Int, _ month: Int, _ day: Int) -> Date {
        var components = DateComponents()
        components.year = year
        components.month = month
        components.day = day
        return Calendar.current.date(from: components)!
    }
}

// MARK: - Custom Cell

class TransactionCell: UITableViewCell, ReusableView {

    private let titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = .systemFont(ofSize: 16, weight: .medium)
        return label
    }()

    private let categoryLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = .systemFont(ofSize: 12, weight: .regular)
        label.textColor = .secondaryLabel
        return label
    }()

    private let amountLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = .systemFont(ofSize: 16, weight: .semibold)
        label.textAlignment = .right
        return label
    }()

    override init(style: UITableViewCell.CellStyle, reuseIdentifier: String?) {
        super.init(style: style, reuseIdentifier: reuseIdentifier)
        setupViews()
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    private func setupViews() {
        contentView.addSubview(titleLabel)
        contentView.addSubview(categoryLabel)
        contentView.addSubview(amountLabel)

        NSLayoutConstraint.activate([
            titleLabel.topAnchor.constraint(equalTo: contentView.topAnchor, constant: 10),
            titleLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            titleLabel.trailingAnchor.constraint(lessThanOrEqualTo: amountLabel.leadingAnchor, constant: -8),

            categoryLabel.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 2),
            categoryLabel.leadingAnchor.constraint(equalTo: titleLabel.leadingAnchor),
            categoryLabel.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -10),

            amountLabel.centerYAnchor.constraint(equalTo: contentView.centerYAnchor),
            amountLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            amountLabel.widthAnchor.constraint(greaterThanOrEqualToConstant: 80)
        ])
    }

    func configure(with transaction: Transaction, formattedAmount: String) {
        titleLabel.text = transaction.title
        categoryLabel.text = transaction.category
        amountLabel.text = formattedAmount
        amountLabel.textColor = transaction.amount >= 0 ? .systemGreen : .label
    }
}

// MARK: - ViewController

class TransactionListViewController: UIViewController {

    private let tableView: UITableView = {
        let tv = UITableView(frame: .zero, style: .grouped)
        tv.translatesAutoresizingMaskIntoConstraints = false
        return tv
    }()

    private let viewModel = TransactionViewModel()

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Transactions"

        view.addSubview(tableView)
        NSLayoutConstraint.activate([
            tableView.topAnchor.constraint(equalTo: view.topAnchor),
            tableView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            tableView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            tableView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])

        tableView.register(TransactionCell.self)
        tableView.dataSource = self
        tableView.delegate = self

        viewModel.load()
        tableView.reloadData()
    }
}

extension TransactionListViewController: UITableViewDataSource {

    func numberOfSections(in tableView: UITableView) -> Int {
        return viewModel.sections.count
    }

    func tableView(_ tableView: UITableView, titleForHeaderInSection section: Int) -> String? {
        return viewModel.sections[section].title
    }

    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return viewModel.sections[section].transactions.count
    }

    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell: TransactionCell = tableView.dequeueReusableCell(for: indexPath)
        let transaction = viewModel.transaction(at: indexPath)
        cell.configure(with: transaction, formattedAmount: viewModel.formattedAmount(for: transaction))
        return cell
    }
}

extension TransactionListViewController: UITableViewDelegate {

    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        tableView.deselectRow(at: indexPath, animated: true)
        let transaction = viewModel.transaction(at: indexPath)
        print("Selected transaction: \(transaction.title)")
    }
}
```

---

## 5. Inserting Cells

Single row insert, batch insert with `beginUpdates`/`endUpdates`, and insert into a specific section.

```swift
import UIKit

class InsertableCellsViewController: UIViewController {

    private let tableView: UITableView = {
        let tv = UITableView(frame: .zero, style: .plain)
        tv.translatesAutoresizingMaskIntoConstraints = false
        return tv
    }()

    private var sections: [[String]] = [
        ["Row A1", "Row A2"],
        ["Row B1", "Row B2"]
    ]

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Insert Demo"

        view.addSubview(tableView)
        NSLayoutConstraint.activate([
            tableView.topAnchor.constraint(equalTo: view.topAnchor),
            tableView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            tableView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            tableView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])

        tableView.register(UITableViewCell.self, forCellReuseIdentifier: "Cell")
        tableView.dataSource = self

        navigationItem.rightBarButtonItems = [
            UIBarButtonItem(title: "Single", style: .plain, target: self, action: #selector(insertSingleRow)),
            UIBarButtonItem(title: "Batch", style: .plain, target: self, action: #selector(insertBatchRows)),
            UIBarButtonItem(title: "Section", style: .plain, target: self, action: #selector(insertToSection))
        ]
    }

    // MARK: - Insert a single row at the end of section 0

    @objc private func insertSingleRow() {
        let newItem = "New Row \(sections[0].count + 1)"
        let newIndexPath = IndexPath(row: sections[0].count, section: 0)

        // 1. Update the data model FIRST
        sections[0].append(newItem)

        // 2. Then insert into the table view
        tableView.insertRows(at: [newIndexPath], with: .automatic)
    }

    // MARK: - Batch insert multiple rows

    @objc private func insertBatchRows() {
        let newItems = ["Batch Item 1", "Batch Item 2", "Batch Item 3"]
        let startIndex = sections[0].count

        let indexPaths = newItems.enumerated().map { offset, _ in
            IndexPath(row: startIndex + offset, section: 0)
        }

        // 1. Update the data model
        sections[0].append(contentsOf: newItems)

        // 2. Wrap multiple inserts in beginUpdates/endUpdates
        tableView.beginUpdates()
        tableView.insertRows(at: indexPaths, with: .fade)
        tableView.endUpdates()
    }

    // MARK: - Insert into a specific section

    @objc private func insertToSection() {
        let newItem = "Section B New \(sections[1].count + 1)"
        let targetSection = 1
        let newIndexPath = IndexPath(row: sections[targetSection].count, section: targetSection)

        sections[targetSection].append(newItem)

        tableView.insertRows(at: [newIndexPath], with: .left)
    }

    // MARK: - performBatchUpdates (modern alternative to beginUpdates/endUpdates)

    private func insertWithPerformBatchUpdates() {
        let newItems = ["Modern 1", "Modern 2"]
        let startIndex = sections[0].count

        let indexPaths = newItems.enumerated().map { offset, _ in
            IndexPath(row: startIndex + offset, section: 0)
        }

        sections[0].append(contentsOf: newItems)

        tableView.performBatchUpdates {
            tableView.insertRows(at: indexPaths, with: .automatic)
        } completion: { finished in
            print("Batch update completed: \(finished)")
        }
    }

    // MARK: - Insert an entire new section

    private func insertNewSection() {
        let newSectionData = ["Section C Row 1", "Section C Row 2"]
        let newSectionIndex = sections.count

        sections.append(newSectionData)

        tableView.insertSections(IndexSet(integer: newSectionIndex), with: .automatic)
    }
}

// MARK: - UITableViewDataSource
extension InsertableCellsViewController: UITableViewDataSource {

    func numberOfSections(in tableView: UITableView) -> Int {
        return sections.count
    }

    func tableView(_ tableView: UITableView, titleForHeaderInSection section: Int) -> String? {
        return "Section \(section)"
    }

    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return sections[section].count
    }

    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: "Cell", for: indexPath)
        cell.textLabel?.text = sections[indexPath.section][indexPath.row]
        return cell
    }
}
```

---

## 6. Diffable Data Source

Hashable model, `UITableViewDiffableDataSource` setup, snapshot apply, and filtered search.

```swift
import UIKit

// MARK: - Hashable Model

struct Contact: Hashable {
    let id: UUID
    let name: String
    let email: String
    let department: String

    // Hashable conformance uses id for uniqueness
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }

    static func == (lhs: Contact, rhs: Contact) -> Bool {
        return lhs.id == rhs.id
    }
}

// MARK: - Section Identifier

enum ContactSection: String, CaseIterable {
    case favorites = "Favorites"
    case all = "All Contacts"
}

// MARK: - ViewController

class DiffableContactsViewController: UIViewController {

    private let tableView: UITableView = {
        let tv = UITableView(frame: .zero, style: .insetGrouped)
        tv.translatesAutoresizingMaskIntoConstraints = false
        return tv
    }()

    private let searchController = UISearchController(searchResultsController: nil)

    private var dataSource: UITableViewDiffableDataSource<ContactSection, Contact>!

    private var allContacts: [Contact] = []
    private var favoriteContacts: [Contact] = []

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Contacts"

        setupSearchController()
        setupTableView()
        configureDataSource()
        loadData()
    }

    private func setupSearchController() {
        searchController.searchResultsUpdater = self
        searchController.obscuresBackgroundDuringPresentation = false
        searchController.searchBar.placeholder = "Search contacts"
        navigationItem.searchController = searchController
        definesPresentationContext = true
    }

    private func setupTableView() {
        view.addSubview(tableView)
        NSLayoutConstraint.activate([
            tableView.topAnchor.constraint(equalTo: view.topAnchor),
            tableView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            tableView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            tableView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])

        tableView.register(UITableViewCell.self, forCellReuseIdentifier: "ContactCell")
        tableView.delegate = self
    }

    // MARK: - Configure Diffable Data Source

    private func configureDataSource() {
        dataSource = UITableViewDiffableDataSource<ContactSection, Contact>(
            tableView: tableView
        ) { tableView, indexPath, contact in
            let cell = tableView.dequeueReusableCell(withIdentifier: "ContactCell", for: indexPath)

            var content = cell.defaultContentConfiguration()
            content.text = contact.name
            content.secondaryText = contact.email
            content.image = UIImage(systemName: "person.circle")
            cell.contentConfiguration = content

            return cell
        }

        // Optional: customize section header titles
        dataSource.defaultRowAnimation = .fade
    }

    // MARK: - Load Data and Apply Snapshot

    private func loadData() {
        allContacts = [
            Contact(id: UUID(), name: "Alice Johnson", email: "alice@example.com", department: "Engineering"),
            Contact(id: UUID(), name: "Bob Smith", email: "bob@example.com", department: "Design"),
            Contact(id: UUID(), name: "Carol White", email: "carol@example.com", department: "Engineering"),
            Contact(id: UUID(), name: "David Brown", email: "david@example.com", department: "Marketing"),
            Contact(id: UUID(), name: "Eve Davis", email: "eve@example.com", department: "Engineering"),
        ]

        favoriteContacts = [allContacts[0], allContacts[2]]

        applySnapshot()
    }

    // MARK: - Apply Snapshot

    private func applySnapshot(filter: String? = nil, animatingDifferences: Bool = true) {
        var snapshot = NSDiffableDataSourceSnapshot<ContactSection, Contact>()

        var filteredFavorites = favoriteContacts
        var filteredAll = allContacts

        // Apply search filter
        if let filter = filter, !filter.isEmpty {
            filteredFavorites = favoriteContacts.filter {
                $0.name.localizedCaseInsensitiveContains(filter)
            }
            filteredAll = allContacts.filter {
                $0.name.localizedCaseInsensitiveContains(filter)
            }
        }

        // Only add sections that have items
        if !filteredFavorites.isEmpty {
            snapshot.appendSections([.favorites])
            snapshot.appendItems(filteredFavorites, toSection: .favorites)
        }

        if !filteredAll.isEmpty {
            snapshot.appendSections([.all])
            snapshot.appendItems(filteredAll, toSection: .all)
        }

        dataSource.apply(snapshot, animatingDifferences: animatingDifferences)
    }

    // MARK: - Add a new contact dynamically

    func addContact(_ contact: Contact) {
        allContacts.append(contact)

        // Get the current snapshot, append, and re-apply
        var snapshot = dataSource.snapshot()

        if !snapshot.sectionIdentifiers.contains(.all) {
            snapshot.appendSections([.all])
        }
        snapshot.appendItems([contact], toSection: .all)

        dataSource.apply(snapshot, animatingDifferences: true)
    }

    // MARK: - Delete a contact

    func deleteContact(_ contact: Contact) {
        allContacts.removeAll { $0.id == contact.id }
        favoriteContacts.removeAll { $0.id == contact.id }

        var snapshot = dataSource.snapshot()
        snapshot.deleteItems([contact])

        // Remove empty sections
        for section in snapshot.sectionIdentifiers where snapshot.itemIdentifiers(inSection: section).isEmpty {
            snapshot.deleteSections([section])
        }

        dataSource.apply(snapshot, animatingDifferences: true)
    }
}

// MARK: - UITableViewDelegate
extension DiffableContactsViewController: UITableViewDelegate {

    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        tableView.deselectRow(at: indexPath, animated: true)
        guard let contact = dataSource.itemIdentifier(for: indexPath) else { return }
        print("Selected: \(contact.name)")
    }
}

// MARK: - UISearchResultsUpdating (Filtered Search)
extension DiffableContactsViewController: UISearchResultsUpdating {

    func updateSearchResults(for searchController: UISearchController) {
        let searchText = searchController.searchBar.text
        applySnapshot(filter: searchText)
    }
}
```

---

## 7. Swipeable Cells

Edit mode delete, trailing swipe actions, and leading swipe actions with images.

```swift
import UIKit

class SwipeableCellsViewController: UIViewController {

    private let tableView: UITableView = {
        let tv = UITableView(frame: .zero, style: .plain)
        tv.translatesAutoresizingMaskIntoConstraints = false
        return tv
    }()

    struct Email {
        let sender: String
        let subject: String
        var isRead: Bool
        var isFlagged: Bool
    }

    private var emails: [Email] = [
        Email(sender: "Alice", subject: "Meeting tomorrow", isRead: false, isFlagged: false),
        Email(sender: "Bob", subject: "Project update", isRead: true, isFlagged: false),
        Email(sender: "Carol", subject: "Invoice attached", isRead: false, isFlagged: true),
        Email(sender: "David", subject: "Quick question", isRead: true, isFlagged: false),
        Email(sender: "Eve", subject: "Lunch plans?", isRead: false, isFlagged: false),
    ]

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Inbox"

        view.addSubview(tableView)
        NSLayoutConstraint.activate([
            tableView.topAnchor.constraint(equalTo: view.topAnchor),
            tableView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            tableView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            tableView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])

        tableView.register(UITableViewCell.self, forCellReuseIdentifier: "EmailCell")
        tableView.dataSource = self
        tableView.delegate = self

        // Enable Edit button for edit-mode deletion
        navigationItem.rightBarButtonItem = editButtonItem
    }

    // Toggle table editing mode
    override func setEditing(_ editing: Bool, animated: Bool) {
        super.setEditing(editing, animated: animated)
        tableView.setEditing(editing, animated: animated)
    }
}

// MARK: - UITableViewDataSource
extension SwipeableCellsViewController: UITableViewDataSource {

    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return emails.count
    }

    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: "EmailCell", for: indexPath)
        let email = emails[indexPath.row]

        var content = cell.defaultContentConfiguration()
        content.text = email.sender
        content.secondaryText = email.subject
        content.textProperties.font = email.isRead
            ? .systemFont(ofSize: 16, weight: .regular)
            : .systemFont(ofSize: 16, weight: .bold)
        if email.isFlagged {
            content.image = UIImage(systemName: "flag.fill")
            content.imageProperties.tintColor = .systemOrange
        } else {
            content.image = UIImage(systemName: "envelope")
        }
        cell.contentConfiguration = content

        return cell
    }

    // MARK: - Edit Mode Delete Support

    func tableView(_ tableView: UITableView, canEditRowAt indexPath: IndexPath) -> Bool {
        return true
    }

    func tableView(_ tableView: UITableView, commit editingStyle: UITableViewCell.EditingStyle,
                   forRowAt indexPath: IndexPath) {
        if editingStyle == .delete {
            emails.remove(at: indexPath.row)
            tableView.deleteRows(at: [indexPath], with: .automatic)
        }
    }
}

// MARK: - UITableViewDelegate — Swipe Actions
extension SwipeableCellsViewController: UITableViewDelegate {

    // MARK: Trailing Swipe Actions (swipe left)

    func tableView(_ tableView: UITableView, trailingSwipeActionsConfigurationForRowAt indexPath: IndexPath)
        -> UISwipeActionsConfiguration?
    {
        // Delete action
        let deleteAction = UIContextualAction(style: .destructive, title: nil) { [weak self] _, _, completionHandler in
            self?.emails.remove(at: indexPath.row)
            tableView.deleteRows(at: [indexPath], with: .automatic)
            completionHandler(true)
        }
        deleteAction.image = UIImage(systemName: "trash.fill")
        deleteAction.backgroundColor = .systemRed

        // Archive action
        let archiveAction = UIContextualAction(style: .normal, title: nil) { [weak self] _, _, completionHandler in
            guard let self = self else { return }
            print("Archived: \(self.emails[indexPath.row].subject)")
            self.emails.remove(at: indexPath.row)
            tableView.deleteRows(at: [indexPath], with: .automatic)
            completionHandler(true)
        }
        archiveAction.image = UIImage(systemName: "archivebox.fill")
        archiveAction.backgroundColor = .systemPurple

        let configuration = UISwipeActionsConfiguration(actions: [deleteAction, archiveAction])
        configuration.performsFirstActionWithFullSwipe = true  // full swipe triggers delete
        return configuration
    }

    // MARK: Leading Swipe Actions (swipe right)

    func tableView(_ tableView: UITableView, leadingSwipeActionsConfigurationForRowAt indexPath: IndexPath)
        -> UISwipeActionsConfiguration?
    {
        // Toggle read/unread
        let email = emails[indexPath.row]
        let readAction = UIContextualAction(style: .normal, title: nil) { [weak self] _, _, completionHandler in
            self?.emails[indexPath.row].isRead.toggle()
            tableView.reloadRows(at: [indexPath], with: .automatic)
            completionHandler(true)
        }
        readAction.image = email.isRead
            ? UIImage(systemName: "envelope.badge.fill")
            : UIImage(systemName: "envelope.open.fill")
        readAction.backgroundColor = .systemBlue

        // Toggle flag
        let flagAction = UIContextualAction(style: .normal, title: nil) { [weak self] _, _, completionHandler in
            self?.emails[indexPath.row].isFlagged.toggle()
            tableView.reloadRows(at: [indexPath], with: .automatic)
            completionHandler(true)
        }
        flagAction.image = email.isFlagged
            ? UIImage(systemName: "flag.slash.fill")
            : UIImage(systemName: "flag.fill")
        flagAction.backgroundColor = .systemOrange

        let configuration = UISwipeActionsConfiguration(actions: [readAction, flagAction])
        configuration.performsFirstActionWithFullSwipe = false
        return configuration
    }
}
```

---

## 8. Moveable Cells

Custom `DiffableDataSource` subclass with `canMoveRowAt`/`moveRowAt`, plus long press gesture for reordering with snapshot-based animation.

```swift
import UIKit

// MARK: - Model

struct Playlist: Hashable {
    let id: UUID
    var name: String
    var position: Int

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }

    static func == (lhs: Playlist, rhs: Playlist) -> Bool {
        return lhs.id == rhs.id
    }
}

enum PlaylistSection: CaseIterable {
    case main
}

// MARK: - Custom Diffable Data Source Subclass

class PlaylistDiffableDataSource: UITableViewDiffableDataSource<PlaylistSection, Playlist> {

    // Enable move support
    override func tableView(_ tableView: UITableView, canMoveRowAt indexPath: IndexPath) -> Bool {
        return true
    }

    // Handle the move — update the snapshot to match the new order
    override func tableView(_ tableView: UITableView, moveRowAt sourceIndexPath: IndexPath,
                            to destinationIndexPath: IndexPath) {
        guard let sourceItem = itemIdentifier(for: sourceIndexPath) else { return }

        // Guard against same-position no-op
        guard sourceIndexPath != destinationIndexPath else { return }

        var currentSnapshot = snapshot()
        currentSnapshot.deleteItems([sourceItem])

        if let destinationItem = itemIdentifier(for: destinationIndexPath) {
            let isAfter = destinationIndexPath.row > sourceIndexPath.row
            if isAfter {
                currentSnapshot.insertItems([sourceItem], afterItem: destinationItem)
            } else {
                currentSnapshot.insertItems([sourceItem], beforeItem: destinationItem)
            }
        } else {
            // Destination is past the last item; append
            currentSnapshot.appendItems([sourceItem], toSection: .main)
        }

        // Apply without animation — the table view already animated the move
        apply(currentSnapshot, animatingDifferences: false)
    }

    // Optionally disable swipe-to-delete in edit mode
    override func tableView(_ tableView: UITableView, canEditRowAt indexPath: IndexPath) -> Bool {
        return true
    }
}

// MARK: - ViewController with Edit Mode Reordering

class MoveableCellsViewController: UIViewController {

    private let tableView: UITableView = {
        let tv = UITableView(frame: .zero, style: .plain)
        tv.translatesAutoresizingMaskIntoConstraints = false
        return tv
    }()

    private var dataSource: PlaylistDiffableDataSource!

    private var playlists: [Playlist] = [
        Playlist(id: UUID(), name: "Morning Vibes", position: 0),
        Playlist(id: UUID(), name: "Workout Mix", position: 1),
        Playlist(id: UUID(), name: "Chill Evening", position: 2),
        Playlist(id: UUID(), name: "Focus Mode", position: 3),
        Playlist(id: UUID(), name: "Road Trip", position: 4),
    ]

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Playlists"

        view.addSubview(tableView)
        NSLayoutConstraint.activate([
            tableView.topAnchor.constraint(equalTo: view.topAnchor),
            tableView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            tableView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            tableView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])

        tableView.register(UITableViewCell.self, forCellReuseIdentifier: "PlaylistCell")

        // Edit button for reorder handles
        navigationItem.rightBarButtonItem = editButtonItem

        configureDataSource()
        applySnapshot()
        addLongPressGesture()
    }

    override func setEditing(_ editing: Bool, animated: Bool) {
        super.setEditing(editing, animated: animated)
        tableView.setEditing(editing, animated: animated)
    }

    // MARK: - Data Source

    private func configureDataSource() {
        dataSource = PlaylistDiffableDataSource(
            tableView: tableView
        ) { tableView, indexPath, playlist in
            let cell = tableView.dequeueReusableCell(withIdentifier: "PlaylistCell", for: indexPath)
            var content = cell.defaultContentConfiguration()
            content.text = playlist.name
            content.image = UIImage(systemName: "music.note.list")
            cell.contentConfiguration = content
            return cell
        }

        dataSource.defaultRowAnimation = .fade
    }

    private func applySnapshot() {
        var snapshot = NSDiffableDataSourceSnapshot<PlaylistSection, Playlist>()
        snapshot.appendSections([.main])
        snapshot.appendItems(playlists, toSection: .main)
        dataSource.apply(snapshot, animatingDifferences: true)
    }

    // MARK: - Long Press Gesture for Drag Reordering

    private func addLongPressGesture() {
        let longPress = UILongPressGestureRecognizer(target: self, action: #selector(handleLongPress(_:)))
        longPress.minimumPressDuration = 0.3
        tableView.addGestureRecognizer(longPress)
    }

    private var dragIndexPath: IndexPath?
    private var dragCellSnapshot: UIView?

    @objc private func handleLongPress(_ gesture: UILongPressGestureRecognizer) {
        let location = gesture.location(in: tableView)

        switch gesture.state {
        case .began:
            guard let indexPath = tableView.indexPathForRow(at: location),
                  let cell = tableView.cellForRow(at: indexPath) else { return }

            dragIndexPath = indexPath

            // Create a snapshot of the cell for dragging
            let snapshot = cell.snapshotView(afterScreenUpdates: true)!
            snapshot.frame = cell.frame
            snapshot.alpha = 0.9
            snapshot.layer.shadowColor = UIColor.black.cgColor
            snapshot.layer.shadowOpacity = 0.2
            snapshot.layer.shadowRadius = 4
            dragCellSnapshot = snapshot
            tableView.addSubview(snapshot)

            // Animate the lift
            UIView.animate(withDuration: 0.2) {
                snapshot.transform = CGAffineTransform(scaleX: 1.05, y: 1.05)
                snapshot.center.y = location.y
                cell.alpha = 0
            }

        case .changed:
            guard let snapshot = dragCellSnapshot else { return }
            snapshot.center.y = location.y

            // Swap cells if hovering over a different row
            guard let sourceIndexPath = dragIndexPath,
                  let destinationIndexPath = tableView.indexPathForRow(at: location),
                  sourceIndexPath != destinationIndexPath else { return }

            // Move in the data source (snapshot-based)
            guard let sourceItem = dataSource.itemIdentifier(for: sourceIndexPath),
                  let destItem = dataSource.itemIdentifier(for: destinationIndexPath) else { return }

            var currentSnapshot = dataSource.snapshot()
            // Determine relative order and insert accordingly
            if sourceIndexPath.row < destinationIndexPath.row {
                currentSnapshot.moveItem(sourceItem, afterItem: destItem)
            } else {
                currentSnapshot.moveItem(sourceItem, beforeItem: destItem)
            }
            dataSource.apply(currentSnapshot, animatingDifferences: true)

            dragIndexPath = destinationIndexPath

        case .ended, .cancelled:
            guard let sourceIndexPath = dragIndexPath,
                  let cell = tableView.cellForRow(at: sourceIndexPath) else {
                dragCellSnapshot?.removeFromSuperview()
                dragCellSnapshot = nil
                dragIndexPath = nil
                return
            }

            // Animate drop
            UIView.animate(withDuration: 0.2, animations: {
                self.dragCellSnapshot?.center = cell.center
                self.dragCellSnapshot?.transform = .identity
            }, completion: { _ in
                cell.alpha = 1
                self.dragCellSnapshot?.removeFromSuperview()
                self.dragCellSnapshot = nil
                self.dragIndexPath = nil
            })

            // Update the playlists array to reflect the final snapshot order
            playlists = dataSource.snapshot().itemIdentifiers(inSection: .main)

        default:
            break
        }
    }
}
```

---

## 9. Section Header/Footer Views

Custom `UITableViewHeaderFooterView` with programmatic layout and nib registration.

```swift
import UIKit

// MARK: - Custom Section Header View (Programmatic)

class SectionHeaderView: UITableViewHeaderFooterView, ReusableView {

    private let titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = .systemFont(ofSize: 18, weight: .bold)
        label.textColor = .label
        return label
    }()

    private let countLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = .systemFont(ofSize: 14, weight: .medium)
        label.textColor = .secondaryLabel
        return label
    }()

    private let actionButton: UIButton = {
        let button = UIButton(type: .system)
        button.translatesAutoresizingMaskIntoConstraints = false
        button.setTitle("See All", for: .normal)
        button.titleLabel?.font = .systemFont(ofSize: 14, weight: .medium)
        return button
    }()

    var onActionTapped: (() -> Void)?

    override init(reuseIdentifier: String?) {
        super.init(reuseIdentifier: reuseIdentifier)
        setupViews()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        setupViews()
    }

    private func setupViews() {
        contentView.addSubview(titleLabel)
        contentView.addSubview(countLabel)
        contentView.addSubview(actionButton)

        actionButton.addTarget(self, action: #selector(actionTapped), for: .touchUpInside)

        NSLayoutConstraint.activate([
            titleLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            titleLabel.centerYAnchor.constraint(equalTo: contentView.centerYAnchor),

            countLabel.leadingAnchor.constraint(equalTo: titleLabel.trailingAnchor, constant: 8),
            countLabel.centerYAnchor.constraint(equalTo: titleLabel.centerYAnchor),

            actionButton.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            actionButton.centerYAnchor.constraint(equalTo: contentView.centerYAnchor),

            contentView.heightAnchor.constraint(greaterThanOrEqualToConstant: 44)
        ])
    }

    @objc private func actionTapped() {
        onActionTapped?()
    }

    func configure(title: String, count: Int) {
        titleLabel.text = title
        countLabel.text = "(\(count))"
    }
}

// MARK: - Custom Section Footer View (Programmatic)

class SectionFooterView: UITableViewHeaderFooterView, ReusableView {

    private let separatorView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        view.backgroundColor = .separator
        return view
    }()

    private let infoLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = .systemFont(ofSize: 12, weight: .regular)
        label.textColor = .tertiaryLabel
        label.numberOfLines = 0
        return label
    }()

    override init(reuseIdentifier: String?) {
        super.init(reuseIdentifier: reuseIdentifier)
        setupViews()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        setupViews()
    }

    private func setupViews() {
        contentView.addSubview(separatorView)
        contentView.addSubview(infoLabel)

        NSLayoutConstraint.activate([
            separatorView.topAnchor.constraint(equalTo: contentView.topAnchor),
            separatorView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            separatorView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            separatorView.heightAnchor.constraint(equalToConstant: 0.5),

            infoLabel.topAnchor.constraint(equalTo: separatorView.bottomAnchor, constant: 8),
            infoLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            infoLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),
            infoLabel.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -8)
        ])
    }

    func configure(text: String) {
        infoLabel.text = text
    }
}

// MARK: - Section Header View Loaded from Nib

class NibSectionHeaderView: UITableViewHeaderFooterView, ReusableView, NibLoadableView {

    // Connect these outlets in the .xib file
    // @IBOutlet private var iconImageView: UIImageView!
    // @IBOutlet private var titleLabel: UILabel!
    // @IBOutlet private var subtitleLabel: UILabel!

    // For this example, we set up programmatically but still register via nib pattern
    private let iconImageView: UIImageView = {
        let iv = UIImageView()
        iv.translatesAutoresizingMaskIntoConstraints = false
        iv.contentMode = .scaleAspectFit
        iv.tintColor = .systemBlue
        return iv
    }()

    private let titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = .systemFont(ofSize: 16, weight: .bold)
        return label
    }()

    private let subtitleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = .systemFont(ofSize: 12, weight: .regular)
        label.textColor = .secondaryLabel
        return label
    }()

    override init(reuseIdentifier: String?) {
        super.init(reuseIdentifier: reuseIdentifier)
        setupViews()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        setupViews()
    }

    private func setupViews() {
        contentView.addSubview(iconImageView)
        contentView.addSubview(titleLabel)
        contentView.addSubview(subtitleLabel)

        NSLayoutConstraint.activate([
            iconImageView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor, constant: 16),
            iconImageView.centerYAnchor.constraint(equalTo: contentView.centerYAnchor),
            iconImageView.widthAnchor.constraint(equalToConstant: 24),
            iconImageView.heightAnchor.constraint(equalToConstant: 24),

            titleLabel.leadingAnchor.constraint(equalTo: iconImageView.trailingAnchor, constant: 10),
            titleLabel.topAnchor.constraint(equalTo: contentView.topAnchor, constant: 8),
            titleLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor, constant: -16),

            subtitleLabel.leadingAnchor.constraint(equalTo: titleLabel.leadingAnchor),
            subtitleLabel.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 2),
            subtitleLabel.trailingAnchor.constraint(equalTo: titleLabel.trailingAnchor),
            subtitleLabel.bottomAnchor.constraint(equalTo: contentView.bottomAnchor, constant: -8)
        ])
    }

    func configure(icon: UIImage?, title: String, subtitle: String) {
        iconImageView.image = icon
        titleLabel.text = title
        subtitleLabel.text = subtitle
    }
}

// MARK: - ViewController Using Custom Header/Footer Views

class SectionHeaderFooterViewController: UIViewController {

    private let tableView: UITableView = {
        let tv = UITableView(frame: .zero, style: .grouped)
        tv.translatesAutoresizingMaskIntoConstraints = false
        return tv
    }()

    struct Section {
        let title: String
        let icon: UIImage?
        let subtitle: String
        let footerText: String
        let items: [String]
    }

    private let sections: [Section] = [
        Section(
            title: "General",
            icon: UIImage(systemName: "gear"),
            subtitle: "App preferences",
            footerText: "Changing these settings will affect all users on this device.",
            items: ["Appearance", "Language", "Notifications"]
        ),
        Section(
            title: "Privacy",
            icon: UIImage(systemName: "lock.shield"),
            subtitle: "Security settings",
            footerText: "Your data is encrypted end-to-end.",
            items: ["Passcode", "Face ID", "Two-Factor Auth"]
        ),
        Section(
            title: "Storage",
            icon: UIImage(systemName: "externaldrive"),
            subtitle: "Manage storage",
            footerText: "Clearing cache may require re-downloading some content.",
            items: ["Clear Cache", "Manage Downloads", "iCloud Sync"]
        )
    ]

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Settings"

        view.addSubview(tableView)
        NSLayoutConstraint.activate([
            tableView.topAnchor.constraint(equalTo: view.topAnchor),
            tableView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            tableView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            tableView.bottomAnchor.constraint(equalTo: view.bottomAnchor)
        ])

        tableView.register(UITableViewCell.self, forCellReuseIdentifier: "SettingCell")

        // Register custom header/footer views using the ReusableView protocol
        tableView.registerHeaderFooter(SectionHeaderView.self)
        tableView.registerHeaderFooter(SectionFooterView.self)

        tableView.dataSource = self
        tableView.delegate = self
    }
}

// MARK: - UITableViewDataSource
extension SectionHeaderFooterViewController: UITableViewDataSource {

    func numberOfSections(in tableView: UITableView) -> Int {
        return sections.count
    }

    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return sections[section].items.count
    }

    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: "SettingCell", for: indexPath)
        var content = cell.defaultContentConfiguration()
        content.text = sections[indexPath.section].items[indexPath.row]
        cell.contentConfiguration = content
        cell.accessoryType = .disclosureIndicator
        return cell
    }
}

// MARK: - UITableViewDelegate
extension SectionHeaderFooterViewController: UITableViewDelegate {

    func tableView(_ tableView: UITableView, viewForHeaderInSection section: Int) -> UIView? {
        let headerView: SectionHeaderView = tableView.dequeueReusableHeaderFooterView()
        let sectionData = sections[section]
        headerView.configure(title: sectionData.title, count: sectionData.items.count)
        headerView.onActionTapped = {
            print("See All tapped for section: \(sectionData.title)")
        }
        return headerView
    }

    func tableView(_ tableView: UITableView, viewForFooterInSection section: Int) -> UIView? {
        let footerView: SectionFooterView = tableView.dequeueReusableHeaderFooterView()
        footerView.configure(text: sections[section].footerText)
        return footerView
    }

    func tableView(_ tableView: UITableView, heightForHeaderInSection section: Int) -> CGFloat {
        return UITableView.automaticDimension
    }

    func tableView(_ tableView: UITableView, heightForFooterInSection section: Int) -> CGFloat {
        return UITableView.automaticDimension
    }

    func tableView(_ tableView: UITableView, estimatedHeightForHeaderInSection section: Int) -> CGFloat {
        return 44
    }

    func tableView(_ tableView: UITableView, estimatedHeightForFooterInSection section: Int) -> CGFloat {
        return 30
    }

    func tableView(_ tableView: UITableView, didSelectRowAt indexPath: IndexPath) {
        tableView.deselectRow(at: indexPath, animated: true)
        print("Selected: \(sections[indexPath.section].items[indexPath.row])")
    }
}
```
