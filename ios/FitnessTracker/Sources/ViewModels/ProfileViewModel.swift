import Foundation

struct ProfileSettings: Codable {
    var displayName: String?
    var email: String?
    var notifications: Bool
    var healthKitSync: Bool
    var darkMode: Bool
}

@MainActor
class ProfileViewModel: ObservableObject {
    @Published var settings = ProfileSettings(
        displayName: nil,
        email: nil,
        notifications: true,
        healthKitSync: false,
        darkMode: false
    )
    @Published var error: String?
    
    func loadProfile() async {
        do {
            let settings: ProfileSettings = try await APIService.shared.performRequest(
                "/profile/settings",
                method: "GET"
            )
            self.settings = settings
            error = nil
        } catch {
            self.error = error.localizedDescription
        }
    }
    
    func saveProfile() async {
        do {
            let _: ProfileSettings = try await APIService.shared.performRequest(
                "/profile/settings",
                method: "PUT",
                body: settings
            )
            error = nil
        } catch {
            self.error = error.localizedDescription
        }
    }
}
