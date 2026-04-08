---
name: ios-uikit
description: >
  This skill MUST be invoked when the user says "UIKit", "iOS geliştirme",
  "programmatic UI", "table view", "collection view", "Auto Layout",
  "UIViewController", "UINavigationController", "Core Animation",
  "UIKit review", "UIKit build", "iOS view controller", "UIKit pattern",
  "programmatic layout", or any variation requesting UIKit development,
  review, or improvement. Covers programmatic UIKit with Auto Layout,
  table/collection views, navigation, animation, networking, architecture,
  and 20 reference documents with production-ready patterns.
argument-hint: "[review | build | improve]"
---

# Programmatic UIKit Development

Build, review, and improve programmatic UIKit applications following production-ready patterns. All UI is built in code — no Storyboards.

## Usage

```bash
/ios-uikit review     # Review existing UIKit code for issues
/ios-uikit build      # Implement new UIKit feature
/ios-uikit improve    # Modernize existing UIKit code
/ios-uikit            # Auto-detect mode from context
```

## Operating Rules

- All UI built **programmatically**. Always set `translatesAutoresizingMaskIntoConstraints = false`.
- Prefer `NSLayoutConstraint.activate([...])` for batch constraint activation.
- Organize view controller code with extensions: separate `style()`, `layout()`, and protocol conformances.
- Use factory functions for repetitive UI element creation.
- Use `weak` references for delegates and `[weak self]` in closures to prevent retain cycles.
- Prefer `async/await` for new code; `Result<Success, Error>` for completion handler APIs.
- Always dispatch UI updates to the main thread — use `@MainActor` or `MainActor.run {}`.
- Extract custom views flush to their container; parent manages spacing.
- Use child view controllers for complex, self-contained screen sections.
- Consult relevant reference files before implementing any topic.

## Modes

### Review Mode (`/ios-uikit review`)

1. Read the code under review and identify which topics apply
2. Run the Topic Router below for each relevant topic
3. Check for retain cycles (missing `weak` delegates, missing `[weak self]`)
4. Verify Auto Layout completeness (unambiguous constraints, no warnings)
5. Flag deprecated patterns (e.g., manual `beginUpdates`/`endUpdates` when Diffable is available)
6. Check for missing `@MainActor` on UI-updating async code
7. Flag completion handler patterns where async/await would be cleaner

### Build Mode (`/ios-uikit build`)

1. Design data flow first: identify service, view model, view controller, and view layers
2. Structure views for composition (extracted views + child view controllers)
3. Apply correct animation patterns (constraint-based, Core Animation, or UIView)
4. Use protocol-delegate for sustained relationships; closures for one-shot callbacks
5. Add proper loading/error states
6. Include accessibility identifiers and VoiceOver support

### Improve Mode (`/ios-uikit improve`)

1. Audit current implementation against the Topic Router topics
2. Extract large view controllers into child VCs and custom views
3. Replace inline UI creation with factory functions
4. Migrate legacy table/collection view data sources to Diffable where appropriate
5. Migrate completion handlers to async/await where possible
6. Add `@MainActor` annotations to ViewModel and UI-updating code
7. Add proper error handling with `Result` types or throws

## Topic Router

Consult the reference file for each topic relevant to the current task:

| Topic                  | Reference                              |
|------------------------|----------------------------------------|
| UITableView            | `references/uitableview.md`            |
| UICollectionView       | `references/uicollectionview.md`       |
| UINavigationController | `references/uinavigationcontroller.md` |
| UIScrollView           | `references/uiscrollview.md`           |
| Core Animation         | `references/core-animation.md`         |
| Core Graphics          | `references/core-graphics.md`          |
| Auto Layout Animation  | `references/auto-layout-animation.md`  |
| Communication Patterns | `references/communication-patterns.md` |
| Architecture Patterns  | `references/architecture-patterns.md`  |
| View Extraction        | `references/view-extraction.md`        |
| Navigation Patterns    | `references/navigation-patterns.md`    |
| Design Patterns (UI)   | `references/design-patterns.md`        |
| Networking             | `references/networking.md`             |
| Factory Functions      | `references/factory-patterns.md`       |
| Nib / XIB Patterns     | `references/nib-patterns.md`           |
| NSAttributedString     | `references/nsattributedstring.md`     |
| Gesture Recognizers    | `references/gesture-recognizers.md`    |
| Custom Controls        | `references/custom-controls.md`        |
| Currency Formatting    | `references/currency-formatting.md`    |
| Deep Linking           | `references/deep-linking.md`           |

## Correctness Checklist

Hard rules — violations are always bugs:

### Layout
- [ ] Every programmatic view sets `translatesAutoresizingMaskIntoConstraints = false`
- [ ] `NSLayoutConstraint.activate()` is used instead of `isActive = true` one-by-one
- [ ] Factory functions return views with `translatesAutoresizingMaskIntoConstraints` already `false`
- [ ] Custom views define `intrinsicContentSize` when they have a natural size

### Memory
- [ ] Delegates are declared `weak var delegate: SomeDelegate?`
- [ ] Async closures capture `[weak self]` when referencing the owning object
- [ ] Combine subscriptions stored in `Set<AnyCancellable>` with `store(in:)`

### Table / Collection Views
- [ ] `performBatchUpdates` used (not `beginUpdates`/`endUpdates`) for iOS 11+
- [ ] Diffable data source items conform to `Hashable` with stable identifiers
- [ ] Cell registration uses `UICollectionView.CellRegistration` or `register(_:forCellWithReuseIdentifier:)`

### Threading
- [ ] UI updates from async callbacks dispatched to `DispatchQueue.main` or use `@MainActor`
- [ ] `async` functions that update UI are marked `@MainActor`
- [ ] Core Data background work uses `performBackgroundTask` or `perform`

### Child View Controllers
- [ ] Follow 3-step lifecycle: `addChild()`, `addSubview()`, `didMove(toParent:)`
- [ ] Removal: `willMove(toParent: nil)`, `removeFromSuperview()`, `removeFromParent()`

### Animation
- [ ] Core Animation model layer updated after animation to persist final state
- [ ] Bounds-dependent layers (shadows, gradients) set in `viewDidLayoutSubviews`

### Networking
- [ ] Prefer `async/await` URLSession APIs for new code
- [ ] Completion handler APIs use `Result<T, Error>` return type
- [ ] Network tasks stored for cancellation support

## Quick Diagnostics

| Symptom | Likely Cause | Reference |
|---------|-------------|-----------|
| View doesn't appear | Missing `translatesAutoresizingMaskIntoConstraints = false` | `references/view-extraction.md` |
| Table view crashes on insert | Data source count mismatch with batch updates | `references/uitableview.md` |
| Animation snaps to final state | Model layer not updated after CA animation | `references/core-animation.md` |
| Retain cycle / memory leak | Missing `weak` on delegate or `[weak self]` | `references/communication-patterns.md` |
| Scroll view doesn't scroll | Missing content size or broken constraint chain | `references/uiscrollview.md` |
| Shadow clipped by view | `masksToBounds = true` on layer | `references/core-animation.md` |
| Gradient/shadow wrong size | Set bounds-dependent layers in `viewDidLayoutSubviews` | `references/core-animation.md` |
| Collection view empty | Forgot to register cell or data source nil | `references/uicollectionview.md` |
| Core Data threading crash | Accessing managed object on wrong queue | `references/networking.md` |
| Nav bar title missing | Not setting `title` or `navigationItem.title` | `references/uinavigationcontroller.md` |
| Async callback UI freeze | Missing `@MainActor` or `DispatchQueue.main` dispatch | `references/architecture-patterns.md` |
| Combine subscription no fire | Subscriber deallocated — store in `cancellables` | `references/communication-patterns.md` |

## Modern Swift Notes

When working with UIKit in modern Swift (2025+):

- **async/await** is preferred over completion handlers for new networking code
- **@MainActor** replaces manual `DispatchQueue.main.async` for UI thread safety
- **Combine** is available for reactive data binding (alternative to delegate/closure patterns)
- **Diffable Data Source** is the standard for table/collection view data management
- **UICollectionViewCompositionalLayout** replaces manual flow layout calculations
- **UIViewPropertyAnimator** provides interruptible, scrubbable animations
- Completion handlers remain valid for existing codebases — do not force-migrate without reason
