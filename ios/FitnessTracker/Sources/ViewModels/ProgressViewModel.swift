import Foundation

@MainActor
class ProgressViewModel: ObservableObject {
    @Published var progressData: ProgressData?
    @Published var selectedTimeRange: TimeRange = .month
    @Published var error: String?
    @Published var isLoading: Bool = false
    
    enum TimeRange: String, CaseIterable {
        case month = "1 Month"
        case threeMonths = "3 Months"
        case sixMonths = "6 Months"
        case year = "1 Year"
        case allTime = "All Time"
    }
    
    func loadProgress() async {
        isLoading = true
        do {
            let data: ProgressData = try await APIService.shared.performRequest(
                "/progress?range=\(selectedTimeRange.rawValue)",
                method: "GET"
            )
            self.progressData = data
            error = nil
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }
}
