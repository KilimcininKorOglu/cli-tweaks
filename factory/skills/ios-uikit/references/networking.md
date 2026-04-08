# Networking

## Service Layer Pattern

### Custom Error Enum

```swift
import Foundation

enum ServiceError: Error {
    case server(statusCode: Int)
    case parsing(underlying: Error)
    case general(underlying: Error)

    var localizedDescription: String {
        switch self {
        case .server(let statusCode):
            return "Server error with status code: \(statusCode)"
        case .parsing(let error):
            return "Parsing error: \(error.localizedDescription)"
        case .general(let error):
            return "Error: \(error.localizedDescription)"
        }
    }
}
```

### Service with Singleton Pattern

```swift
import Foundation

struct HistoryTransaction: Codable {
    let id: Int
    let amount: Decimal
    let description: String
    let date: Date
}

class HistoryService {

    static let shared = HistoryService()

    private let session: URLSession
    private let baseURL = "https://api.example.com/v1"

    private init(session: URLSession = .shared) {
        self.session = session
    }

    func fetchTransactions(
        completion: @escaping (Result<[HistoryTransaction], ServiceError>) -> Void
    ) {
        guard let url = URL(string: "\(baseURL)/transactions") else { return }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        session.dataTask(with: request) { data, response, error in
            // 1. Check for network error
            if let error = error {
                DispatchQueue.main.async {
                    completion(.failure(.general(underlying: error)))
                }
                return
            }

            // 2. Validate HTTP status code
            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                let statusCode = (response as? HTTPURLResponse)?.statusCode ?? -1
                DispatchQueue.main.async {
                    completion(.failure(.server(statusCode: statusCode)))
                }
                return
            }

            // 3. Parse JSON
            guard let data = data else {
                DispatchQueue.main.async {
                    completion(.failure(.server(statusCode: -1)))
                }
                return
            }

            do {
                let decoder = JSONDecoder()
                decoder.dateDecodingStrategy = .iso8601
                let transactions = try decoder.decode([HistoryTransaction].self, from: data)
                DispatchQueue.main.async {
                    completion(.success(transactions))
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(.parsing(underlying: error)))
                }
            }
        }.resume()
    }

    func postTransaction(
        _ transaction: HistoryTransaction,
        completion: @escaping (Result<Void, ServiceError>) -> Void
    ) {
        guard let url = URL(string: "\(baseURL)/transactions") else { return }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let encoder = JSONEncoder()
            encoder.dateEncodingStrategy = .iso8601
            request.httpBody = try encoder.encode(transaction)
        } catch {
            completion(.failure(.general(underlying: error)))
            return
        }

        session.dataTask(with: request) { _, response, error in
            if let error = error {
                DispatchQueue.main.async {
                    completion(.failure(.general(underlying: error)))
                }
                return
            }

            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                let statusCode = (response as? HTTPURLResponse)?.statusCode ?? -1
                DispatchQueue.main.async {
                    completion(.failure(.server(statusCode: statusCode)))
                }
                return
            }

            DispatchQueue.main.async {
                completion(.success(()))
            }
        }.resume()
    }
}
```

## ViewModel Bridge Pattern

The ViewModel receives raw data, transforms it, and exposes display-ready properties. The `didSet` on the input property triggers the transformation automatically.

```swift
import Foundation

struct TransactionViewModel {
    let title: String
    let amount: String
    let date: String
    let isCredit: Bool
}

class HistoryViewModel {

    // Input -- set from service response
    var transactions: [HistoryTransaction] = [] {
        didSet {
            displayItems = transactions.map { transform($0) }
        }
    }

    // Output -- read by the view controller
    private(set) var displayItems: [TransactionViewModel] = []

    private let currencyFormatter: NumberFormatter = {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.locale = Locale(identifier: "en_US")
        return formatter
    }()

    private let dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        return formatter
    }()

    private func transform(_ transaction: HistoryTransaction) -> TransactionViewModel {
        let isCredit = transaction.amount >= 0
        let formatted = currencyFormatter.string(from: transaction.amount as NSDecimalNumber) ?? "$0.00"

        return TransactionViewModel(
            title: transaction.description,
            amount: isCredit ? "+\(formatted)" : formatted,
            date: dateFormatter.string(from: transaction.date),
            isCredit: isCredit
        )
    }
}
```

### ViewController Usage

```swift
import UIKit

class HistoryViewController: UIViewController {

    let viewModel = HistoryViewModel()

    override func viewDidLoad() {
        super.viewDidLoad()
        fetchData()
    }

    private func fetchData() {
        HistoryService.shared.fetchTransactions { [weak self] result in
            // Already on main thread -- service dispatches to main
            switch result {
            case .success(let transactions):
                self?.viewModel.transactions = transactions
                self?.reloadUI()
            case .failure(let error):
                self?.showError(error)
            }
        }
    }

    private func reloadUI() {
        // viewModel.displayItems is ready to use
        for item in viewModel.displayItems {
            print("\(item.title): \(item.amount) on \(item.date)")
        }
    }

    private func showError(_ error: ServiceError) {
        let alert = UIAlertController(
            title: "Error",
            message: error.localizedDescription,
            preferredStyle: .alert
        )
        alert.addAction(UIAlertAction(title: "OK", style: .default))
        present(alert, animated: true)
    }
}
```

## Main Thread Dispatch

Always dispatch UI updates to the main thread. Network callbacks arrive on background threads.

```swift
// Inside a URLSession completion handler:
DispatchQueue.main.async {
    self.tableView.reloadData()
    self.activityIndicator.stopAnimating()
}
```

## Core Data Background Thread Pattern

```swift
import CoreData

class CoreDataManager {

    let persistentContainer: NSPersistentContainer

    init(container: NSPersistentContainer) {
        self.persistentContainer = container
    }

    /// Write on a background thread -- will not block the UI.
    func saveTransactions(_ transactions: [HistoryTransaction]) {
        persistentContainer.performBackgroundTask { context in
            for tx in transactions {
                let entity = TransactionEntity(context: context)
                entity.id = Int64(tx.id)
                entity.amount = tx.amount as NSDecimalNumber
                entity.desc = tx.description
                entity.date = tx.date
            }

            do {
                try context.save()
            } catch {
                print("Core Data save error: \(error)")
            }
        }
    }

    /// Read on the view context (main thread) for UI display.
    func fetchAllTransactions() -> [TransactionEntity] {
        let request: NSFetchRequest<TransactionEntity> = TransactionEntity.fetchRequest()
        request.sortDescriptors = [NSSortDescriptor(key: "date", ascending: false)]

        do {
            return try persistentContainer.viewContext.fetch(request)
        } catch {
            print("Core Data fetch error: \(error)")
            return []
        }
    }

    /// Synchronous background operation when you need to wait for the result.
    func countTransactions() -> Int {
        var count = 0
        persistentContainer.viewContext.performAndWait {
            let request: NSFetchRequest<TransactionEntity> = TransactionEntity.fetchRequest()
            count = (try? persistentContainer.viewContext.count(for: request)) ?? 0
        }
        return count
    }
}
```

## Testing Patterns

### Pattern 1: Simple (Naive) -- Direct Service Call

Tests hit the real network. Fast to write, but fragile and slow.

```swift
import XCTest

class SimpleNetworkTests: XCTestCase {

    func testFetchTransactions() {
        let expectation = expectation(description: "fetch")

        HistoryService.shared.fetchTransactions { result in
            switch result {
            case .success(let transactions):
                XCTAssertFalse(transactions.isEmpty)
            case .failure(let error):
                XCTFail("Unexpected error: \(error)")
            }
            expectation.fulfill()
        }

        waitForExpectations(timeout: 5)
    }
}
```

### Pattern 2: Medium (Recommended) -- Context Injection with URLProtocol

Inject a mock URLSession that returns controlled responses. No real network calls.

```swift
import XCTest

// Mock URLProtocol that returns predefined data
class MockURLProtocol: URLProtocol {

    static var mockData: Data?
    static var mockResponse: HTTPURLResponse?
    static var mockError: Error?

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        if let error = MockURLProtocol.mockError {
            client?.urlProtocol(self, didFailWithError: error)
        } else {
            if let response = MockURLProtocol.mockResponse {
                client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
            }
            if let data = MockURLProtocol.mockData {
                client?.urlProtocol(self, didLoad: data)
            }
        }
        client?.urlProtocolDidFinishLoading(self)
    }

    override func stopLoading() {}
}

// Testable service that accepts a URLSession
class TestableHistoryService {

    private let session: URLSession

    init(session: URLSession) {
        self.session = session
    }

    func fetchTransactions(
        completion: @escaping (Result<[HistoryTransaction], ServiceError>) -> Void
    ) {
        let url = URL(string: "https://api.example.com/v1/transactions")!
        session.dataTask(with: url) { data, response, error in
            if let error = error {
                completion(.failure(.general(underlying: error)))
                return
            }
            guard let httpResponse = response as? HTTPURLResponse,
                  (200...299).contains(httpResponse.statusCode) else {
                let code = (response as? HTTPURLResponse)?.statusCode ?? -1
                completion(.failure(.server(statusCode: code)))
                return
            }
            guard let data = data else {
                completion(.failure(.server(statusCode: -1)))
                return
            }
            do {
                let decoder = JSONDecoder()
                decoder.dateDecodingStrategy = .iso8601
                let items = try decoder.decode([HistoryTransaction].self, from: data)
                completion(.success(items))
            } catch {
                completion(.failure(.parsing(underlying: error)))
            }
        }.resume()
    }
}

class MediumNetworkTests: XCTestCase {

    var session: URLSession!
    var service: TestableHistoryService!

    override func setUp() {
        super.setUp()
        let config = URLSessionConfiguration.ephemeral
        config.protocolClasses = [MockURLProtocol.self]
        session = URLSession(configuration: config)
        service = TestableHistoryService(session: session)
    }

    func testFetchTransactionsSuccess() {
        // Arrange
        let json = """
        [{"id":1,"amount":42.50,"description":"Coffee","date":"2025-01-15T10:30:00Z"}]
        """
        MockURLProtocol.mockData = json.data(using: .utf8)
        MockURLProtocol.mockResponse = HTTPURLResponse(
            url: URL(string: "https://api.example.com")!,
            statusCode: 200,
            httpVersion: nil,
            headerFields: nil
        )
        MockURLProtocol.mockError = nil

        let expectation = expectation(description: "fetch")

        // Act
        service.fetchTransactions { result in
            // Assert
            switch result {
            case .success(let transactions):
                XCTAssertEqual(transactions.count, 1)
                XCTAssertEqual(transactions.first?.description, "Coffee")
            case .failure(let error):
                XCTFail("Expected success, got: \(error)")
            }
            expectation.fulfill()
        }

        waitForExpectations(timeout: 2)
    }

    func testFetchTransactionsServerError() {
        MockURLProtocol.mockData = nil
        MockURLProtocol.mockResponse = HTTPURLResponse(
            url: URL(string: "https://api.example.com")!,
            statusCode: 500,
            httpVersion: nil,
            headerFields: nil
        )
        MockURLProtocol.mockError = nil

        let expectation = expectation(description: "fetch")

        service.fetchTransactions { result in
            switch result {
            case .success:
                XCTFail("Expected failure")
            case .failure(let error):
                if case .server(let code) = error {
                    XCTAssertEqual(code, 500)
                } else {
                    XCTFail("Expected server error")
                }
            }
            expectation.fulfill()
        }

        waitForExpectations(timeout: 2)
    }
}
```

### Pattern 3: Complex -- Background/Main Thread Split

Test that Core Data operations run on the correct threads.

```swift
import XCTest
import CoreData

class CoreDataThreadTests: XCTestCase {

    var container: NSPersistentContainer!
    var manager: CoreDataManager!

    override func setUp() {
        super.setUp()

        // In-memory store for testing
        container = NSPersistentContainer(name: "Model")
        let description = NSPersistentStoreDescription()
        description.type = NSInMemoryStoreType
        container.persistentStoreDescriptions = [description]

        let loadExpectation = expectation(description: "load")
        container.loadPersistentStores { _, error in
            XCTAssertNil(error)
            loadExpectation.fulfill()
        }
        waitForExpectations(timeout: 2)

        manager = CoreDataManager(container: container)
    }

    func testSaveOnBackgroundAndFetchOnMain() {
        let saveExpectation = expectation(description: "save")

        // Save happens on a background thread
        container.performBackgroundTask { context in
            let entity = TransactionEntity(context: context)
            entity.id = 1
            entity.amount = NSDecimalNumber(value: 99.99)
            entity.desc = "Test"
            entity.date = Date()

            try? context.save()
            saveExpectation.fulfill()
        }

        waitForExpectations(timeout: 2)

        // Fetch happens on the main thread (view context)
        let results = manager.fetchAllTransactions()
        XCTAssertEqual(results.count, 1)
        XCTAssertEqual(results.first?.desc, "Test")
    }
}
```
