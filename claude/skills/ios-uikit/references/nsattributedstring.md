# NSAttributedString

## NSMutableParagraphStyle

Control line spacing, indentation, and alignment.

```swift
import UIKit

func makeStyledParagraph(text: String) -> NSAttributedString {
    let paragraphStyle = NSMutableParagraphStyle()
    paragraphStyle.lineSpacing = 6
    paragraphStyle.firstLineHeadIndent = 20
    paragraphStyle.headIndent = 0
    paragraphStyle.alignment = .justified
    paragraphStyle.lineBreakMode = .byWordWrapping
    paragraphStyle.paragraphSpacingBefore = 12

    let attributes: [NSAttributedString.Key: Any] = [
        .font: UIFont.preferredFont(forTextStyle: .body),
        .foregroundColor: UIColor.label,
        .paragraphStyle: paragraphStyle,
    ]

    return NSAttributedString(string: text, attributes: attributes)
}
```

### Usage

```swift
let label = UILabel()
label.numberOfLines = 0
label.attributedText = makeStyledParagraph(
    text: "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
        + "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua."
)
```

## Font Traits: Bold via withTraits

Add bold, italic, or other symbolic traits to an existing font.

```swift
import UIKit

extension UIFont {
    func withTraits(_ traits: UIFontDescriptor.SymbolicTraits) -> UIFont {
        guard let descriptor = fontDescriptor.withSymbolicTraits(traits) else {
            return self
        }
        return UIFont(descriptor: descriptor, size: 0) // size 0 preserves original size
    }

    var bold: UIFont {
        return withTraits(.traitBold)
    }

    var italic: UIFont {
        return withTraits(.traitItalic)
    }

    var boldItalic: UIFont {
        return withTraits([.traitBold, .traitItalic])
    }
}
```

### Usage in Attributed Strings

```swift
func makeBoldSubstring(fullText: String, boldPart: String) -> NSAttributedString {
    let baseFont = UIFont.preferredFont(forTextStyle: .body)

    let attributed = NSMutableAttributedString(
        string: fullText,
        attributes: [.font: baseFont]
    )

    if let range = fullText.range(of: boldPart) {
        let nsRange = NSRange(range, in: fullText)
        attributed.addAttribute(.font, value: baseFont.bold, range: nsRange)
    }

    return attributed
}

// "Welcome back, Jonathan!" with "Jonathan" in bold
let text = makeBoldSubstring(fullText: "Welcome back, Jonathan!", boldPart: "Jonathan")
```

## Kerning and Baseline Offset

```swift
func makeKernedText(text: String, kern: CGFloat) -> NSAttributedString {
    let attributes: [NSAttributedString.Key: Any] = [
        .font: UIFont.systemFont(ofSize: 24, weight: .light),
        .kern: kern, // spacing between characters (points)
        .foregroundColor: UIColor.label,
    ]
    return NSAttributedString(string: text, attributes: attributes)
}

// Wide letter spacing
let spacedTitle = makeKernedText(text: "WELCOME", kern: 8.0)

// Tight letter spacing
let tightTitle = makeKernedText(text: "WELCOME", kern: -0.5)
```

### Baseline Offset

Shift text up or down relative to the baseline. Positive moves up, negative moves down.

```swift
func makeSuperscript(base: String, superscript sup: String) -> NSAttributedString {
    let result = NSMutableAttributedString()

    let baseAttributes: [NSAttributedString.Key: Any] = [
        .font: UIFont.systemFont(ofSize: 24, weight: .medium),
    ]

    let superAttributes: [NSAttributedString.Key: Any] = [
        .font: UIFont.systemFont(ofSize: 14, weight: .medium),
        .baselineOffset: 10, // shift up
        .foregroundColor: UIColor.secondaryLabel,
    ]

    result.append(NSAttributedString(string: base, attributes: baseAttributes))
    result.append(NSAttributedString(string: sup, attributes: superAttributes))
    return result
}

// "42nd" with "nd" raised
let ordinal = makeSuperscript(base: "42", superscript: "nd")
```

## Embed Images via NSTextAttachment

Insert inline images into attributed text.

```swift
import UIKit

func makeTextWithIcon(
    text: String,
    systemName: String,
    tintColor: UIColor = .systemBlue,
    font: UIFont = .preferredFont(forTextStyle: .body)
) -> NSAttributedString {
    let result = NSMutableAttributedString()

    // Create the image attachment
    let attachment = NSTextAttachment()
    let config = UIImage.SymbolConfiguration(font: font)
    attachment.image = UIImage(systemName: systemName, withConfiguration: config)?
        .withTintColor(tintColor, renderingMode: .alwaysOriginal)

    // Vertically center the image with the text
    let imageHeight = font.capHeight
    attachment.bounds = CGRect(
        x: 0,
        y: (font.capHeight - imageHeight) / 2,
        width: imageHeight,
        height: imageHeight
    )

    let imageString = NSAttributedString(attachment: attachment)
    result.append(imageString)
    result.append(NSAttributedString(string: " ")) // space after icon

    let textAttributes: [NSAttributedString.Key: Any] = [
        .font: font,
        .foregroundColor: UIColor.label,
    ]
    result.append(NSAttributedString(string: text, attributes: textAttributes))

    return result
}
```

### Usage

```swift
let label = UILabel()
label.attributedText = makeTextWithIcon(
    text: "Verified Account",
    systemName: "checkmark.seal.fill",
    tintColor: .systemGreen
)
```

### Multiple Inline Icons

```swift
func makeRatingText(rating: Int, maxRating: Int = 5) -> NSAttributedString {
    let result = NSMutableAttributedString()
    let font = UIFont.systemFont(ofSize: 18)

    for i in 1...maxRating {
        let attachment = NSTextAttachment()
        let systemName = i <= rating ? "star.fill" : "star"
        let color: UIColor = i <= rating ? .systemYellow : .tertiaryLabel
        let config = UIImage.SymbolConfiguration(font: font)
        attachment.image = UIImage(systemName: systemName, withConfiguration: config)?
            .withTintColor(color, renderingMode: .alwaysOriginal)

        let height = font.capHeight
        attachment.bounds = CGRect(x: 0, y: (font.capHeight - height) / 2, width: height, height: height)

        result.append(NSAttributedString(attachment: attachment))
        result.append(NSAttributedString(string: " "))
    }

    return result
}

// Five stars, 3 filled
let stars = makeRatingText(rating: 3)
```

## Building Complex Text with Append

Combine multiple styled segments into a single attributed string.

```swift
func makeTransactionDetailText(
    merchant: String,
    amount: String,
    date: String,
    category: String
) -> NSAttributedString {
    let result = NSMutableAttributedString()

    // Merchant name -- bold, large
    let merchantAttrs: [NSAttributedString.Key: Any] = [
        .font: UIFont.systemFont(ofSize: 20, weight: .bold),
        .foregroundColor: UIColor.label,
    ]
    result.append(NSAttributedString(string: merchant, attributes: merchantAttrs))
    result.append(NSAttributedString(string: "\n"))

    // Amount -- colored based on sign
    let isCredit = amount.hasPrefix("+")
    let amountAttrs: [NSAttributedString.Key: Any] = [
        .font: UIFont.systemFont(ofSize: 28, weight: .heavy),
        .foregroundColor: isCredit ? UIColor.systemGreen : UIColor.label,
    ]
    result.append(NSAttributedString(string: amount, attributes: amountAttrs))
    result.append(NSAttributedString(string: "\n\n"))

    // Date -- secondary
    let dateAttrs: [NSAttributedString.Key: Any] = [
        .font: UIFont.preferredFont(forTextStyle: .subheadline),
        .foregroundColor: UIColor.secondaryLabel,
    ]
    result.append(NSAttributedString(string: date, attributes: dateAttrs))
    result.append(NSAttributedString(string: "  "))

    // Category -- pill-like with background
    let categoryAttrs: [NSAttributedString.Key: Any] = [
        .font: UIFont.systemFont(ofSize: 13, weight: .semibold),
        .foregroundColor: UIColor.systemBlue,
        .backgroundColor: UIColor.systemBlue.withAlphaComponent(0.12),
    ]
    result.append(NSAttributedString(string: " \(category) ", attributes: categoryAttrs))

    return result
}
```

### Usage

```swift
let label = UILabel()
label.numberOfLines = 0
label.attributedText = makeTransactionDetailText(
    merchant: "Apple Store",
    amount: "-$999.00",
    date: "January 15, 2025",
    category: "Electronics"
)
```

## boundingRect for Sizing

Calculate how much space an attributed string needs to render at a given width. Useful for dynamic cell heights or manual layout.

```swift
import UIKit

func heightForAttributedString(
    _ attributedString: NSAttributedString,
    constrainedToWidth width: CGFloat
) -> CGFloat {
    let boundingRect = attributedString.boundingRect(
        with: CGSize(width: width, height: .greatestFiniteMagnitude),
        options: [.usesLineFragmentOrigin, .usesFontLeading],
        context: nil
    )
    return ceil(boundingRect.height)
}
```

### Usage in a Table View

```swift
func tableView(_ tableView: UITableView, heightForRowAt indexPath: IndexPath) -> CGFloat {
    let text = makeTransactionDetailText(
        merchant: "Apple Store",
        amount: "-$999.00",
        date: "January 15, 2025",
        category: "Electronics"
    )

    let labelWidth = tableView.bounds.width - 32 // 16pt padding each side
    let textHeight = heightForAttributedString(text, constrainedToWidth: labelWidth)

    return textHeight + 24 // add vertical padding
}
```

### Sizing for a Custom View

```swift
class DynamicBadgeView: UIView {

    private let label = UILabel()
    private let padding: CGFloat = 12

    var attributedText: NSAttributedString? {
        didSet {
            label.attributedText = attributedText
            invalidateIntrinsicContentSize()
        }
    }

    override init(frame: CGRect) {
        super.init(frame: frame)
        label.numberOfLines = 0
        label.translatesAutoresizingMaskIntoConstraints = false
        addSubview(label)
        NSLayoutConstraint.activate([
            label.topAnchor.constraint(equalTo: topAnchor, constant: padding),
            label.leadingAnchor.constraint(equalTo: leadingAnchor, constant: padding),
            label.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -padding),
            label.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -padding),
        ])
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    override var intrinsicContentSize: CGSize {
        guard let text = attributedText else { return .zero }
        let maxWidth: CGFloat = 280 - (padding * 2)
        let height = heightForAttributedString(text, constrainedToWidth: maxWidth)
        return CGSize(width: 280, height: height + (padding * 2))
    }
}
```
