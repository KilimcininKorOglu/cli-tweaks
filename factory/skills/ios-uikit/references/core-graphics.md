# Core Graphics

## Two Drawing Approaches

### 1. Override `draw(_:)` in a UIView subclass

Called automatically by UIKit when the view needs to be rendered. Use `setNeedsDisplay()` to trigger a redraw.

```swift
import UIKit

class CustomDrawView: UIView {

    override func draw(_ rect: CGRect) {
        guard let context = UIGraphicsGetCurrentContext() else { return }

        context.setStrokeColor(UIColor.systemBlue.cgColor)
        context.setLineWidth(2)
        context.move(to: CGPoint(x: 0, y: 0))
        context.addLine(to: CGPoint(x: rect.width, y: rect.height))
        context.strokePath()
    }
}
```

### 2. UIGraphicsImageRenderer

Creates an image off-screen. Useful for generating icons, thumbnails, or any image you want to use elsewhere.

```swift
import UIKit

func makeCheckmarkImage(size: CGSize = CGSize(width: 30, height: 30)) -> UIImage {
    let renderer = UIGraphicsImageRenderer(size: size)
    return renderer.image { context in
        let path = UIBezierPath()
        path.move(to: CGPoint(x: 5, y: size.height / 2))
        path.addLine(to: CGPoint(x: size.width / 3, y: size.height - 5))
        path.addLine(to: CGPoint(x: size.width - 5, y: 5))

        UIColor.systemGreen.setStroke()
        path.lineWidth = 3
        path.lineCapStyle = .round
        path.lineJoinStyle = .round
        path.stroke()
    }
}
```

## Coordinate System

UIKit uses an upper-left origin with Y increasing downward.

```
(0, 0) -----> X
|
|
v
Y
```

This is the opposite of standard math coordinates. Core Graphics contexts obtained via `UIGraphicsGetCurrentContext()` in `draw(_:)` already have this transform applied.

## Primitives

### Points and Lines

```swift
override func draw(_ rect: CGRect) {
    guard let context = UIGraphicsGetCurrentContext() else { return }

    context.setStrokeColor(UIColor.label.cgColor)
    context.setLineWidth(2)

    // Single line
    context.move(to: CGPoint(x: 10, y: 10))
    context.addLine(to: CGPoint(x: 200, y: 10))
    context.strokePath()

    // Connected line segments
    context.move(to: CGPoint(x: 10, y: 40))
    context.addLine(to: CGPoint(x: 100, y: 80))
    context.addLine(to: CGPoint(x: 200, y: 40))
    context.strokePath()
}
```

### Arcs

```swift
override func draw(_ rect: CGRect) {
    guard let context = UIGraphicsGetCurrentContext() else { return }

    let center = CGPoint(x: rect.midX, y: rect.midY)
    let radius: CGFloat = 60

    // Full circle
    context.addArc(
        center: center,
        radius: radius,
        startAngle: 0,
        endAngle: .pi * 2,
        clockwise: false
    )
    context.setStrokeColor(UIColor.systemBlue.cgColor)
    context.setLineWidth(3)
    context.strokePath()

    // Partial arc (quarter circle)
    context.addArc(
        center: center,
        radius: radius + 20,
        startAngle: -.pi / 2,
        endAngle: 0,
        clockwise: false
    )
    context.setStrokeColor(UIColor.systemRed.cgColor)
    context.strokePath()
}
```

### Curves (Quadratic and Cubic Bezier)

```swift
override func draw(_ rect: CGRect) {
    let path = UIBezierPath()

    // Quadratic curve
    path.move(to: CGPoint(x: 20, y: 100))
    path.addQuadCurve(
        to: CGPoint(x: 200, y: 100),
        controlPoint: CGPoint(x: 110, y: 20)
    )

    // Cubic Bezier curve
    path.move(to: CGPoint(x: 20, y: 200))
    path.addCurve(
        to: CGPoint(x: 200, y: 200),
        controlPoint1: CGPoint(x: 70, y: 130),
        controlPoint2: CGPoint(x: 150, y: 270)
    )

    UIColor.systemPurple.setStroke()
    path.lineWidth = 2
    path.stroke()
}
```

### Ellipses and Rectangles

```swift
override func draw(_ rect: CGRect) {
    // Filled rectangle
    let rectPath = UIBezierPath(rect: CGRect(x: 20, y: 20, width: 100, height: 60))
    UIColor.systemYellow.setFill()
    rectPath.fill()

    // Rounded rectangle
    let roundedRect = UIBezierPath(
        roundedRect: CGRect(x: 140, y: 20, width: 100, height: 60),
        cornerRadius: 12
    )
    UIColor.systemBlue.setStroke()
    roundedRect.lineWidth = 2
    roundedRect.stroke()

    // Ellipse
    let ellipsePath = UIBezierPath(ovalIn: CGRect(x: 20, y: 100, width: 150, height: 80))
    UIColor.systemGreen.setFill()
    UIColor.systemGreen.withAlphaComponent(0.3).setFill()
    ellipsePath.fill()
    UIColor.systemGreen.setStroke()
    ellipsePath.lineWidth = 2
    ellipsePath.stroke()
}
```

## Stroke Width Straddling

A stroke straddles the path -- half inside, half outside. A 4pt stroke on a rectangle edge means 2pt inside and 2pt outside the boundary.

```swift
override func draw(_ rect: CGRect) {
    let lineWidth: CGFloat = 10

    // Inset so the stroke does not get clipped at the view edge
    let insetRect = rect.insetBy(dx: lineWidth / 2, dy: lineWidth / 2)

    let path = UIBezierPath(rect: insetRect)
    path.lineWidth = lineWidth
    UIColor.systemRed.setStroke()
    path.stroke()
}
```

## Painter's Model (Draw Order)

Later draws paint over earlier draws, like a painter layering paint on canvas. The last thing drawn is on top.

```swift
override func draw(_ rect: CGRect) {
    // Layer 1 -- drawn first, appears behind
    let redRect = UIBezierPath(rect: CGRect(x: 40, y: 40, width: 120, height: 120))
    UIColor.systemRed.setFill()
    redRect.fill()

    // Layer 2 -- drawn second, overlaps the red
    let blueRect = UIBezierPath(rect: CGRect(x: 80, y: 80, width: 120, height: 120))
    UIColor.systemBlue.setFill()
    blueRect.fill()

    // Layer 3 -- drawn last, on top of both
    let greenCircle = UIBezierPath(
        arcCenter: CGPoint(x: 120, y: 120),
        radius: 50,
        startAngle: 0,
        endAngle: .pi * 2,
        clockwise: true
    )
    UIColor.systemGreen.setFill()
    greenCircle.fill()
}
```

## RewardsGraphView Example

A complete example drawing dots, connecting lines, and labels for a rewards graph.

```swift
import UIKit

struct RewardsDataPoint {
    let label: String
    let value: CGFloat
}

class RewardsGraphView: UIView {

    var dataPoints: [RewardsDataPoint] = [] {
        didSet { setNeedsDisplay() }
    }

    private let dotRadius: CGFloat = 6
    private let lineWidth: CGFloat = 2
    private let labelFont = UIFont.systemFont(ofSize: 11, weight: .medium)
    private let padding = UIEdgeInsets(top: 30, left: 30, bottom: 40, right: 30)

    override func draw(_ rect: CGRect) {
        guard dataPoints.count >= 2 else { return }
        guard let context = UIGraphicsGetCurrentContext() else { return }

        let drawableWidth = rect.width - padding.left - padding.right
        let drawableHeight = rect.height - padding.top - padding.bottom

        let maxValue = dataPoints.map(\.value).max() ?? 1
        let minValue = dataPoints.map(\.value).min() ?? 0
        let valueRange = maxValue - minValue
        let safeRange = valueRange > 0 ? valueRange : 1

        // Calculate point positions
        let points: [CGPoint] = dataPoints.enumerated().map { index, dp in
            let x = padding.left + (drawableWidth / CGFloat(dataPoints.count - 1)) * CGFloat(index)
            let normalizedValue = (dp.value - minValue) / safeRange
            let y = padding.top + drawableHeight * (1 - normalizedValue) // flip Y
            return CGPoint(x: x, y: y)
        }

        // Draw connecting lines
        context.setStrokeColor(UIColor.systemBlue.cgColor)
        context.setLineWidth(lineWidth)
        context.setLineCap(.round)
        context.setLineJoin(.round)

        context.move(to: points[0])
        for point in points.dropFirst() {
            context.addLine(to: point)
        }
        context.strokePath()

        // Draw dots
        context.setFillColor(UIColor.systemBlue.cgColor)
        for point in points {
            let dotRect = CGRect(
                x: point.x - dotRadius,
                y: point.y - dotRadius,
                width: dotRadius * 2,
                height: dotRadius * 2
            )
            context.fillEllipse(in: dotRect)
        }

        // Draw white inner dot
        context.setFillColor(UIColor.systemBackground.cgColor)
        let innerRadius = dotRadius - 2
        for point in points {
            let dotRect = CGRect(
                x: point.x - innerRadius,
                y: point.y - innerRadius,
                width: innerRadius * 2,
                height: innerRadius * 2
            )
            context.fillEllipse(in: dotRect)
        }

        // Draw labels below each dot
        let paragraphStyle = NSMutableParagraphStyle()
        paragraphStyle.alignment = .center

        let attributes: [NSAttributedString.Key: Any] = [
            .font: labelFont,
            .foregroundColor: UIColor.secondaryLabel,
            .paragraphStyle: paragraphStyle,
        ]

        for (index, point) in points.enumerated() {
            let label = dataPoints[index].label
            let size = (label as NSString).size(withAttributes: attributes)
            let labelRect = CGRect(
                x: point.x - size.width / 2,
                y: rect.height - padding.bottom + 8,
                width: size.width,
                height: size.height
            )
            (label as NSString).draw(in: labelRect, withAttributes: attributes)
        }

        // Draw value labels above each dot
        let valueAttributes: [NSAttributedString.Key: Any] = [
            .font: UIFont.systemFont(ofSize: 10, weight: .bold),
            .foregroundColor: UIColor.systemBlue,
            .paragraphStyle: paragraphStyle,
        ]

        for (index, point) in points.enumerated() {
            let valueText = String(format: "%.0f", dataPoints[index].value)
            let size = (valueText as NSString).size(withAttributes: valueAttributes)
            let labelRect = CGRect(
                x: point.x - size.width / 2,
                y: point.y - dotRadius - size.height - 4,
                width: size.width,
                height: size.height
            )
            (valueText as NSString).draw(in: labelRect, withAttributes: valueAttributes)
        }
    }
}
```

### Usage

```swift
class RewardsViewController: UIViewController {

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground

        let graphView = RewardsGraphView()
        graphView.backgroundColor = .secondarySystemBackground
        graphView.layer.cornerRadius = 12
        graphView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(graphView)

        NSLayoutConstraint.activate([
            graphView.centerYAnchor.constraint(equalTo: view.centerYAnchor),
            graphView.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 16),
            graphView.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -16),
            graphView.heightAnchor.constraint(equalToConstant: 250),
        ])

        graphView.dataPoints = [
            RewardsDataPoint(label: "Jan", value: 120),
            RewardsDataPoint(label: "Feb", value: 250),
            RewardsDataPoint(label: "Mar", value: 180),
            RewardsDataPoint(label: "Apr", value: 310),
            RewardsDataPoint(label: "May", value: 275),
            RewardsDataPoint(label: "Jun", value: 400),
        ]
    }
}
```
