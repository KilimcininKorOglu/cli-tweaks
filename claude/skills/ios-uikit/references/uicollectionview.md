# UICollectionView

## Compositional Layout Concepts

UICollectionViewCompositionalLayout builds layouts from four nested levels:

```
Layout
 └── Section (one per section index)
      └── Group (sizing + arrangement container)
           └── Item (leaf node = one cell)
```

- **NSCollectionLayoutItem** -- defines the size of a single cell.
- **NSCollectionLayoutGroup** -- arranges items horizontally, vertically, or in a custom layout. A group is itself an `NSCollectionLayoutItem`, so groups can nest.
- **NSCollectionLayoutSection** -- contains one group definition and optional supplementary/decoration items. Each section in the collection view maps to one `NSCollectionLayoutSection`.
- **UICollectionViewCompositionalLayout** -- the top-level layout object. Created with a single section or a section provider closure that returns a different section for each index.

```swift
// Minimal hierarchy
let itemSize = NSCollectionLayoutSize(
    widthDimension: .fractionalWidth(1.0),
    heightDimension: .absolute(44)
)
let item = NSCollectionLayoutItem(layoutSize: itemSize)

let groupSize = NSCollectionLayoutSize(
    widthDimension: .fractionalWidth(1.0),
    heightDimension: .absolute(44)
)
let group = NSCollectionLayoutGroup.horizontal(layoutSize: groupSize, subitems: [item])

let section = NSCollectionLayoutSection(group: group)

let layout = UICollectionViewCompositionalLayout(section: section)
```

### Size Dimensions

| Dimension                | Meaning                                           |
| ------------------------ | ------------------------------------------------- |
| `.fractionalWidth(0.5)`  | 50% of the container's width                      |
| `.fractionalHeight(1.0)` | 100% of the container's height                    |
| `.absolute(200)`         | Fixed 200pt                                       |
| `.estimated(100)`        | Start at 100pt, grow to fit content (self-sizing) |

---

## List Layout

A full-width vertical list where each row is 44pt tall.

```swift
final class ListViewController: UIViewController {

    enum Section { case main }

    struct Item: Hashable {
        let id = UUID()
        let title: String
    }

    private var collectionView: UICollectionView!
    private var dataSource: UICollectionViewDiffableDataSource<Section, Item>!

    override func viewDidLoad() {
        super.viewDidLoad()
        configureCollectionView()
        configureDataSource()
        applyInitialSnapshot()
    }

    private func configureCollectionView() {
        collectionView = UICollectionView(frame: .zero, collectionViewLayout: createLayout())
        collectionView.translatesAutoresizingMaskIntoConstraints = false
        collectionView.backgroundColor = .systemBackground
        view.addSubview(collectionView)

        NSLayoutConstraint.activate([
            collectionView.topAnchor.constraint(equalTo: view.topAnchor),
            collectionView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            collectionView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            collectionView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
        ])
    }

    private func createLayout() -> UICollectionViewLayout {
        let itemSize = NSCollectionLayoutSize(
            widthDimension: .fractionalWidth(1.0),
            heightDimension: .absolute(44)
        )
        let item = NSCollectionLayoutItem(layoutSize: itemSize)

        let groupSize = NSCollectionLayoutSize(
            widthDimension: .fractionalWidth(1.0),
            heightDimension: .absolute(44)
        )
        let group = NSCollectionLayoutGroup.vertical(layoutSize: groupSize, subitems: [item])

        let section = NSCollectionLayoutSection(group: group)
        section.interGroupSpacing = 1

        return UICollectionViewCompositionalLayout(section: section)
    }

    private func configureDataSource() {
        let cellRegistration = UICollectionView.CellRegistration<UICollectionViewListCell, Item> {
            cell, indexPath, item in
            var content = cell.defaultContentConfiguration()
            content.text = item.title
            cell.contentConfiguration = content
        }

        dataSource = UICollectionViewDiffableDataSource<Section, Item>(
            collectionView: collectionView
        ) { collectionView, indexPath, item in
            collectionView.dequeueConfiguredReusableCell(
                using: cellRegistration, for: indexPath, item: item
            )
        }
    }

    private func applyInitialSnapshot() {
        var snapshot = NSDiffableDataSourceSnapshot<Section, Item>()
        snapshot.appendSections([.main])
        snapshot.appendItems((1...20).map { Item(title: "Row \($0)") })
        dataSource.apply(snapshot, animatingDifferences: false)
    }
}
```

---

## Grid Layout

A 5-column grid where each item is a square with content insets for spacing.

```swift
private func createGridLayout() -> UICollectionViewLayout {
    let itemSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(0.2),
        heightDimension: .fractionalHeight(1.0)
    )
    let item = NSCollectionLayoutItem(layoutSize: itemSize)
    item.contentInsets = NSDirectionalEdgeInsets(top: 4, leading: 4, bottom: 4, trailing: 4)

    let groupSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(1.0),
        heightDimension: .fractionalWidth(0.2)
    )
    let group = NSCollectionLayoutGroup.horizontal(
        layoutSize: groupSize,
        subitems: [item]
    )

    let section = NSCollectionLayoutSection(group: group)
    section.contentInsets = NSDirectionalEdgeInsets(top: 8, leading: 8, bottom: 8, trailing: 8)

    return UICollectionViewCompositionalLayout(section: section)
}
```

The key idea: the item width is `.fractionalWidth(0.2)` (1/5 of the group), and the group height equals `.fractionalWidth(0.2)` so each cell is square. `contentInsets` on the item create inter-cell spacing without affecting the 5-column math.

---

## Two-Column Layout

Two equal-width columns using `subitems` with `count: 2` and `interItemSpacing`.

```swift
private func createTwoColumnLayout() -> UICollectionViewLayout {
    let itemSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(1.0),
        heightDimension: .fractionalHeight(1.0)
    )
    let item = NSCollectionLayoutItem(layoutSize: itemSize)

    let groupSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(1.0),
        heightDimension: .absolute(200)
    )
    let group = NSCollectionLayoutGroup.horizontal(
        layoutSize: groupSize,
        subitem: item,
        count: 2
    )
    group.interItemSpacing = .fixed(12)

    let section = NSCollectionLayoutSection(group: group)
    section.interGroupSpacing = 12
    section.contentInsets = NSDirectionalEdgeInsets(top: 16, leading: 16, bottom: 16, trailing: 16)

    return UICollectionViewCompositionalLayout(section: section)
}
```

When you pass `count: 2`, the layout distributes items evenly across the group width regardless of the item's `widthDimension`. The item width becomes `(groupWidth - interItemSpacing) / 2`.

---

## Badge Supplementary Item

A small badge pinned to the top-trailing corner of each cell.

```swift
private func createLayoutWithBadge() -> UICollectionViewLayout {
    // 1. Define the badge anchor and supplementary item
    let badgeAnchor = NSCollectionLayoutAnchor(
        edges: [.top, .trailing],
        fractionalOffset: CGPoint(x: 0.3, y: -0.3)
    )
    let badgeSize = NSCollectionLayoutSize(
        widthDimension: .absolute(20),
        heightDimension: .absolute(20)
    )
    let badgeItem = NSCollectionLayoutSupplementaryItem(
        layoutSize: badgeSize,
        elementKind: "badge",
        containerAnchor: badgeAnchor
    )

    // 2. Attach the badge to the item
    let itemSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(0.25),
        heightDimension: .fractionalHeight(1.0)
    )
    let item = NSCollectionLayoutItem(layoutSize: itemSize, supplementaryItems: [badgeItem])
    item.contentInsets = NSDirectionalEdgeInsets(top: 8, leading: 8, bottom: 8, trailing: 8)

    let groupSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(1.0),
        heightDimension: .fractionalWidth(0.25)
    )
    let group = NSCollectionLayoutGroup.horizontal(layoutSize: groupSize, subitems: [item])

    let section = NSCollectionLayoutSection(group: group)
    section.contentInsets = NSDirectionalEdgeInsets(top: 16, leading: 16, bottom: 16, trailing: 16)

    return UICollectionViewCompositionalLayout(section: section)
}
```

Register and provide the badge supplementary view:

```swift
// Registration
let badgeRegistration = UICollectionView.SupplementaryRegistration<BadgeView>(
    elementKind: "badge"
) { supplementaryView, elementKind, indexPath in
    supplementaryView.configure(count: 3)
}

dataSource.supplementaryViewProvider = { collectionView, kind, indexPath in
    collectionView.dequeueConfiguredReusableSupplementary(
        using: badgeRegistration, for: indexPath
    )
}
```

```swift
// Minimal badge view
final class BadgeView: UICollectionReusableView {

    private let label: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = .systemFont(ofSize: 11, weight: .bold)
        label.textColor = .white
        label.textAlignment = .center
        return label
    }()

    override init(frame: CGRect) {
        super.init(frame: frame)
        backgroundColor = .systemRed
        layer.cornerRadius = 10
        layer.masksToBounds = true
        addSubview(label)
        NSLayoutConstraint.activate([
            label.centerXAnchor.constraint(equalTo: centerXAnchor),
            label.centerYAnchor.constraint(equalTo: centerYAnchor),
        ])
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    func configure(count: Int) {
        label.text = "\(count)"
    }
}
```

---

## Header/Footer Boundary Items

Section headers and footers using `NSCollectionLayoutBoundarySupplementaryItem`.

```swift
private func createLayoutWithHeaderFooter() -> UICollectionViewLayout {
    let itemSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(1.0),
        heightDimension: .absolute(44)
    )
    let item = NSCollectionLayoutItem(layoutSize: itemSize)

    let groupSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(1.0),
        heightDimension: .absolute(44)
    )
    let group = NSCollectionLayoutGroup.vertical(layoutSize: groupSize, subitems: [item])

    let headerSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(1.0),
        heightDimension: .estimated(44)
    )
    let header = NSCollectionLayoutBoundarySupplementaryItem(
        layoutSize: headerSize,
        elementKind: UICollectionView.elementKindSectionHeader,
        alignment: .top
    )
    header.pinToVisibleBounds = true  // sticky header

    let footerSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(1.0),
        heightDimension: .estimated(44)
    )
    let footer = NSCollectionLayoutBoundarySupplementaryItem(
        layoutSize: footerSize,
        elementKind: UICollectionView.elementKindSectionFooter,
        alignment: .bottom
    )

    let section = NSCollectionLayoutSection(group: group)
    section.boundarySupplementaryItems = [header, footer]
    section.interGroupSpacing = 1

    return UICollectionViewCompositionalLayout(section: section)
}
```

Register and provide supplementary views through the data source:

```swift
let headerRegistration = UICollectionView.SupplementaryRegistration<HeaderView>(
    elementKind: UICollectionView.elementKindSectionHeader
) { supplementaryView, elementKind, indexPath in
    supplementaryView.titleLabel.text = "Section \(indexPath.section)"
}

let footerRegistration = UICollectionView.SupplementaryRegistration<FooterView>(
    elementKind: UICollectionView.elementKindSectionFooter
) { supplementaryView, elementKind, indexPath in
    supplementaryView.titleLabel.text = "\(itemCount) items"
}

dataSource.supplementaryViewProvider = { collectionView, kind, indexPath in
    switch kind {
    case UICollectionView.elementKindSectionHeader:
        return collectionView.dequeueConfiguredReusableSupplementary(
            using: headerRegistration, for: indexPath
        )
    case UICollectionView.elementKindSectionFooter:
        return collectionView.dequeueConfiguredReusableSupplementary(
            using: footerRegistration, for: indexPath
        )
    default:
        fatalError("Unexpected supplementary kind: \(kind)")
    }
}
```

```swift
final class HeaderView: UICollectionReusableView {

    let titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = .preferredFont(forTextStyle: .headline)
        return label
    }()

    override init(frame: CGRect) {
        super.init(frame: frame)
        backgroundColor = .secondarySystemBackground
        addSubview(titleLabel)
        NSLayoutConstraint.activate([
            titleLabel.topAnchor.constraint(equalTo: topAnchor, constant: 8),
            titleLabel.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            titleLabel.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),
            titleLabel.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -8),
        ])
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
}
```

Use `.estimated(44)` for the header/footer height so the layout measures the actual content size from Auto Layout constraints.

---

## Background Decoration

A background decoration view that sits behind all items in a section.

```swift
final class SectionBackgroundView: UICollectionReusableView {
    override init(frame: CGRect) {
        super.init(frame: frame)
        backgroundColor = .secondarySystemGroupedBackground
        layer.cornerRadius = 12
        layer.masksToBounds = true
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
}
```

```swift
private func createLayoutWithBackground() -> UICollectionViewLayout {
    let itemSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(1.0),
        heightDimension: .absolute(44)
    )
    let item = NSCollectionLayoutItem(layoutSize: itemSize)

    let groupSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(1.0),
        heightDimension: .absolute(44)
    )
    let group = NSCollectionLayoutGroup.vertical(layoutSize: groupSize, subitems: [item])

    let section = NSCollectionLayoutSection(group: group)
    section.contentInsets = NSDirectionalEdgeInsets(top: 12, leading: 16, bottom: 12, trailing: 16)
    section.interGroupSpacing = 1

    // Attach background decoration
    let backgroundDecoration = NSCollectionLayoutDecorationItem.background(
        elementKind: "section-background"
    )
    backgroundDecoration.contentInsets = NSDirectionalEdgeInsets(
        top: 4, leading: 8, bottom: 4, trailing: 8
    )
    section.decorationItems = [backgroundDecoration]

    let configuration = UICollectionViewCompositionalLayoutConfiguration()
    configuration.interSectionSpacing = 20

    let layout = UICollectionViewCompositionalLayout(section: section, configuration: configuration)

    // Register the decoration view on the layout, not on the collection view
    layout.register(
        SectionBackgroundView.self,
        forDecorationViewOfKind: "section-background"
    )

    return layout
}
```

Decoration items are registered on the **layout** object (not the collection view). They are not backed by a data source -- the layout creates and positions them automatically.

---

## Orthogonal Scrolling

Sections that scroll horizontally inside a vertically-scrolling collection view.

```swift
private func createOrthogonalLayout() -> UICollectionViewLayout {
    let layout = UICollectionViewCompositionalLayout { sectionIndex, environment in
        switch sectionIndex {
        case 0:
            return Self.createFeaturedSection()   // groupPagingCentered
        case 1:
            return Self.createCarouselSection()    // continuous
        default:
            return Self.createBannerSection()      // paging
        }
    }
    return layout
}

// Paging centered: snaps one group at a time, centered
private static func createFeaturedSection() -> NSCollectionLayoutSection {
    let itemSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(1.0),
        heightDimension: .fractionalHeight(1.0)
    )
    let item = NSCollectionLayoutItem(layoutSize: itemSize)
    item.contentInsets = NSDirectionalEdgeInsets(top: 0, leading: 8, bottom: 0, trailing: 8)

    let groupSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(0.85),
        heightDimension: .absolute(200)
    )
    let group = NSCollectionLayoutGroup.horizontal(layoutSize: groupSize, subitems: [item])

    let section = NSCollectionLayoutSection(group: group)
    section.orthogonalScrollingBehavior = .groupPagingCentered
    section.contentInsets = NSDirectionalEdgeInsets(top: 16, leading: 0, bottom: 16, trailing: 0)
    return section
}

// Continuous: free horizontal scroll, no snapping
private static func createCarouselSection() -> NSCollectionLayoutSection {
    let itemSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(1.0),
        heightDimension: .fractionalHeight(1.0)
    )
    let item = NSCollectionLayoutItem(layoutSize: itemSize)

    let groupSize = NSCollectionLayoutSize(
        widthDimension: .absolute(120),
        heightDimension: .absolute(120)
    )
    let group = NSCollectionLayoutGroup.horizontal(layoutSize: groupSize, subitems: [item])

    let section = NSCollectionLayoutSection(group: group)
    section.orthogonalScrollingBehavior = .continuous
    section.interGroupSpacing = 8
    section.contentInsets = NSDirectionalEdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16)
    return section
}

// Paging: snaps to full-width pages
private static func createBannerSection() -> NSCollectionLayoutSection {
    let itemSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(1.0),
        heightDimension: .fractionalHeight(1.0)
    )
    let item = NSCollectionLayoutItem(layoutSize: itemSize)

    let groupSize = NSCollectionLayoutSize(
        widthDimension: .fractionalWidth(1.0),
        heightDimension: .absolute(180)
    )
    let group = NSCollectionLayoutGroup.horizontal(layoutSize: groupSize, subitems: [item])

    let section = NSCollectionLayoutSection(group: group)
    section.orthogonalScrollingBehavior = .paging
    return section
}
```

### Orthogonal Scrolling Behaviors

| Behavior                          | Description                                      |
| --------------------------------- | ------------------------------------------------ |
| `.continuous`                     | Free-scrolling, no snapping                      |
| `.continuousGroupLeadingBoundary` | Snaps group leading edge to section leading edge |
| `.paging`                         | Full-width page snapping                         |
| `.groupPaging`                    | Snaps one group at a time to leading edge        |
| `.groupPagingCentered`            | Snaps one group at a time, centered              |
| `.none`                           | Default. No orthogonal scrolling.                |

---

## Diffable Data Source

### Setup with CellRegistration

```swift
final class SearchViewController: UIViewController {

    enum Section { case main }

    struct Contact: Hashable {
        let id: UUID
        let name: String
        let email: String
    }

    private var collectionView: UICollectionView!
    private var dataSource: UICollectionViewDiffableDataSource<Section, Contact>!
    private var allContacts: [Contact] = []

    override func viewDidLoad() {
        super.viewDidLoad()
        configureSearchBar()
        configureCollectionView()
        configureDataSource()
        loadContacts()
    }

    private func configureSearchBar() {
        let searchController = UISearchController(searchResultsController: nil)
        searchController.searchResultsUpdater = self
        searchController.obscuresBackgroundDuringPresentation = false
        searchController.searchBar.placeholder = "Search contacts"
        navigationItem.searchController = searchController
        definesPresentationContext = true
    }

    private func configureCollectionView() {
        var configuration = UICollectionLayoutListConfiguration(appearance: .plain)
        configuration.separatorConfiguration.bottomSeparatorInsets = .init(
            top: 0, leading: 60, bottom: 0, trailing: 0
        )
        let layout = UICollectionViewCompositionalLayout.list(using: configuration)

        collectionView = UICollectionView(frame: .zero, collectionViewLayout: layout)
        collectionView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(collectionView)

        NSLayoutConstraint.activate([
            collectionView.topAnchor.constraint(equalTo: view.topAnchor),
            collectionView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            collectionView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            collectionView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
        ])
    }

    private func configureDataSource() {
        let cellRegistration = UICollectionView.CellRegistration<UICollectionViewListCell, Contact> {
            cell, indexPath, contact in
            var content = cell.defaultContentConfiguration()
            content.text = contact.name
            content.secondaryText = contact.email
            content.image = UIImage(systemName: "person.circle.fill")
            content.imageProperties.tintColor = .systemBlue
            cell.contentConfiguration = content
        }

        dataSource = UICollectionViewDiffableDataSource<Section, Contact>(
            collectionView: collectionView
        ) { collectionView, indexPath, contact in
            collectionView.dequeueConfiguredReusableCell(
                using: cellRegistration, for: indexPath, item: contact
            )
        }
    }

    private func loadContacts() {
        allContacts = [
            Contact(id: UUID(), name: "Alice Johnson", email: "alice@example.com"),
            Contact(id: UUID(), name: "Bob Smith", email: "bob@example.com"),
            Contact(id: UUID(), name: "Charlie Brown", email: "charlie@example.com"),
        ]
        applySnapshot(with: allContacts)
    }

    private func applySnapshot(with contacts: [Contact], animate: Bool = true) {
        var snapshot = NSDiffableDataSourceSnapshot<Section, Contact>()
        snapshot.appendSections([.main])
        snapshot.appendItems(contacts)
        dataSource.apply(snapshot, animatingDifferences: animate)
    }
}

// MARK: - UISearchResultsUpdating

extension SearchViewController: UISearchResultsUpdating {
    func updateSearchResults(for searchController: UISearchController) {
        let query = searchController.searchBar.text ?? ""
        if query.isEmpty {
            applySnapshot(with: allContacts)
        } else {
            let filtered = allContacts.filter {
                $0.name.localizedCaseInsensitiveContains(query)
                || $0.email.localizedCaseInsensitiveContains(query)
            }
            applySnapshot(with: filtered)
        }
    }
}
```

### Multi-Section Diffable Data Source

```swift
enum Section: Int, CaseIterable {
    case featured
    case recent
    case all
}

struct Item: Hashable {
    let id: UUID
    let title: String
    let section: Section
}

// Build a snapshot with multiple sections
private func applyMultiSectionSnapshot() {
    var snapshot = NSDiffableDataSourceSnapshot<Section, Item>()
    snapshot.appendSections(Section.allCases)
    snapshot.appendItems(featuredItems, toSection: .featured)
    snapshot.appendItems(recentItems, toSection: .recent)
    snapshot.appendItems(allItems, toSection: .all)
    dataSource.apply(snapshot, animatingDifferences: true)
}
```

### Snapshot Operations

```swift
// Reload specific items (triggers cell reconfiguration)
var snapshot = dataSource.snapshot()
snapshot.reloadItems([updatedItem])
dataSource.apply(snapshot)

// Delete items
var snapshot = dataSource.snapshot()
snapshot.deleteItems([removedItem])
dataSource.apply(snapshot)

// Move item
var snapshot = dataSource.snapshot()
snapshot.moveItem(movedItem, afterItem: targetItem)
dataSource.apply(snapshot)

// Reconfigure (iOS 15+): updates cell content without replacing the cell
var snapshot = dataSource.snapshot()
snapshot.reconfigureItems([changedItem])
dataSource.apply(snapshot)
```

---

## Flow Layout

`UICollectionViewFlowLayout` is the pre-Compositional approach. Still useful for simple grids or when targeting older patterns.

```swift
final class FlowLayoutViewController: UIViewController {

    private let cellReuseID = "PhotoCell"
    private var collectionView: UICollectionView!
    private let photos: [String] = (1...50).map { "photo_\($0)" }

    override func viewDidLoad() {
        super.viewDidLoad()
        configureCollectionView()
    }

    private func configureCollectionView() {
        let layout = UICollectionViewFlowLayout()
        layout.scrollDirection = .vertical
        layout.minimumLineSpacing = 8
        layout.minimumInteritemSpacing = 8
        layout.sectionInset = UIEdgeInsets(top: 16, left: 16, bottom: 16, right: 16)

        // Optional: set header/footer size on the layout directly
        layout.headerReferenceSize = CGSize(width: 0, height: 44)
        layout.footerReferenceSize = CGSize(width: 0, height: 30)

        collectionView = UICollectionView(frame: .zero, collectionViewLayout: layout)
        collectionView.translatesAutoresizingMaskIntoConstraints = false
        collectionView.backgroundColor = .systemBackground
        collectionView.dataSource = self
        collectionView.delegate = self
        collectionView.register(PhotoCell.self, forCellWithReuseIdentifier: cellReuseID)
        collectionView.register(
            SectionHeaderView.self,
            forSupplementaryViewOfKind: UICollectionView.elementKindSectionHeader,
            withReuseIdentifier: "Header"
        )
        collectionView.register(
            SectionFooterView.self,
            forSupplementaryViewOfKind: UICollectionView.elementKindSectionFooter,
            withReuseIdentifier: "Footer"
        )

        view.addSubview(collectionView)
        NSLayoutConstraint.activate([
            collectionView.topAnchor.constraint(equalTo: view.topAnchor),
            collectionView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            collectionView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            collectionView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
        ])
    }
}

// MARK: - UICollectionViewDataSource

extension FlowLayoutViewController: UICollectionViewDataSource {
    func collectionView(_ collectionView: UICollectionView, numberOfItemsInSection section: Int) -> Int {
        photos.count
    }

    func collectionView(
        _ collectionView: UICollectionView,
        cellForItemAt indexPath: IndexPath
    ) -> UICollectionViewCell {
        let cell = collectionView.dequeueReusableCell(
            withReuseIdentifier: cellReuseID, for: indexPath
        ) as! PhotoCell
        cell.configure(with: photos[indexPath.item])
        return cell
    }

    func collectionView(
        _ collectionView: UICollectionView,
        viewForSupplementaryElementOfKind kind: String,
        at indexPath: IndexPath
    ) -> UICollectionReusableView {
        switch kind {
        case UICollectionView.elementKindSectionHeader:
            let header = collectionView.dequeueReusableSupplementary(
                ofKind: kind, withReuseIdentifier: "Header", for: indexPath
            ) as! SectionHeaderView
            header.titleLabel.text = "All Photos"
            return header
        case UICollectionView.elementKindSectionFooter:
            let footer = collectionView.dequeueReusableSupplementary(
                ofKind: kind, withReuseIdentifier: "Footer", for: indexPath
            ) as! SectionFooterView
            footer.titleLabel.text = "\(photos.count) photos"
            return footer
        default:
            fatalError("Unexpected supplementary kind: \(kind)")
        }
    }
}

// MARK: - UICollectionViewDelegateFlowLayout

extension FlowLayoutViewController: UICollectionViewDelegateFlowLayout {
    func collectionView(
        _ collectionView: UICollectionView,
        layout collectionViewLayout: UICollectionViewLayout,
        sizeForItemAt indexPath: IndexPath
    ) -> CGSize {
        let padding: CGFloat = 16 * 2 + 8 * 2  // sectionInset + interitemSpacing
        let availableWidth = collectionView.frame.width - padding
        let cellWidth = availableWidth / 3
        return CGSize(width: cellWidth, height: cellWidth)
    }

    func collectionView(
        _ collectionView: UICollectionView,
        layout collectionViewLayout: UICollectionViewLayout,
        minimumLineSpacingForSectionAt section: Int
    ) -> CGFloat {
        8
    }

    func collectionView(
        _ collectionView: UICollectionView,
        layout collectionViewLayout: UICollectionViewLayout,
        minimumInteritemSpacingForSectionAt section: Int
    ) -> CGFloat {
        8
    }

    func collectionView(
        _ collectionView: UICollectionView,
        layout collectionViewLayout: UICollectionViewLayout,
        insetForSectionAt section: Int
    ) -> UIEdgeInsets {
        UIEdgeInsets(top: 16, left: 16, bottom: 16, right: 16)
    }

    func collectionView(
        _ collectionView: UICollectionView,
        layout collectionViewLayout: UICollectionViewLayout,
        referenceSizeForHeaderInSection section: Int
    ) -> CGSize {
        CGSize(width: collectionView.frame.width, height: 44)
    }

    func collectionView(
        _ collectionView: UICollectionView,
        layout collectionViewLayout: UICollectionViewLayout,
        referenceSizeForFooterInSection section: Int
    ) -> CGSize {
        CGSize(width: collectionView.frame.width, height: 30)
    }
}
```

```swift
final class PhotoCell: UICollectionViewCell {

    private let imageView: UIImageView = {
        let iv = UIImageView()
        iv.translatesAutoresizingMaskIntoConstraints = false
        iv.contentMode = .scaleAspectFill
        iv.clipsToBounds = true
        iv.backgroundColor = .tertiarySystemFill
        iv.layer.cornerRadius = 8
        return iv
    }()

    override init(frame: CGRect) {
        super.init(frame: frame)
        contentView.addSubview(imageView)
        NSLayoutConstraint.activate([
            imageView.topAnchor.constraint(equalTo: contentView.topAnchor),
            imageView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            imageView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
            imageView.bottomAnchor.constraint(equalTo: contentView.bottomAnchor),
        ])
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    func configure(with imageName: String) {
        imageView.image = UIImage(named: imageName)
    }
}
```

---

## Nested Collection Views (Spotify Pattern)

A vertically-scrolling collection view where each section row is a cell containing its own horizontally-scrolling collection view. Common in media apps (Spotify, Netflix, App Store).

### Outer View Controller

```swift
final class NestedCollectionViewController: UIViewController {

    struct Category {
        let title: String
        let items: [String]
    }

    private var collectionView: UICollectionView!
    private let categories: [Category] = [
        Category(title: "Recently Played", items: (1...15).map { "Track \($0)" }),
        Category(title: "Made for You", items: (1...10).map { "Playlist \($0)" }),
        Category(title: "Popular Albums", items: (1...20).map { "Album \($0)" }),
        Category(title: "New Releases", items: (1...12).map { "Release \($0)" }),
    ]

    override func viewDidLoad() {
        super.viewDidLoad()
        title = "Browse"
        view.backgroundColor = .systemBackground
        configureCollectionView()
    }

    private func configureCollectionView() {
        let layout = UICollectionViewFlowLayout()
        layout.scrollDirection = .vertical
        layout.minimumLineSpacing = 0

        collectionView = UICollectionView(frame: .zero, collectionViewLayout: layout)
        collectionView.translatesAutoresizingMaskIntoConstraints = false
        collectionView.backgroundColor = .systemBackground
        collectionView.dataSource = self
        collectionView.delegate = self
        collectionView.register(
            CategoryCell.self,
            forCellWithReuseIdentifier: CategoryCell.reuseID
        )
        collectionView.register(
            CategoryHeaderView.self,
            forSupplementaryViewOfKind: UICollectionView.elementKindSectionHeader,
            withReuseIdentifier: CategoryHeaderView.reuseID
        )

        view.addSubview(collectionView)
        NSLayoutConstraint.activate([
            collectionView.topAnchor.constraint(equalTo: view.topAnchor),
            collectionView.leadingAnchor.constraint(equalTo: view.leadingAnchor),
            collectionView.trailingAnchor.constraint(equalTo: view.trailingAnchor),
            collectionView.bottomAnchor.constraint(equalTo: view.bottomAnchor),
        ])
    }
}

// MARK: - UICollectionViewDataSource

extension NestedCollectionViewController: UICollectionViewDataSource {
    func numberOfSections(in collectionView: UICollectionView) -> Int {
        categories.count
    }

    func collectionView(
        _ collectionView: UICollectionView,
        numberOfItemsInSection section: Int
    ) -> Int {
        1  // one cell per section; the cell itself holds the horizontal collection
    }

    func collectionView(
        _ collectionView: UICollectionView,
        cellForItemAt indexPath: IndexPath
    ) -> UICollectionViewCell {
        let cell = collectionView.dequeueReusableCell(
            withReuseIdentifier: CategoryCell.reuseID, for: indexPath
        ) as! CategoryCell
        cell.configure(with: categories[indexPath.section].items)
        return cell
    }

    func collectionView(
        _ collectionView: UICollectionView,
        viewForSupplementaryElementOfKind kind: String,
        at indexPath: IndexPath
    ) -> UICollectionReusableView {
        let header = collectionView.dequeueReusableSupplementary(
            ofKind: kind,
            withReuseIdentifier: CategoryHeaderView.reuseID,
            for: indexPath
        ) as! CategoryHeaderView
        header.titleLabel.text = categories[indexPath.section].title
        return header
    }
}

// MARK: - UICollectionViewDelegateFlowLayout

extension NestedCollectionViewController: UICollectionViewDelegateFlowLayout {
    func collectionView(
        _ collectionView: UICollectionView,
        layout collectionViewLayout: UICollectionViewLayout,
        sizeForItemAt indexPath: IndexPath
    ) -> CGSize {
        CGSize(width: collectionView.frame.width, height: 160)
    }

    func collectionView(
        _ collectionView: UICollectionView,
        layout collectionViewLayout: UICollectionViewLayout,
        referenceSizeForHeaderInSection section: Int
    ) -> CGSize {
        CGSize(width: collectionView.frame.width, height: 44)
    }

    func collectionView(
        _ collectionView: UICollectionView,
        layout collectionViewLayout: UICollectionViewLayout,
        insetForSectionAt section: Int
    ) -> UIEdgeInsets {
        UIEdgeInsets(top: 0, left: 0, bottom: 16, right: 0)
    }
}
```

### Category Cell (contains the inner horizontal collection view)

```swift
final class CategoryCell: UICollectionViewCell {

    static let reuseID = "CategoryCell"

    private var items: [String] = []
    private var innerCollectionView: UICollectionView!

    override init(frame: CGRect) {
        super.init(frame: frame)

        let layout = UICollectionViewFlowLayout()
        layout.scrollDirection = .horizontal
        layout.itemSize = CGSize(width: 130, height: 140)
        layout.minimumLineSpacing = 12
        layout.sectionInset = UIEdgeInsets(top: 0, left: 16, bottom: 0, right: 16)

        innerCollectionView = UICollectionView(frame: .zero, collectionViewLayout: layout)
        innerCollectionView.translatesAutoresizingMaskIntoConstraints = false
        innerCollectionView.backgroundColor = .clear
        innerCollectionView.showsHorizontalScrollIndicator = false
        innerCollectionView.dataSource = self
        innerCollectionView.delegate = self
        innerCollectionView.register(
            InnerItemCell.self,
            forCellWithReuseIdentifier: InnerItemCell.reuseID
        )

        contentView.addSubview(innerCollectionView)
        NSLayoutConstraint.activate([
            innerCollectionView.topAnchor.constraint(equalTo: contentView.topAnchor),
            innerCollectionView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            innerCollectionView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
            innerCollectionView.bottomAnchor.constraint(equalTo: contentView.bottomAnchor),
        ])
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    func configure(with items: [String]) {
        self.items = items
        innerCollectionView.reloadData()
        innerCollectionView.setContentOffset(.zero, animated: false)
    }
}

// MARK: - Inner Collection Data Source & Delegate

extension CategoryCell: UICollectionViewDataSource, UICollectionViewDelegate {
    func collectionView(
        _ collectionView: UICollectionView,
        numberOfItemsInSection section: Int
    ) -> Int {
        items.count
    }

    func collectionView(
        _ collectionView: UICollectionView,
        cellForItemAt indexPath: IndexPath
    ) -> UICollectionViewCell {
        let cell = collectionView.dequeueReusableCell(
            withReuseIdentifier: InnerItemCell.reuseID, for: indexPath
        ) as! InnerItemCell
        cell.configure(with: items[indexPath.item])
        return cell
    }

    func collectionView(
        _ collectionView: UICollectionView,
        didSelectItemAt indexPath: IndexPath
    ) {
        // Forward selection to the outer view controller via delegate or closure
        print("Selected: \(items[indexPath.item])")
    }
}
```

### Inner Item Cell

```swift
final class InnerItemCell: UICollectionViewCell {

    static let reuseID = "InnerItemCell"

    private let imageView: UIImageView = {
        let iv = UIImageView()
        iv.translatesAutoresizingMaskIntoConstraints = false
        iv.contentMode = .scaleAspectFill
        iv.clipsToBounds = true
        iv.backgroundColor = .tertiarySystemFill
        iv.layer.cornerRadius = 8
        return iv
    }()

    private let titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = .systemFont(ofSize: 13, weight: .medium)
        label.textColor = .label
        label.numberOfLines = 2
        return label
    }()

    override init(frame: CGRect) {
        super.init(frame: frame)
        contentView.addSubview(imageView)
        contentView.addSubview(titleLabel)

        NSLayoutConstraint.activate([
            imageView.topAnchor.constraint(equalTo: contentView.topAnchor),
            imageView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            imageView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
            imageView.heightAnchor.constraint(equalTo: imageView.widthAnchor),

            titleLabel.topAnchor.constraint(equalTo: imageView.bottomAnchor, constant: 4),
            titleLabel.leadingAnchor.constraint(equalTo: contentView.leadingAnchor),
            titleLabel.trailingAnchor.constraint(equalTo: contentView.trailingAnchor),
        ])
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    func configure(with title: String) {
        titleLabel.text = title
        imageView.image = UIImage(systemName: "music.note")
    }
}
```

### Category Header View

```swift
final class CategoryHeaderView: UICollectionReusableView {

    static let reuseID = "CategoryHeaderView"

    let titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = .systemFont(ofSize: 20, weight: .bold)
        label.textColor = .label
        return label
    }()

    override init(frame: CGRect) {
        super.init(frame: frame)
        addSubview(titleLabel)
        NSLayoutConstraint.activate([
            titleLabel.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            titleLabel.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),
            titleLabel.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -4),
        ])
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
}
```

### Modern Alternative: Orthogonal Scrolling Sections

The nested collection view pattern predates Compositional Layout. For new code, prefer orthogonal scrolling sections (see the Orthogonal Scrolling section above) which achieve the same visual result with a single collection view and data source, avoiding the complexity of nested delegates and scroll offset management during cell reuse.
