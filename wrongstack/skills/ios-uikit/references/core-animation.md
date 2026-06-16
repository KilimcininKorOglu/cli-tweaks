# Core Animation

## CABasicAnimation

Animates a single property from one value to another over a duration.

```swift
// Position animation
let positionAnim = CABasicAnimation(keyPath: "position.y")
positionAnim.fromValue = 100
positionAnim.toValue = 400
positionAnim.duration = 1.0

// CRITICAL: Update the model layer BEFORE adding animation.
// Without this, the view snaps back to its original position when the animation ends.
myView.layer.position.y = 400
myView.layer.add(positionAnim, forKey: "positionY")
```

```swift
// Scale animation
let scaleAnim = CABasicAnimation(keyPath: "transform.scale")
scaleAnim.fromValue = 1.0
scaleAnim.toValue = 2.0
scaleAnim.duration = 0.5

myView.layer.transform = CATransform3DMakeScale(2.0, 2.0, 1.0)
myView.layer.add(scaleAnim, forKey: "scale")
```

```swift
// Rotation animation
let rotationAnim = CABasicAnimation(keyPath: "transform.rotation.z")
rotationAnim.fromValue = 0
rotationAnim.toValue = CGFloat.pi * 2
rotationAnim.duration = 1.0

myView.layer.transform = CATransform3DMakeRotation(CGFloat.pi * 2, 0, 0, 1)
myView.layer.add(rotationAnim, forKey: "rotation")
```

### Model Layer Update Pattern

The **model layer** holds the real property values. The **presentation layer** is the on-screen copy during animation. Core Animation only animates the presentation layer. If you do not set the model layer to the final value, the view snaps back when the animation completes.

```swift
// WRONG -- snaps back after animation
let anim = CABasicAnimation(keyPath: "position.x")
anim.fromValue = view.layer.position.x
anim.toValue = 300
anim.duration = 1.0
view.layer.add(anim, forKey: "move")

// CORRECT -- set model layer to final value, then add animation
let anim = CABasicAnimation(keyPath: "position.x")
anim.fromValue = view.layer.position.x
anim.toValue = 300
anim.duration = 1.0
view.layer.position.x = 300          // <-- persist final state
view.layer.add(anim, forKey: "move")
```

Common animatable keyPaths:

- `position`, `position.x`, `position.y`
- `opacity`
- `transform.scale`, `transform.scale.x`, `transform.scale.y`
- `transform.rotation.z`
- `backgroundColor`
- `cornerRadius`
- `borderWidth`, `borderColor`
- `shadowOpacity`, `shadowOffset`, `shadowRadius`, `shadowColor`

---

## CAKeyframeAnimation

Animates through a sequence of values with control over timing at each step.

### Shake Animation

```swift
func shakeView(_ view: UIView) {
    let shake = CAKeyframeAnimation(keyPath: "position.x")
    shake.values = [0, 10, -10, 10, -5, 5, -2, 0]
    shake.keyTimes = [0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 1.0]
    shake.duration = 0.4
    shake.isAdditive = true  // values are relative to the current model value
    view.layer.add(shake, forKey: "shake")
}
```

`isAdditive = true` makes values **relative** to the current model layer value rather than absolute. This avoids having to calculate the view's current position -- the values above are offsets from wherever the view currently is.

### Pulsing Animation

```swift
func pulseView(_ view: UIView) {
    let pulse = CAKeyframeAnimation(keyPath: "transform.scale")
    pulse.values = [1.0, 1.15, 0.95, 1.05, 1.0]
    pulse.keyTimes = [0, 0.25, 0.5, 0.75, 1.0]
    pulse.duration = 0.6
    pulse.timingFunctions = [
        CAMediaTimingFunction(name: .easeInEaseOut),
        CAMediaTimingFunction(name: .easeInEaseOut),
        CAMediaTimingFunction(name: .easeInEaseOut),
        CAMediaTimingFunction(name: .easeInEaseOut)
    ]
    view.layer.add(pulse, forKey: "pulse")
}
```

---

## Path-Based Animation

Animate a layer along an arbitrary CGPath.

### Ellipse Orbit

```swift
func orbitAnimation(for view: UIView, in bounds: CGRect) {
    let orbitPath = CGPath(
        ellipseIn: bounds.insetBy(dx: 40, dy: 80),
        transform: nil
    )

    let orbit = CAKeyframeAnimation(keyPath: "position")
    orbit.path = orbitPath
    orbit.calculationMode = .paced       // constant speed along path
    orbit.rotationMode = .rotateAuto     // layer tangent follows path direction
    orbit.duration = 3.0
    orbit.repeatCount = .infinity

    view.layer.add(orbit, forKey: "orbit")
}
```

- `calculationMode = .paced` -- ignores `keyTimes` and distributes motion evenly along the path length so the object moves at constant speed.
- `rotationMode = .rotateAuto` -- automatically rotates the layer so its front edge always faces the direction of travel.

### Custom Bezier Path

```swift
func curvedPathAnimation(for view: UIView) {
    let path = UIBezierPath()
    path.move(to: CGPoint(x: 50, y: 400))
    path.addCurve(
        to: CGPoint(x: 300, y: 100),
        controlPoint1: CGPoint(x: 100, y: 200),
        controlPoint2: CGPoint(x: 250, y: 300)
    )

    let pathAnim = CAKeyframeAnimation(keyPath: "position")
    pathAnim.path = path.cgPath
    pathAnim.calculationMode = .paced
    pathAnim.duration = 2.0

    view.layer.position = CGPoint(x: 300, y: 100)  // model layer to end
    view.layer.add(pathAnim, forKey: "curvePath")
}
```

---

## CAGradientLayer

### Basic Setup

```swift
func addGradient(to view: UIView) {
    let gradientLayer = CAGradientLayer()
    gradientLayer.frame = view.bounds
    gradientLayer.colors = [
        UIColor.systemBlue.cgColor,
        UIColor.systemPurple.cgColor
    ]
    view.layer.addSublayer(gradientLayer)
}
```

### Direction Control

`startPoint` and `endPoint` use the **unit coordinate system**: `(0,0)` is top-left, `(1,1)` is bottom-right.

```swift
// Top to bottom (default)
gradientLayer.startPoint = CGPoint(x: 0.5, y: 0)
gradientLayer.endPoint   = CGPoint(x: 0.5, y: 1)

// Left to right
gradientLayer.startPoint = CGPoint(x: 0, y: 0.5)
gradientLayer.endPoint   = CGPoint(x: 1, y: 0.5)

// Diagonal: top-left to bottom-right
gradientLayer.startPoint = CGPoint(x: 0, y: 0)
gradientLayer.endPoint   = CGPoint(x: 1, y: 1)
```

### Color Locations

`locations` maps each color to a position from 0.0 to 1.0. Count must match `colors`.

```swift
gradientLayer.colors = [
    UIColor.red.cgColor,
    UIColor.yellow.cgColor,
    UIColor.green.cgColor
]
gradientLayer.locations = [0.0, 0.3, 1.0]  // yellow starts at 30% mark
```

### Animated Gradient Color Change

```swift
func animateGradientColors(layer: CAGradientLayer) {
    let colorAnim = CABasicAnimation(keyPath: "colors")
    colorAnim.fromValue = layer.colors
    colorAnim.toValue = [
        UIColor.systemOrange.cgColor,
        UIColor.systemPink.cgColor
    ]
    colorAnim.duration = 2.0

    // Persist the final colors on the model layer
    layer.colors = [
        UIColor.systemOrange.cgColor,
        UIColor.systemPink.cgColor
    ]
    layer.add(colorAnim, forKey: "colorChange")
}
```

Use a helper method for looping gradient animations:

```swift
func setColors(_ colors: [CGColor], on layer: CAGradientLayer, animated: Bool = true) {
    if animated {
        let anim = CABasicAnimation(keyPath: "colors")
        anim.fromValue = layer.colors
        anim.toValue = colors
        anim.duration = 1.0
        anim.fillMode = .forwards
        layer.add(anim, forKey: "setColors")
    }
    layer.colors = colors
}
```

---

## Gradient Types

### Linear (Default)

```swift
let linear = CAGradientLayer()
linear.type = .axial          // .axial is the default linear gradient
linear.colors = [
    UIColor.systemBlue.cgColor,
    UIColor.systemCyan.cgColor
]
linear.frame = view.bounds
view.layer.addSublayer(linear)
```

### Radial

```swift
let radial = CAGradientLayer()
radial.type = .radial
radial.colors = [
    UIColor.white.cgColor,
    UIColor.systemBlue.cgColor
]
// For radial: startPoint is the center, endPoint defines the radius edge
radial.startPoint = CGPoint(x: 0.5, y: 0.5)   // center
radial.endPoint   = CGPoint(x: 1.0, y: 1.0)   // corner -- defines radius
radial.frame = view.bounds
view.layer.addSublayer(radial)
```

For `.radial`, the gradient radiates outward from `startPoint` to the circle defined by the distance to `endPoint`. The gradient circle is an ellipse that fits within the rectangle defined by these two points.

---

## Shadows

### Simple Shadow

```swift
func applyShadow(to view: UIView) {
    view.layer.shadowOpacity = 0.5        // 0 = invisible, 1 = fully opaque
    view.layer.shadowOffset = CGSize(width: 0, height: 4)
    view.layer.shadowRadius = 8
    view.layer.shadowColor = UIColor.black.cgColor
    view.layer.masksToBounds = false       // MUST be false -- shadows are drawn outside bounds
}
```

### Performance Optimization

Shadows are expensive because the system traces the layer's composited alpha channel every frame.

```swift
// Option 1: shouldRasterize -- caches the rendered layer + shadow as a bitmap
view.layer.shouldRasterize = true
view.layer.rasterizationScale = UIScreen.main.scale  // match retina resolution

// Option 2: shadowPath -- precomputes the shadow shape (much faster)
view.layer.shadowPath = UIBezierPath(
    roundedRect: view.bounds,
    cornerRadius: view.layer.cornerRadius
).cgPath
```

`shadowPath` is the preferred approach. It eliminates per-frame alpha tracing. Update it whenever the view's bounds change (e.g., in `layoutSubviews`).

### Custom Shadow Paths

#### Bottom Contact Shadow

A thin, tight shadow directly below the view (material resting on a surface).

```swift
func bottomContactShadow(for view: UIView) {
    let rect = view.bounds
    let contactRect = CGRect(
        x: rect.origin.x + 8,
        y: rect.maxY - 4,
        width: rect.width - 16,
        height: 8
    )
    view.layer.shadowPath = UIBezierPath(ovalIn: contactRect).cgPath
    view.layer.shadowOpacity = 0.4
    view.layer.shadowRadius = 4
    view.layer.shadowOffset = .zero
}
```

#### Front 3D Perspective Shadow

Shadow extends downward and to the right, giving a 3D tilted appearance.

```swift
func perspectiveShadow(for view: UIView) {
    let rect = view.bounds
    let path = UIBezierPath()

    // Trapezoid shape below the view
    path.move(to: CGPoint(x: rect.minX + 10, y: rect.maxY))      // bottom-left of view
    path.addLine(to: CGPoint(x: rect.maxX - 10, y: rect.maxY))   // bottom-right of view
    path.addLine(to: CGPoint(x: rect.maxX + 20, y: rect.maxY + 30))  // right offset down
    path.addLine(to: CGPoint(x: rect.minX - 10, y: rect.maxY + 30))  // left offset down
    path.close()

    view.layer.shadowPath = path.cgPath
    view.layer.shadowOpacity = 0.3
    view.layer.shadowRadius = 6
    view.layer.shadowOffset = .zero
}
```

#### Curved Shadow

An arced shadow along the bottom edge using `addCurve`.

```swift
func curvedShadow(for view: UIView) {
    let rect = view.bounds
    let path = UIBezierPath()

    let curveDepth: CGFloat = 20

    path.move(to: CGPoint(x: rect.minX, y: rect.maxY))
    path.addLine(to: CGPoint(x: rect.maxX, y: rect.maxY))

    // Curved bottom edge bowing downward
    path.addCurve(
        to: CGPoint(x: rect.minX, y: rect.maxY),
        controlPoint1: CGPoint(x: rect.maxX - 20, y: rect.maxY + curveDepth),
        controlPoint2: CGPoint(x: rect.minX + 20, y: rect.maxY + curveDepth)
    )
    path.close()

    view.layer.shadowPath = path.cgPath
    view.layer.shadowOpacity = 0.35
    view.layer.shadowRadius = 5
    view.layer.shadowOffset = .zero
}
```

---

## CAAnimationGroup

Groups multiple animations so they run together with shared timing control.

```swift
func groupedAnimation(on view: UIView) {
    // Animation 1: Fade in
    let fadeIn = CABasicAnimation(keyPath: "opacity")
    fadeIn.fromValue = 0
    fadeIn.toValue = 1
    fadeIn.duration = 1.0

    // Animation 2: Scale up
    let scaleUp = CABasicAnimation(keyPath: "transform.scale")
    scaleUp.fromValue = 0.5
    scaleUp.toValue = 1.0
    scaleUp.duration = 0.8

    // Animation 3: Move up (starts after a delay)
    let moveUp = CABasicAnimation(keyPath: "position.y")
    moveUp.fromValue = view.layer.position.y + 50
    moveUp.toValue = view.layer.position.y
    moveUp.duration = 0.6
    moveUp.beginTime = 0.4   // starts 0.4s after group begins

    let group = CAAnimationGroup()
    group.animations = [fadeIn, scaleUp, moveUp]
    group.duration = 1.5     // overall duration (must be >= longest sub-animation)
    group.repeatCount = 1
    group.timingFunction = CAMediaTimingFunction(name: .easeInEaseOut)

    // Update model layer
    view.layer.opacity = 1
    view.layer.transform = CATransform3DIdentity

    view.layer.add(group, forKey: "introGroup")
}
```

### Staggered beginTime

Each sub-animation's `beginTime` is relative to the group's start:

```swift
let anim1 = CABasicAnimation(keyPath: "opacity")
anim1.beginTime = 0.0       // starts immediately

let anim2 = CABasicAnimation(keyPath: "transform.scale")
anim2.beginTime = 0.3       // starts 0.3s into the group

let anim3 = CABasicAnimation(keyPath: "position.y")
anim3.beginTime = 0.6       // starts 0.6s into the group
```

### repeatCount and Infinite Repeat

```swift
group.repeatCount = 3            // play 3 times
group.repeatCount = .infinity    // loop forever
group.autoreverses = true        // play forward then backward each cycle
```

---

## Shimmer / Skeleton Loading

A common pattern for placeholder loading states using animated gradient color cycling.

### Protocol-Based SkeletonLoadable

```swift
protocol SkeletonLoadable {}

extension SkeletonLoadable {
    func makeAnimationGroup(previousGroup: CAAnimationGroup? = nil) -> CAAnimationGroup {
        let animDuration: CFTimeInterval = 1.5

        // Dark to light
        let anim1 = CABasicAnimation(keyPath: #keyPath(CAGradientLayer.backgroundColor))
        anim1.fromValue = UIColor.systemGray5.cgColor
        anim1.toValue = UIColor.systemGray6.cgColor
        anim1.duration = animDuration
        anim1.beginTime = 0.0

        // Light to dark
        let anim2 = CABasicAnimation(keyPath: #keyPath(CAGradientLayer.backgroundColor))
        anim2.fromValue = UIColor.systemGray6.cgColor
        anim2.toValue = UIColor.systemGray5.cgColor
        anim2.duration = animDuration
        anim2.beginTime = anim1.beginTime + anim1.duration

        let group = CAAnimationGroup()
        group.animations = [anim1, anim2]
        group.repeatCount = .infinity
        group.duration = anim2.beginTime + anim2.duration
        group.isRemovedOnCompletion = false

        // Stagger: offset from the previous group so items shimmer in sequence
        if let previousGroup = previousGroup {
            group.beginTime = previousGroup.beginTime + 0.33
        }

        return group
    }
}
```

### Skeleton Cell Implementation

```swift
class SkeletonCell: UITableViewCell, SkeletonLoadable {

    let titleLayer = CAGradientLayer()
    let subtitleLayer = CAGradientLayer()

    override init(style: UITableViewCell.CellStyle, reuseIdentifier: String?) {
        super.init(style: style, reuseIdentifier: reuseIdentifier)
        setupLayers()
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }

    private func setupLayers() {
        titleLayer.startPoint = CGPoint(x: 0, y: 0.5)
        titleLayer.endPoint = CGPoint(x: 1, y: 0.5)
        titleLayer.cornerRadius = 4
        contentView.layer.addSublayer(titleLayer)

        subtitleLayer.startPoint = CGPoint(x: 0, y: 0.5)
        subtitleLayer.endPoint = CGPoint(x: 1, y: 0.5)
        subtitleLayer.cornerRadius = 4
        contentView.layer.addSublayer(subtitleLayer)
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        titleLayer.frame = CGRect(x: 16, y: 12, width: bounds.width - 32, height: 16)
        subtitleLayer.frame = CGRect(x: 16, y: 36, width: bounds.width * 0.6, height: 12)
    }

    func startAnimating() {
        // Stagger: second group is offset from the first
        let titleGroup = makeAnimationGroup()
        titleLayer.add(titleGroup, forKey: "skeleton")

        let subtitleGroup = makeAnimationGroup(previousGroup: titleGroup)
        subtitleLayer.add(subtitleGroup, forKey: "skeleton")
    }

    func stopAnimating() {
        titleLayer.removeAllAnimations()
        subtitleLayer.removeAllAnimations()
        titleLayer.removeFromSuperlayer()
        subtitleLayer.removeFromSuperlayer()
    }
}
```

---

## Keyframe UIView Animation

`UIView.animateKeyframes` uses **relative** start times and durations (0.0 to 1.0 fractions of the total duration).

### Bell Shake Pattern

```swift
func bellShake(_ view: UIView) {
    UIView.animateKeyframes(withDuration: 0.5, delay: 0, options: []) {
        UIView.addKeyframe(withRelativeStartTime: 0.0, relativeDuration: 0.15) {
            view.transform = CGAffineTransform(rotationAngle: .pi / 8)
        }
        UIView.addKeyframe(withRelativeStartTime: 0.15, relativeDuration: 0.15) {
            view.transform = CGAffineTransform(rotationAngle: -.pi / 8)
        }
        UIView.addKeyframe(withRelativeStartTime: 0.30, relativeDuration: 0.15) {
            view.transform = CGAffineTransform(rotationAngle: .pi / 16)
        }
        UIView.addKeyframe(withRelativeStartTime: 0.45, relativeDuration: 0.15) {
            view.transform = CGAffineTransform(rotationAngle: -.pi / 16)
        }
        UIView.addKeyframe(withRelativeStartTime: 0.60, relativeDuration: 0.15) {
            view.transform = CGAffineTransform(rotationAngle: .pi / 32)
        }
        UIView.addKeyframe(withRelativeStartTime: 0.75, relativeDuration: 0.25) {
            view.transform = .identity
        }
    }
}
```

### Multi-Step Move

```swift
func stepAnimation(_ view: UIView) {
    let totalDuration: TimeInterval = 2.0

    UIView.animateKeyframes(withDuration: totalDuration, delay: 0, options: [.calculationModeCubic]) {
        // Phase 1: move right and fade out (first 50%)
        UIView.addKeyframe(withRelativeStartTime: 0.0, relativeDuration: 0.5) {
            view.center.x += 100
            view.alpha = 0.3
        }
        // Phase 2: move down and fade in (last 50%)
        UIView.addKeyframe(withRelativeStartTime: 0.5, relativeDuration: 0.5) {
            view.center.y += 100
            view.alpha = 1.0
        }
    }
}
```

---

## Anchor Point Adjustment

Changing `anchorPoint` shifts the layer's visual position because the anchor point defines where `position` is pinned. This extension compensates by adjusting `position` so the view stays in place.

```swift
extension UIView {
    func setAnchorPoint(_ point: CGPoint) {
        // Save the old position in superlayer coordinates
        let oldOrigin = frame.origin

        // Change the anchor point
        layer.anchorPoint = point

        // Restore visual position
        let newOrigin = frame.origin
        let delta = CGPoint(
            x: newOrigin.x - oldOrigin.x,
            y: newOrigin.y - oldOrigin.y
        )
        layer.position = CGPoint(
            x: layer.position.x - delta.x,
            y: layer.position.y - delta.y
        )
    }
}
```

Usage (rotate from bottom edge instead of center):

```swift
override func viewDidAppear(_ animated: Bool) {
    super.viewDidAppear(animated)

    cardView.setAnchorPoint(CGPoint(x: 0.5, y: 1.0))  // bottom center

    UIView.animate(withDuration: 0.6) {
        self.cardView.transform = CGAffineTransform(rotationAngle: .pi / 6)
    }
}
```

---

## Critical Rules

### 1. Model Layer vs Presentation Layer

The model layer holds the **truth**. Core Animation only animates the presentation layer. Always set the model layer to the animation's final value before or alongside adding the animation, or the view snaps back.

```swift
// Always do this:
layer.opacity = 1.0                         // model layer = final value
layer.add(fadeAnimation, forKey: "fade")    // presentation layer animates
```

If you need to read the current on-screen value **during** animation (e.g., for hit testing), query the presentation layer:

```swift
if let presentationLayer = view.layer.presentation() {
    let currentPosition = presentationLayer.position
}
```

### 2. Bounds-Dependent Timing

`CAGradientLayer`, shadows with `shadowPath`, and any layer whose `frame` is derived from `view.bounds` must be configured in `viewDidAppear(_:)` or `layoutSubviews()` -- **not** in `viewDidLoad()`. Auto Layout has not resolved frames yet in `viewDidLoad`.

```swift
class GradientViewController: UIViewController {
    let gradientLayer = CAGradientLayer()

    override func viewDidLoad() {
        super.viewDidLoad()
        gradientLayer.colors = [UIColor.red.cgColor, UIColor.blue.cgColor]
        view.layer.addSublayer(gradientLayer)
        // DO NOT set gradientLayer.frame here -- bounds are zero or stale
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        gradientLayer.frame = view.bounds   // bounds are now final
    }

    // Also update on rotation / resize
    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        gradientLayer.frame = view.bounds
    }
}
```

### 3. Transform Concatenation

Transforms applied via `CGAffineTransformConcat` or `CATransform3DConcat` are **not commutative** -- order matters. Scale-then-rotate produces a different result than rotate-then-scale.

```swift
// Scale then rotate
var t = CGAffineTransform.identity
t = t.scaledBy(x: 2.0, y: 2.0)
t = t.rotated(by: .pi / 4)
view.transform = t

// Rotate then scale (different visual result)
var t2 = CGAffineTransform.identity
t2 = t2.rotated(by: .pi / 4)
t2 = t2.scaledBy(x: 2.0, y: 2.0)
view.transform = t2
```

When combining transforms, always start from `.identity` and chain in the intended order.

### 4. masksToBounds and Shadows

`masksToBounds = true` (or `clipsToBounds = true`) clips content to the layer boundary, which also clips the shadow since shadows are drawn outside bounds. If you need both clipping and a shadow, wrap the view in a container that draws the shadow.

```swift
// Container draws the shadow
let shadowContainer = UIView()
shadowContainer.layer.shadowOpacity = 0.3
shadowContainer.layer.shadowRadius = 8
shadowContainer.layer.shadowOffset = CGSize(width: 0, height: 4)

// Inner view clips its content
let cardView = UIView()
cardView.layer.cornerRadius = 12
cardView.clipsToBounds = true

shadowContainer.addSubview(cardView)
```

### 5. removeOnCompletion Default

`CAAnimation.isRemovedOnCompletion` defaults to `true`. The animation object is removed from the layer when it finishes. If you set `fillMode = .forwards` without setting the model layer, the visual state persists only while the animation object exists -- it will vanish unpredictably (e.g., on background/foreground transitions). Always update the model layer instead of relying on `fillMode`.
