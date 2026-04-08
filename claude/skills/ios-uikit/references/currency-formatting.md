# Currency Formatting

## Use Decimal, Not Double, for Money

`Double` has floating-point precision issues. `Decimal` provides exact decimal arithmetic.

```swift
let price: Decimal = 19.99
let tax: Decimal = 0.08
let total = price * (1 + tax) // exact: 21.5892

// Double would give: 21.589200000000002
```

## NumberFormatter with .currency Style

```swift
import Foundation

let formatter = NumberFormatter()
formatter.numberStyle = .currency
formatter.locale = Locale(identifier: "en_US")

let amount: Decimal = 1234.56
let formatted = formatter.string(from: amount as NSDecimalNumber)
// "$1,234.56"

// Other locales:
formatter.locale = Locale(identifier: "de_DE")
// "1.234,56 €"

formatter.locale = Locale(identifier: "ja_JP")
// "¥1,235" (no decimals for JPY)
```

## Dollar/Cent Split with Darwin modf()

Use `modf()` to split a dollar amount into the whole-dollar and cents portions for custom display.

```swift
import Darwin
import Foundation

func splitDollarsAndCents(from amount: Decimal) -> (dollars: String, cents: String) {
    let doubleValue = NSDecimalNumber(decimal: amount).doubleValue
    var integerPart: Double = 0
    let fractionalPart = modf(doubleValue, &integerPart)

    let dollars = String(format: "%.0f", integerPart)
    let cents = String(format: "%02d", Int(round(fractionalPart * 100)))

    return (dollars, cents)
}

let result = splitDollarsAndCents(from: 1234.50)
// result.dollars == "1234"
// result.cents == "50"
```

## NSAttributedString Display: Small Dollar Sign + Large Amount + Small Cents

A common banking UI pattern where the dollar sign and cents are smaller than the main amount.

```swift
import UIKit

func makeFormattedBalanceString(amount: Decimal) -> NSAttributedString {
    let parts = splitDollarsAndCents(from: amount)

    let dollarSignAttributes: [NSAttributedString.Key: Any] = [
        .font: UIFont.systemFont(ofSize: 18, weight: .regular),
        .baselineOffset: 14,
        .foregroundColor: UIColor.label,
    ]

    let dollarsAttributes: [NSAttributedString.Key: Any] = [
        .font: UIFont.systemFont(ofSize: 40, weight: .bold),
        .foregroundColor: UIColor.label,
    ]

    let centsAttributes: [NSAttributedString.Key: Any] = [
        .font: UIFont.systemFont(ofSize: 18, weight: .regular),
        .baselineOffset: 14,
        .foregroundColor: UIColor.secondaryLabel,
    ]

    let result = NSMutableAttributedString()
    result.append(NSAttributedString(string: "$", attributes: dollarSignAttributes))
    result.append(NSAttributedString(string: parts.dollars, attributes: dollarsAttributes))
    result.append(NSAttributedString(string: ".", attributes: centsAttributes))
    result.append(NSAttributedString(string: parts.cents, attributes: centsAttributes))

    return result
}
```

### Usage

```swift
class BalanceViewController: UIViewController {

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground

        let balanceLabel = UILabel()
        balanceLabel.translatesAutoresizingMaskIntoConstraints = false
        balanceLabel.attributedText = makeFormattedBalanceString(amount: 12345.67)
        view.addSubview(balanceLabel)

        NSLayoutConstraint.activate([
            balanceLabel.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            balanceLabel.centerYAnchor.constraint(equalTo: view.centerYAnchor),
        ])
    }
}
```

### Adding Comma Separators to the Dollar Portion

```swift
func splitDollarsAndCentsFormatted(from amount: Decimal) -> (dollars: String, cents: String) {
    let doubleValue = NSDecimalNumber(decimal: amount).doubleValue
    var integerPart: Double = 0
    let fractionalPart = modf(doubleValue, &integerPart)

    let numberFormatter = NumberFormatter()
    numberFormatter.numberStyle = .decimal
    numberFormatter.groupingSeparator = ","
    let dollars = numberFormatter.string(from: NSNumber(value: integerPart)) ?? "0"

    let cents = String(format: "%02d", Int(round(fractionalPart * 100)))

    return (dollars, cents)
}

// splitDollarsAndCentsFormatted(from: 1234567.89)
// dollars: "1,234,567", cents: "89"
```
