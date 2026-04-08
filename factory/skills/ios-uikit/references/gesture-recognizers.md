# Gesture Recognizers

## UIPanGestureRecognizer

Pan gestures track finger movement across the screen. The key properties are `translation` (how far the finger has moved from the start) and `velocity` (speed and direction of movement).

### State Machine

Pan gestures move through states: `.began` -> `.changed` (repeated) -> `.ended` (or `.cancelled`).

```swift
import UIKit

class DraggableViewController: UIViewController {

    let card = UIView()
    var cardOriginalCenter: CGPoint = .zero

    override func viewDidLoad() {
        super.viewDidLoad()

        card.backgroundColor = .systemBlue
        card.layer.cornerRadius = 12
        card.frame = CGRect(x: 80, y: 300, width: 220, height: 140)
        view.addSubview(card)

        let pan = UIPanGestureRecognizer(target: self, action: #selector(handlePan(_:)))
        card.addGestureRecognizer(pan)
    }

    @objc private func handlePan(_ gesture: UIPanGestureRecognizer) {
        let translation = gesture.translation(in: view)
        let velocity = gesture.velocity(in: view)

        switch gesture.state {
        case .began:
            cardOriginalCenter = card.center

        case .changed:
            card.center = CGPoint(
                x: cardOriginalCenter.x + translation.x,
                y: cardOriginalCenter.y + translation.y
            )

        case .ended:
            // Snap back or dismiss based on velocity
            if abs(velocity.y) > 500 {
                // Fling away
                UIView.animate(withDuration: 0.3) {
                    self.card.center.y += velocity.y > 0 ? 600 : -600
                    self.card.alpha = 0
                }
            } else {
                // Snap back
                UIView.animate(withDuration: 0.4, delay: 0, usingSpringWithDamping: 0.7, initialSpringVelocity: 0) {
                    self.card.center = self.cardOriginalCenter
                }
            }

        case .cancelled, .failed:
            card.center = cardOriginalCenter

        default:
            break
        }
    }
}
```

### Resetting Translation

Call `setTranslation(.zero, in:)` in `.changed` if you want incremental deltas instead of cumulative translation.

```swift
@objc private func handlePanIncremental(_ gesture: UIPanGestureRecognizer) {
    let translation = gesture.translation(in: view)

    if gesture.state == .changed {
        // Move by the delta since last call
        card.center.x += translation.x
        card.center.y += translation.y

        // Reset so next call gives a fresh delta
        gesture.setTranslation(.zero, in: view)
    }
}
```

## Long Press for Table View Reordering with Cell Snapshot

A long press creates a floating snapshot of the cell, which follows the finger as rows reorder.

```swift
import UIKit

class ReorderableTableViewController: UIViewController, UITableViewDataSource {

    var items = ["Apple", "Banana", "Cherry", "Date", "Elderberry", "Fig"]
    let tableView = UITableView()

    private var snapshot: UIView?
    private var sourceIndexPath: IndexPath?

    override func viewDidLoad() {
        super.viewDidLoad()

        tableView.frame = view.bounds
        tableView.dataSource = self
        view.addSubview(tableView)

        let longPress = UILongPressGestureRecognizer(
            target: self,
            action: #selector(handleLongPress(_:))
        )
        longPress.minimumPressDuration = 0.3
        tableView.addGestureRecognizer(longPress)
    }

    @objc private func handleLongPress(_ gesture: UILongPressGestureRecognizer) {
        let location = gesture.location(in: tableView)

        switch gesture.state {
        case .began:
            guard let indexPath = tableView.indexPathForRow(at: location),
                  let cell = tableView.cellForRow(at: indexPath) else { return }

            sourceIndexPath = indexPath

            // Create a snapshot of the cell
            let snap = cell.snapshotView(afterScreenUpdates: true) ?? UIView()
            snap.frame = cell.frame
            snap.alpha = 0.9
            snap.layer.shadowOpacity = 0.3
            snap.layer.shadowRadius = 4
            tableView.addSubview(snap)
            snapshot = snap

            // Fade out the original cell
            UIView.animate(withDuration: 0.2) {
                cell.alpha = 0
                snap.transform = CGAffineTransform(scaleX: 1.05, y: 1.05)
            }

        case .changed:
            guard let snap = snapshot else { return }

            // Move the snapshot with the finger
            snap.center.y = location.y

            // Determine the destination index path
            guard let destinationIndexPath = tableView.indexPathForRow(at: location),
                  let source = sourceIndexPath,
                  destinationIndexPath != source else { return }

            // Swap data
            items.insert(items.remove(at: source.row), at: destinationIndexPath.row)

            // Move the row in the table view
            tableView.moveRow(at: source, to: destinationIndexPath)
            sourceIndexPath = destinationIndexPath

        case .ended, .cancelled:
            guard let source = sourceIndexPath,
                  let cell = tableView.cellForRow(at: source) else {
                snapshot?.removeFromSuperview()
                snapshot = nil
                return
            }

            // Animate snapshot back to cell position and remove
            UIView.animate(withDuration: 0.25, animations: {
                self.snapshot?.center = cell.center
                self.snapshot?.transform = .identity
                cell.alpha = 1
            }, completion: { _ in
                self.snapshot?.removeFromSuperview()
                self.snapshot = nil
            })

            sourceIndexPath = nil

        default:
            break
        }
    }

    // MARK: - UITableViewDataSource

    func tableView(_ tableView: UITableView, numberOfRowsInSection section: Int) -> Int {
        return items.count
    }

    func tableView(_ tableView: UITableView, cellForRowAt indexPath: IndexPath) -> UITableViewCell {
        let cell = tableView.dequeueReusableCell(withIdentifier: "cell")
            ?? UITableViewCell(style: .default, reuseIdentifier: "cell")
        cell.textLabel?.text = items[indexPath.row]
        return cell
    }
}
```

## Tap Gesture Basics

```swift
import UIKit

class TapDemoViewController: UIViewController {

    let label = UILabel()

    override func viewDidLoad() {
        super.viewDidLoad()

        label.text = "Tap me"
        label.font = .systemFont(ofSize: 24, weight: .medium)
        label.textAlignment = .center
        label.isUserInteractionEnabled = true // Required for labels and image views
        label.frame = CGRect(x: 60, y: 200, width: 250, height: 50)
        view.addSubview(label)

        // Single tap
        let singleTap = UITapGestureRecognizer(target: self, action: #selector(handleSingleTap))
        singleTap.numberOfTapsRequired = 1
        label.addGestureRecognizer(singleTap)

        // Double tap
        let doubleTap = UITapGestureRecognizer(target: self, action: #selector(handleDoubleTap))
        doubleTap.numberOfTapsRequired = 2
        label.addGestureRecognizer(doubleTap)

        // Single tap should wait and confirm it is not a double tap
        singleTap.require(toFail: doubleTap)
    }

    @objc private func handleSingleTap() {
        label.text = "Single tap!"
    }

    @objc private func handleDoubleTap() {
        label.text = "Double tap!"
    }
}
```

## InstantPanGestureRecognizer

A UIPanGestureRecognizer subclass that enters `.began` immediately on touch, without waiting for the standard movement threshold. Useful for interactive transitions and custom scroll views.

```swift
import UIKit

class InstantPanGestureRecognizer: UIPanGestureRecognizer {

    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent) {
        super.touchesBegan(touches, with: event)

        // Transition directly to .began instead of waiting for movement
        if state == .possible {
            state = .began
        }
    }
}
```

### Usage

```swift
class InteractiveCardViewController: UIViewController {

    let card = UIView()

    override func viewDidLoad() {
        super.viewDidLoad()

        card.backgroundColor = .systemIndigo
        card.layer.cornerRadius = 16
        card.frame = CGRect(x: 40, y: 200, width: 300, height: 200)
        view.addSubview(card)

        // Responds immediately -- no delay before .began fires
        let instantPan = InstantPanGestureRecognizer(target: self, action: #selector(handlePan(_:)))
        card.addGestureRecognizer(instantPan)
    }

    @objc private func handlePan(_ gesture: UIPanGestureRecognizer) {
        let translation = gesture.translation(in: view)

        switch gesture.state {
        case .began:
            // Fires instantly on touch down
            UIView.animate(withDuration: 0.2) {
                self.card.transform = CGAffineTransform(scaleX: 0.95, y: 0.95)
            }

        case .changed:
            card.transform = CGAffineTransform(scaleX: 0.95, y: 0.95)
                .concatenating(CGAffineTransform(translationX: translation.x, y: translation.y))

        case .ended, .cancelled:
            UIView.animate(withDuration: 0.4, delay: 0, usingSpringWithDamping: 0.7, initialSpringVelocity: 0) {
                self.card.transform = .identity
            }

        default:
            break
        }
    }
}
```

## Anchor Point Considerations for Rotation Gestures

The `anchorPoint` of a layer determines the pivot point for rotations and scales. Default is `(0.5, 0.5)` (center). Changing it shifts the visual position unless you also adjust the layer's `position`.

```swift
import UIKit

class RotationDemoViewController: UIViewController {

    let dial = UIView()

    override func viewDidLoad() {
        super.viewDidLoad()

        dial.backgroundColor = .systemOrange
        dial.frame = CGRect(x: 100, y: 300, width: 180, height: 180)
        dial.layer.cornerRadius = 90
        view.addSubview(dial)

        // Add a marker so rotation is visible
        let marker = UIView()
        marker.backgroundColor = .white
        marker.frame = CGRect(x: 85, y: 10, width: 10, height: 40)
        marker.layer.cornerRadius = 5
        dial.addSubview(marker)

        let rotation = UIRotationGestureRecognizer(
            target: self,
            action: #selector(handleRotation(_:))
        )
        dial.addGestureRecognizer(rotation)
    }

    @objc private func handleRotation(_ gesture: UIRotationGestureRecognizer) {
        // Rotation happens around the anchor point (default center)
        dial.transform = dial.transform.rotated(by: gesture.rotation)
        gesture.rotation = 0 // reset so we get incremental values
    }
}

// To rotate around a different point (e.g., top-left corner):
extension UIView {

    /// Changes the anchor point without shifting the view's visual position.
    func setAnchorPoint(_ point: CGPoint) {
        let oldOrigin = frame.origin
        layer.anchorPoint = point
        let newOrigin = frame.origin

        let translation = CGPoint(
            x: newOrigin.x - oldOrigin.x,
            y: newOrigin.y - oldOrigin.y
        )

        center = CGPoint(
            x: center.x - translation.x,
            y: center.y - translation.y
        )
    }
}

// Usage:
// dial.setAnchorPoint(CGPoint(x: 0, y: 0)) // rotate around top-left
// dial.setAnchorPoint(CGPoint(x: 1, y: 1)) // rotate around bottom-right
```
