# Custom Controls

## UIControl Subclass Pattern: CreditCardControl

A `UIControl` subclass provides built-in target/action support (`.touchUpInside`, `.valueChanged`, etc.) and manages state like `isSelected` and `isHighlighted`.

```swift
import UIKit

class CreditCardControl: UIControl {

    // MARK: - State

    var isOn: Bool = false {
        didSet {
            updateAppearance()
            sendActions(for: .valueChanged)
        }
    }

    // MARK: - Views

    private let stackView = UIStackView()
    private let iconImageView = UIImageView()
    private let cardNumberLabel = UILabel()
    private let checkmarkImageView = UIImageView()

    // MARK: - Init

    override init(frame: CGRect) {
        super.init(frame: frame)
        setup()
    }

    required init?(coder: NSCoder) {
        super.init(coder: coder)
        setup()
    }

    // MARK: - Setup

    private func setup() {
        // Style the control itself
        layer.cornerRadius = 12
        layer.borderWidth = 2

        // Configure stack view
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .horizontal
        stackView.spacing = 12
        stackView.alignment = .center

        // IMPORTANT: Disable interaction on the stack view so touches
        // pass through to the UIControl for target/action to work.
        stackView.isUserInteractionEnabled = false

        addSubview(stackView)

        // Configure icon
        iconImageView.translatesAutoresizingMaskIntoConstraints = false
        iconImageView.contentMode = .scaleAspectFit
        iconImageView.image = UIImage(systemName: "creditcard")
        iconImageView.tintColor = .label

        // Configure card number label
        cardNumberLabel.translatesAutoresizingMaskIntoConstraints = false
        cardNumberLabel.font = .systemFont(ofSize: 16, weight: .medium)
        cardNumberLabel.text = "**** 4242"

        // Content hugging -- let the label stretch, keep others tight
        cardNumberLabel.setContentHuggingPriority(.defaultLow, for: .horizontal)
        iconImageView.setContentHuggingPriority(.required, for: .horizontal)
        checkmarkImageView.setContentHuggingPriority(.required, for: .horizontal)

        // Configure checkmark
        checkmarkImageView.translatesAutoresizingMaskIntoConstraints = false
        checkmarkImageView.contentMode = .scaleAspectFit
        let config = UIImage.SymbolConfiguration(pointSize: 18, weight: .bold)
        checkmarkImageView.image = UIImage(systemName: "checkmark.circle.fill", withConfiguration: config)

        // Assemble stack
        stackView.addArrangedSubview(iconImageView)
        stackView.addArrangedSubview(cardNumberLabel)
        stackView.addArrangedSubview(checkmarkImageView)

        // Layout
        NSLayoutConstraint.activate([
            stackView.topAnchor.constraint(equalTo: topAnchor, constant: 16),
            stackView.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 16),
            stackView.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -16),
            stackView.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -16),

            iconImageView.widthAnchor.constraint(equalToConstant: 32),
            iconImageView.heightAnchor.constraint(equalToConstant: 24),

            checkmarkImageView.widthAnchor.constraint(equalToConstant: 24),
            checkmarkImageView.heightAnchor.constraint(equalToConstant: 24),
        ])

        updateAppearance()
    }

    // MARK: - Appearance

    private func updateAppearance() {
        UIView.animate(withDuration: 0.2) {
            if self.isOn {
                self.layer.borderColor = UIColor.systemBlue.cgColor
                self.backgroundColor = UIColor.systemBlue.withAlphaComponent(0.08)
                self.cardNumberLabel.textColor = .systemBlue
                self.iconImageView.tintColor = .systemBlue
                self.checkmarkImageView.tintColor = .systemBlue
                self.checkmarkImageView.alpha = 1
            } else {
                self.layer.borderColor = UIColor.separator.cgColor
                self.backgroundColor = .secondarySystemBackground
                self.cardNumberLabel.textColor = .label
                self.iconImageView.tintColor = .label
                self.checkmarkImageView.alpha = 0
            }
        }
    }

    // MARK: - Touch Handling (built-in via UIControl)

    override var isHighlighted: Bool {
        didSet {
            UIView.animate(withDuration: 0.1) {
                self.alpha = self.isHighlighted ? 0.7 : 1.0
            }
        }
    }

    // MARK: - Configuration

    func configure(icon: String, cardNumber: String) {
        iconImageView.image = UIImage(systemName: icon)
        cardNumberLabel.text = cardNumber
    }
}
```

## Radio Button / Credit Card Selector Pattern

Only one control in the group can be selected at a time.

```swift
import UIKit

class CardSelectorViewController: UIViewController {

    private var cardControls: [CreditCardControl] = []
    private let stackView = UIStackView()

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        setupCards()
    }

    private func setupCards() {
        stackView.axis = .vertical
        stackView.spacing = 12
        stackView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(stackView)

        NSLayoutConstraint.activate([
            stackView.centerYAnchor.constraint(equalTo: view.centerYAnchor),
            stackView.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 24),
            stackView.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -24),
        ])

        let cardData: [(icon: String, number: String)] = [
            ("creditcard", "**** 4242"),
            ("creditcard.fill", "**** 8888"),
            ("giftcard", "**** 1234"),
        ]

        for data in cardData {
            let control = CreditCardControl()
            control.configure(icon: data.icon, cardNumber: data.number)

            // Use addTarget for .touchUpInside -- just like UIButton
            control.addTarget(self, action: #selector(cardTapped(_:)), for: .touchUpInside)

            stackView.addArrangedSubview(control)
            cardControls.append(control)
        }

        // Select the first card by default
        cardControls.first?.isOn = true
    }

    @objc private func cardTapped(_ sender: CreditCardControl) {
        // Radio button behavior -- deselect all, then select the tapped one
        for control in cardControls {
            control.isOn = false
        }
        sender.isOn = true
    }
}
```

## Content Hugging Priority for Layout

Content hugging controls how much a view resists being stretched beyond its intrinsic size. Higher priority means the view stays closer to its natural size.

```swift
// In a horizontal stack with [icon | label | chevron]:
// - icon and chevron should stay at their natural size
// - label should stretch to fill remaining space

iconImageView.setContentHuggingPriority(.required, for: .horizontal)      // 1000 -- never stretch
chevronImageView.setContentHuggingPriority(.required, for: .horizontal)   // 1000 -- never stretch
titleLabel.setContentHuggingPriority(.defaultLow, for: .horizontal)       // 250 -- stretch freely

// Content compression resistance controls how much a view resists being shrunk
titleLabel.setContentCompressionResistancePriority(.required, for: .vertical) // never truncate height
```

## UITextView Emoji Blocker

A UITextView delegate that rejects emoji input by validating each character against an allowed `CharacterSet`.

```swift
import UIKit

class NoteInputViewController: UIViewController, UITextViewDelegate {

    let textView = UITextView()
    let warningLabel = UILabel()

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground

        textView.translatesAutoresizingMaskIntoConstraints = false
        textView.font = .preferredFont(forTextStyle: .body)
        textView.layer.borderColor = UIColor.separator.cgColor
        textView.layer.borderWidth = 1
        textView.layer.cornerRadius = 8
        textView.delegate = self

        // Suggest ASCII keyboard -- but users can still switch keyboards
        textView.keyboardType = .asciiCapable

        warningLabel.translatesAutoresizingMaskIntoConstraints = false
        warningLabel.text = ""
        warningLabel.textColor = .systemRed
        warningLabel.font = .preferredFont(forTextStyle: .caption1)

        view.addSubview(textView)
        view.addSubview(warningLabel)

        NSLayoutConstraint.activate([
            textView.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 20),
            textView.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 16),
            textView.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -16),
            textView.heightAnchor.constraint(equalToConstant: 150),

            warningLabel.topAnchor.constraint(equalTo: textView.bottomAnchor, constant: 8),
            warningLabel.leadingAnchor.constraint(equalTo: textView.leadingAnchor),
        ])
    }

    // MARK: - UITextViewDelegate

    func textView(
        _ textView: UITextView,
        shouldChangeTextIn range: NSRange,
        replacementText text: String
    ) -> Bool {
        // Allow deletions (empty replacement)
        guard !text.isEmpty else { return true }

        // Allow newlines
        if text == "\n" { return true }

        // Check each character against the allowed set
        let allowedCharacters = CharacterSet.alphanumerics
            .union(.whitespaces)
            .union(.punctuationCharacters)

        for scalar in text.unicodeScalars {
            if !allowedCharacters.contains(scalar) {
                // Rejected -- show warning
                warningLabel.text = "Emoji and special characters are not allowed."
                shakeWarning()
                return false
            }
        }

        warningLabel.text = ""
        return true
    }

    private func shakeWarning() {
        let shake = CAKeyframeAnimation(keyPath: "transform.translation.x")
        shake.timingFunction = CAMediaTimingFunction(name: .easeOut)
        shake.values = [-6, 6, -4, 4, -2, 2, 0]
        shake.duration = 0.35
        warningLabel.layer.add(shake, forKey: "shake")
    }
}
```

### Alternative: Stricter Validation with Custom CharacterSet

```swift
extension CharacterSet {
    /// Only ASCII letters, digits, basic punctuation, and whitespace.
    static let asciiPrintable: CharacterSet = {
        var set = CharacterSet()
        set.insert(charactersIn: Unicode.Scalar(0x20)...Unicode.Scalar(0x7E)) // space through tilde
        set.insert(.newlines)
        return set
    }()
}

// Usage in shouldChangeTextIn:
let allowed = CharacterSet.asciiPrintable
for scalar in text.unicodeScalars {
    if !allowed.contains(scalar) {
        return false
    }
}
```
