import SwiftUI

struct ProfileView: View {
    @StateObject private var viewModel = ProfileViewModel()
    @EnvironmentObject var authViewModel: AuthViewModel
    @State private var showingSaveSuccess = false
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Personal Information")) {
                    TextField("Display Name", text: Binding(
                        get: { viewModel.settings.displayName ?? "" },
                        set: { viewModel.settings.displayName = $0.isEmpty ? nil : $0 }
                    ))
                    
                    TextField("Email", text: Binding(
                        get: { viewModel.settings.email ?? "" },
                        set: { viewModel.settings.email = $0.isEmpty ? nil : $0 }
                    ))
                    .textContentType(.emailAddress)
                    .keyboardType(.emailAddress)
                }
                
                Section(header: Text("App Settings")) {
                    Toggle("Enable Notifications", isOn: $viewModel.settings.notifications)
                    Toggle("Sync with Health Kit", isOn: $viewModel.settings.healthKitSync)
                    Toggle("Dark Mode", isOn: $viewModel.settings.darkMode)
                }
                
                Section {
                    Button(action: {
                        Task {
                            await viewModel.saveProfile()
                            showingSaveSuccess = true
                        }
                    }) {
                        Text("Save Changes")
                    }
                }
                
                Section {
                    Button(action: {
                        authViewModel.logout()
                    }) {
                        Text("Logout")
                            .foregroundColor(.red)
                    }
                }
            }
            .navigationTitle("Profile")
            .alert("Success", isPresented: $showingSaveSuccess) {
                Button("OK", role: .cancel) { }
            } message: {
                Text("Profile settings saved successfully!")
            }
            .alert("Error", isPresented: .constant(viewModel.error != nil)) {
                Button("OK", role: .cancel) {
                    viewModel.error = nil
                }
            } message: {
                if let error = viewModel.error {
                    Text(error)
                }
            }
            .task {
                await viewModel.loadProfile()
            }
        }
    }
}

struct ProfileView_Previews: PreviewProvider {
    static var previews: some View {
        ProfileView()
            .environmentObject(AuthViewModel())
    }
}
