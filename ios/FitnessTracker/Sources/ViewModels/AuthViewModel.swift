import Foundation

@MainActor
class AuthViewModel: ObservableObject {
    @Published var isAuthenticated = false
    @Published var error: String?
    
    func login(username: String, password: String) async {
        do {
            let credentials = LoginCredentials(username: username, password: password)
            let token: AuthToken = try await APIService.shared.performRequest(
                "/auth/login",
                method: "POST",
                body: credentials
            )
            APIService.shared.setAuthToken(token.accessToken)
            isAuthenticated = true
            error = nil
        } catch {
            isAuthenticated = false
            error = error.localizedDescription
        }
    }
    
    func register(username: String, email: String?, password: String) async {
        do {
            let credentials = RegisterCredentials(username: username, email: email, password: password)
            let _: User = try await APIService.shared.performRequest(
                "/auth/register",
                method: "POST",
                body: credentials
            )
            // After successful registration, login automatically
            await login(username: username, password: password)
        } catch {
            isAuthenticated = false
            error = error.localizedDescription
        }
    }
    
    func logout() {
        APIService.shared.clearAuthToken()
        isAuthenticated = false
        error = nil
    }
}
