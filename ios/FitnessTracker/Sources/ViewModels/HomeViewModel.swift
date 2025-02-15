import Foundation

struct DashboardStats: Codable {
    let totalWorkouts: Int
    let successRate: Double
    let recentAchievements: [Achievement]
    let trainingLoad: TrainingLoad
    
    struct Achievement: Codable {
        let name: String
        let description: String
    }
    
    struct TrainingLoad: Codable {
        let currentLoad: Double
        let recoveryScore: Int
        let readinessScore: Int
        let loadStatus: String
        let recoveryStatus: String
        let readinessStatus: String
    }
}

@MainActor
class HomeViewModel: ObservableObject {
    @Published var stats: DashboardStats?
    @Published var error: String?
    @Published var isLoading: Bool = false
    
    func loadDashboard() async {
        isLoading = true
        do {
            let stats: DashboardStats = try await APIService.shared.performRequest(
                "/dashboard",
                method: "GET"
            )
            self.stats = stats
            error = nil
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }
}
