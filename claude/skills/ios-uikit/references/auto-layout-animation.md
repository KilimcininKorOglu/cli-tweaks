# Auto Layout Animation

## Constraint-Based Animation Pattern

The core pattern: store a constraint reference, modify its `.constant`, then call `layoutIfNeeded()` inside an animation block.

```swift
import UIKit

class SlideInViewController: UIViewController {

    let box = UIView()
    var boxLeadingConstraint: NSLayoutConstraint!

    override func viewDidLoad() {
        super.viewDidLoad()

        box.backgroundColor = .systemBlue
        box.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(box)

        // Start off-screen to the left
        boxLeadingConstraint = box.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: -200)

        NSLayoutConstraint.activate([
            boxLeadingConstraint,
            box.centerYAnchor.constraint(equalTo: view.centerYAnchor),
            box.widthAnchor.constraint(equalToConstant: 150),
            box.heightAnchor.constraint(equalToConstant: 150),
        ])
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        slideIn()
    }

    func slideIn() {
        // 1. Update the constraint
        boxLeadingConstraint.constant = 40

        // 2. Animate the layout change
        UIViewPropertyAnimator(duration: 0.6, dampingRatio: 0.7) {
            self.view.layoutIfNeeded()
        }.startAnimation()
    }
}
```

## UIViewPropertyAnimator with startAnimation(afterDelay:)

```swift
func animateWithDelay() {
    let animator = UIViewPropertyAnimator(duration: 0.5, curve: .easeInOut) {
        self.boxLeadingConstraint.constant = 40
        self.view.layoutIfNeeded()
    }
    animator.startAnimation(afterDelay: 1.0) // waits 1 second then starts
}
```

## Chaining Animators with addCompletion

```swift
func chainedAnimation() {
    let moveRight = UIViewPropertyAnimator(duration: 0.4, curve: .easeIn) {
        self.boxLeadingConstraint.constant = 200
        self.view.layoutIfNeeded()
    }

    moveRight.addCompletion { _ in
        let fadeOut = UIViewPropertyAnimator(duration: 0.3, curve: .easeOut) {
            self.box.alpha = 0
        }
        fadeOut.startAnimation()
    }

    moveRight.startAnimation()
}
```

## Off-Screen to On-Screen Pattern (Login Form Slide-In)

```swift
import UIKit

class LoginViewController: UIViewController {

    let titleLabel = UILabel()
    let usernameField = UITextField()
    let passwordField = UITextField()
    let loginButton = UIButton(type: .system)

    var titleCenterXConstraint: NSLayoutConstraint!
    var usernameCenterXConstraint: NSLayoutConstraint!
    var passwordCenterXConstraint: NSLayoutConstraint!
    var buttonCenterXConstraint: NSLayoutConstraint!

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        setupViews()
        layoutViews()
    }

    private func setupViews() {
        titleLabel.text = "Welcome Back"
        titleLabel.font = .systemFont(ofSize: 28, weight: .bold)
        titleLabel.translatesAutoresizingMaskIntoConstraints = false

        usernameField.placeholder = "Username"
        usernameField.borderStyle = .roundedRect
        usernameField.translatesAutoresizingMaskIntoConstraints = false

        passwordField.placeholder = "Password"
        passwordField.borderStyle = .roundedRect
        passwordField.isSecureTextEntry = true
        passwordField.translatesAutoresizingMaskIntoConstraints = false

        loginButton.setTitle("Log In", for: .normal)
        loginButton.translatesAutoresizingMaskIntoConstraints = false

        [titleLabel, usernameField, passwordField, loginButton].forEach {
            view.addSubview($0)
        }
    }

    private func layoutViews() {
        let offScreenOffset = view.bounds.width // start far right

        titleCenterXConstraint = titleLabel.centerXAnchor.constraint(
            equalTo: view.centerXAnchor, constant: offScreenOffset
        )
        usernameCenterXConstraint = usernameField.centerXAnchor.constraint(
            equalTo: view.centerXAnchor, constant: offScreenOffset
        )
        passwordCenterXConstraint = passwordField.centerXAnchor.constraint(
            equalTo: view.centerXAnchor, constant: offScreenOffset
        )
        buttonCenterXConstraint = loginButton.centerXAnchor.constraint(
            equalTo: view.centerXAnchor, constant: offScreenOffset
        )

        NSLayoutConstraint.activate([
            titleCenterXConstraint,
            titleLabel.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor, constant: 80),

            usernameCenterXConstraint,
            usernameField.topAnchor.constraint(equalTo: titleLabel.bottomAnchor, constant: 40),
            usernameField.widthAnchor.constraint(equalToConstant: 260),

            passwordCenterXConstraint,
            passwordField.topAnchor.constraint(equalTo: usernameField.bottomAnchor, constant: 16),
            passwordField.widthAnchor.constraint(equalToConstant: 260),

            buttonCenterXConstraint,
            loginButton.topAnchor.constraint(equalTo: passwordField.bottomAnchor, constant: 30),
        ])
    }

    override func viewDidAppear(_ animated: Bool) {
        super.viewDidAppear(animated)
        animateFormIn()
    }

    private func animateFormIn() {
        let constraints = [
            titleCenterXConstraint,
            usernameCenterXConstraint,
            passwordCenterXConstraint,
            buttonCenterXConstraint,
        ]

        for (index, constraint) in constraints.enumerated() {
            constraint?.constant = 0
            let animator = UIViewPropertyAnimator(duration: 0.5, dampingRatio: 0.8) {
                self.view.layoutIfNeeded()
            }
            animator.startAnimation(afterDelay: Double(index) * 0.15)
        }
    }
}
```

## CGAffineTransform

Transforms modify a view's visual appearance without changing its constraints.

### Basic Transforms

```swift
// Translation -- move 100pt right and 50pt down
view.transform = CGAffineTransform(translationX: 100, y: 50)

// Scale -- make 1.5x wider and 2x taller
view.transform = CGAffineTransform(scaleX: 1.5, y: 2.0)

// Rotation -- rotate 45 degrees
view.transform = CGAffineTransform(rotationAngle: .pi / 4)

// Reset to original
view.transform = .identity
```

### Concatenating Transforms

```swift
// Combine multiple transforms with .concatenating()
let translate = CGAffineTransform(translationX: 0, y: -30)
let scale = CGAffineTransform(scaleX: 1.2, y: 1.2)
view.transform = translate.concatenating(scale)
```

## FormFieldView: Enter/Exit Email Animation with Transform Concatenation

```swift
import UIKit

class FormFieldView: UIView {

    let label = UILabel()
    let textField = UITextField()
    let errorLabel = UILabel()

    enum AnimationState {
        case enter
        case exit
    }

    override init(frame: CGRect) {
        super.init(frame: frame)
        setup()
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    private func setup() {
        let stackView = UIStackView(arrangedSubviews: [label, textField, errorLabel])
        stackView.axis = .vertical
        stackView.spacing = 6
        stackView.translatesAutoresizingMaskIntoConstraints = false
        addSubview(stackView)

        NSLayoutConstraint.activate([
            stackView.topAnchor.constraint(equalTo: topAnchor),
            stackView.leadingAnchor.constraint(equalTo: leadingAnchor),
            stackView.trailingAnchor.constraint(equalTo: trailingAnchor),
            stackView.bottomAnchor.constraint(equalTo: bottomAnchor),
        ])

        label.text = "Email"
        label.font = .preferredFont(forTextStyle: .caption1)

        textField.placeholder = "Enter your email"
        textField.borderStyle = .roundedRect

        errorLabel.text = "Invalid email address"
        errorLabel.font = .preferredFont(forTextStyle: .caption2)
        errorLabel.textColor = .systemRed
        errorLabel.alpha = 0
    }

    func animate(to state: AnimationState) {
        switch state {
        case .enter:
            // Combine: scale up slightly + move up
            let scaleUp = CGAffineTransform(scaleX: 1.05, y: 1.05)
            let moveUp = CGAffineTransform(translationX: 0, y: -8)
            let combined = scaleUp.concatenating(moveUp)

            UIViewPropertyAnimator(duration: 0.3, dampingRatio: 0.8) {
                self.textField.transform = combined
                self.textField.layer.borderColor = UIColor.systemBlue.cgColor
                self.textField.layer.borderWidth = 2
                self.textField.layer.cornerRadius = 6
            }.startAnimation()

        case .exit:
            UIViewPropertyAnimator(duration: 0.2, curve: .easeOut) {
                self.textField.transform = .identity
                self.textField.layer.borderWidth = 0
            }.startAnimation()
        }
    }

    func showError() {
        // Shake animation using transform
        let shake = CAKeyframeAnimation(keyPath: "transform.translation.x")
        shake.timingFunction = CAMediaTimingFunction(name: .easeOut)
        shake.values = [-10, 10, -8, 8, -4, 4, 0]
        shake.duration = 0.4
        textField.layer.add(shake, forKey: "shake")

        UIViewPropertyAnimator(duration: 0.25, curve: .easeIn) {
            self.errorLabel.alpha = 1
        }.startAnimation()
    }

    func hideError() {
        UIViewPropertyAnimator(duration: 0.2, curve: .easeOut) {
            self.errorLabel.alpha = 0
        }.startAnimation()
    }
}
```

## Stack View Animation: Visibility, Alpha, Staggered

Animating `isHidden` on arranged subviews causes the stack view to redistribute space with animation.

```swift
import UIKit

class StackAnimationViewController: UIViewController {

    let stackView = UIStackView()
    var detailLabels: [UILabel] = []

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .systemBackground
        setupStack()
        setupToggleButton()
    }

    private func setupStack() {
        stackView.axis = .vertical
        stackView.spacing = 12
        stackView.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(stackView)

        NSLayoutConstraint.activate([
            stackView.centerYAnchor.constraint(equalTo: view.centerYAnchor),
            stackView.leadingAnchor.constraint(equalTo: view.leadingAnchor, constant: 24),
            stackView.trailingAnchor.constraint(equalTo: view.trailingAnchor, constant: -24),
        ])

        let titles = ["Account Details", "Payment Method", "Shipping Address", "Order Summary"]
        for title in titles {
            let label = UILabel()
            label.text = title
            label.font = .preferredFont(forTextStyle: .body)
            label.textAlignment = .center
            label.backgroundColor = .secondarySystemBackground
            label.layer.cornerRadius = 8
            label.clipsToBounds = true
            label.heightAnchor.constraint(equalToConstant: 50).isActive = true

            // Start hidden for animation
            label.isHidden = true
            label.alpha = 0

            stackView.addArrangedSubview(label)
            detailLabels.append(label)
        }
    }

    private func setupToggleButton() {
        let button = UIButton(type: .system)
        button.setTitle("Toggle Items", for: .normal)
        button.translatesAutoresizingMaskIntoConstraints = false
        button.addTarget(self, action: #selector(toggleTapped), for: .touchUpInside)
        view.addSubview(button)

        NSLayoutConstraint.activate([
            button.bottomAnchor.constraint(equalTo: view.safeAreaLayoutGuide.bottomAnchor, constant: -20),
            button.centerXAnchor.constraint(equalTo: view.centerXAnchor),
        ])
    }

    @objc private func toggleTapped() {
        let isCurrentlyHidden = detailLabels.first?.isHidden ?? true

        for (index, label) in detailLabels.enumerated() {
            // Stagger each label by 0.1 seconds
            let animator = UIViewPropertyAnimator(duration: 0.4, dampingRatio: 0.8) {
                label.isHidden = !isCurrentlyHidden
                label.alpha = isCurrentlyHidden ? 1.0 : 0.0
            }
            animator.startAnimation(afterDelay: Double(index) * 0.1)
        }
    }
}
```

## Summary of Key Patterns

| Technique                                   | What to Animate              | When to Use                           |
|---------------------------------------------|------------------------------|---------------------------------------|
| Constraint `.constant` + `layoutIfNeeded()` | Position, size               | Moving views relative to layout       |
| `CGAffineTransform`                         | Scale, rotation, translation | Visual effects without layout changes |
| `.concatenating()`                          | Multiple transforms          | Combining scale + translate, etc.     |
| Stack view `isHidden`                       | Visibility + redistribution  | Showing/hiding sections               |
| `startAnimation(afterDelay:)`               | Staggered timing             | Sequential reveal effects             |
| `addCompletion`                             | Chained sequences            | Step 1 finishes, then step 2          |
