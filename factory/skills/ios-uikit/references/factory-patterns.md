# Factory Patterns

Factory functions create pre-configured UI components with `translatesAutoresizingMaskIntoConstraints = false` already set. They reduce boilerplate and enforce visual consistency across an app.

## UILabel Factory

```swift
import UIKit

func makeLabel(
    text: String = "",
    font: UIFont = .preferredFont(forTextStyle: .body),
    textColor: UIColor = .label,
    numberOfLines: Int = 0,
    textAlignment: NSTextAlignment = .natural
) -> UILabel {
    let label = UILabel()
    label.translatesAutoresizingMaskIntoConstraints = false
    label.text = text
    label.font = font
    label.textColor = textColor
    label.numberOfLines = numberOfLines
    label.textAlignment = textAlignment
    label.adjustsFontForContentSizeCategory = true
    return label
}
```

### Usage

```swift
let titleLabel = makeLabel(
    text: "Account Summary",
    font: .preferredFont(forTextStyle: .title1),
    textColor: .label
)

let subtitleLabel = makeLabel(
    text: "Last updated 5 min ago",
    font: .preferredFont(forTextStyle: .caption1),
    textColor: .secondaryLabel
)
```

## UIButton Factory

```swift
func makeButton(
    title: String,
    font: UIFont = .systemFont(ofSize: 16, weight: .semibold),
    titleColor: UIColor = .white,
    backgroundColor: UIColor = .systemBlue,
    cornerRadius: CGFloat = 8
) -> UIButton {
    let button = UIButton(type: .system)
    button.translatesAutoresizingMaskIntoConstraints = false
    button.setTitle(title, for: .normal)
    button.titleLabel?.font = font
    button.setTitleColor(titleColor, for: .normal)
    button.backgroundColor = backgroundColor
    button.layer.cornerRadius = cornerRadius
    button.contentEdgeInsets = UIEdgeInsets(top: 12, left: 24, bottom: 12, right: 24)
    return button
}
```

### Green Button Variant

```swift
func makeGreenButton(title: String) -> UIButton {
    let button = makeButton(
        title: title,
        titleColor: .white,
        backgroundColor: .systemGreen,
        cornerRadius: 12
    )
    return button
}
```

## UIStackView Factory

```swift
func makeStackView(
    axis: NSLayoutConstraint.Axis = .vertical,
    spacing: CGFloat = 8,
    distribution: UIStackView.Distribution = .fill,
    alignment: UIStackView.Alignment = .fill
) -> UIStackView {
    let stackView = UIStackView()
    stackView.translatesAutoresizingMaskIntoConstraints = false
    stackView.axis = axis
    stackView.spacing = spacing
    stackView.distribution = distribution
    stackView.alignment = alignment
    return stackView
}
```

### Usage

```swift
let headerStack = makeStackView(axis: .horizontal, spacing: 12, alignment: .center)
let formStack = makeStackView(axis: .vertical, spacing: 16)
```

## UIImageView Factory

### Basic Image View

```swift
func makeImageView(
    named imageName: String? = nil,
    contentMode: UIView.ContentMode = .scaleAspectFit,
    tintColor: UIColor? = nil
) -> UIImageView {
    let imageView = UIImageView()
    imageView.translatesAutoresizingMaskIntoConstraints = false
    imageView.contentMode = contentMode
    imageView.clipsToBounds = true

    if let name = imageName {
        imageView.image = UIImage(named: name)
    }

    if let tint = tintColor {
        imageView.tintColor = tint
    }

    return imageView
}
```

### Symbol Image View with Configuration

```swift
func makeSymbolImageView(
    systemName: String,
    pointSize: CGFloat = 24,
    weight: UIImage.SymbolWeight = .regular,
    scale: UIImage.SymbolScale = .medium,
    tintColor: UIColor = .label
) -> UIImageView {
    let config = UIImage.SymbolConfiguration(
        pointSize: pointSize,
        weight: weight,
        scale: scale
    )
    let image = UIImage(systemName: systemName, withConfiguration: config)

    let imageView = UIImageView(image: image)
    imageView.translatesAutoresizingMaskIntoConstraints = false
    imageView.tintColor = tintColor
    imageView.contentMode = .scaleAspectFit
    return imageView
}
```

### Usage

```swift
let avatar = makeImageView(named: "profile_placeholder", contentMode: .scaleAspectFill)
avatar.layer.cornerRadius = 25
avatar.clipsToBounds = true

let chevron = makeSymbolImageView(
    systemName: "chevron.right",
    pointSize: 14,
    weight: .semibold,
    tintColor: .tertiaryLabel
)

let starIcon = makeSymbolImageView(
    systemName: "star.fill",
    pointSize: 20,
    weight: .regular,
    scale: .large,
    tintColor: .systemYellow
)
```

## UITextField Factory

```swift
func makeTextField(
    placeholder: String,
    font: UIFont = .preferredFont(forTextStyle: .body),
    borderStyle: UITextField.BorderStyle = .roundedRect,
    keyboardType: UIKeyboardType = .default,
    isSecure: Bool = false
) -> UITextField {
    let textField = UITextField()
    textField.translatesAutoresizingMaskIntoConstraints = false
    textField.placeholder = placeholder
    textField.font = font
    textField.borderStyle = borderStyle
    textField.keyboardType = keyboardType
    textField.isSecureTextEntry = isSecure
    textField.autocorrectionType = .no
    return textField
}
```

### Usage

```swift
let emailField = makeTextField(
    placeholder: "Email",
    keyboardType: .emailAddress
)

let passwordField = makeTextField(
    placeholder: "Password",
    isSecure: true
)
```

## Symbol Button Factory

```swift
func makeSymbolButton(
    systemName: String,
    pointSize: CGFloat = 22,
    weight: UIImage.SymbolWeight = .regular,
    scale: UIImage.SymbolScale = .medium,
    tintColor: UIColor = .systemBlue,
    target: Any?,
    action: Selector
) -> UIButton {
    let config = UIImage.SymbolConfiguration(
        pointSize: pointSize,
        weight: weight,
        scale: scale
    )
    let image = UIImage(systemName: systemName, withConfiguration: config)

    let button = UIButton(type: .system)
    button.translatesAutoresizingMaskIntoConstraints = false
    button.setImage(image, for: .normal)
    button.tintColor = tintColor
    button.addTarget(target, action: action, for: .touchUpInside)
    return button
}
```

### Usage

```swift
let settingsButton = makeSymbolButton(
    systemName: "gearshape",
    pointSize: 24,
    weight: .medium,
    tintColor: .label,
    target: self,
    action: #selector(settingsTapped)
)
```

## Spotify-Style Button Factory

A themed button with an icon and rounded pill shape.

```swift
func makeSpotifyButton(
    title: String,
    systemName: String? = nil,
    backgroundColor: UIColor = UIColor(red: 0.12, green: 0.84, blue: 0.38, alpha: 1),
    foregroundColor: UIColor = .black
) -> UIButton {
    let button = UIButton(type: .system)
    button.translatesAutoresizingMaskIntoConstraints = false

    var config = UIButton.Configuration.filled()
    config.title = title
    config.baseForegroundColor = foregroundColor
    config.baseBackgroundColor = backgroundColor
    config.cornerStyle = .capsule
    config.contentInsets = NSDirectionalEdgeInsets(top: 12, leading: 24, bottom: 12, trailing: 24)

    if let systemName = systemName {
        let symbolConfig = UIImage.SymbolConfiguration(pointSize: 14, weight: .bold)
        config.image = UIImage(systemName: systemName, withConfiguration: symbolConfig)
        config.imagePlacement = .leading
        config.imagePadding = 8
    }

    button.configuration = config
    return button
}
```

### Usage

```swift
let shuffleButton = makeSpotifyButton(title: "Shuffle Play", systemName: "shuffle")
let followButton = makeSpotifyButton(
    title: "Follow",
    backgroundColor: .clear,
    foregroundColor: .white
)
followButton.layer.borderWidth = 1
followButton.layer.borderColor = UIColor.white.cgColor
followButton.layer.cornerRadius = 20
```

## When to Use Factories vs Lazy Properties

### Factories -- Use when:

- Creating multiple similar components (cells, form fields, list rows).
- The component is used in many different view controllers.
- You want a shared style across the app.

```swift
// Multiple labels with the same style
let nameLabel = makeLabel(font: .preferredFont(forTextStyle: .headline))
let emailLabel = makeLabel(font: .preferredFont(forTextStyle: .headline))
let phoneLabel = makeLabel(font: .preferredFont(forTextStyle: .headline))
```

### Lazy Properties -- Use when:

- The component is unique to this view controller.
- It needs to capture `self` for targets or delegates.
- You want deferred initialization (only created when first accessed).

```swift
class ProfileViewController: UIViewController {

    private lazy var saveButton: UIButton = {
        let button = UIButton(type: .system)
        button.translatesAutoresizingMaskIntoConstraints = false
        button.setTitle("Save", for: .normal)
        // Can reference self because lazy captures it
        button.addTarget(self, action: #selector(saveTapped), for: .touchUpInside)
        return button
    }()

    private lazy var tableView: UITableView = {
        let table = UITableView()
        table.translatesAutoresizingMaskIntoConstraints = false
        table.delegate = self
        table.dataSource = self
        return table
    }()

    @objc private func saveTapped() { }
}
```

### Combining Both

Use a factory for the base configuration, then customize with a lazy property.

```swift
class SettingsViewController: UIViewController {

    private lazy var headerLabel: UILabel = {
        let label = makeLabel(
            text: "Settings",
            font: .preferredFont(forTextStyle: .largeTitle)
        )
        // Additional customization specific to this screen
        label.accessibilityTraits = .header
        return label
    }()
}
```
