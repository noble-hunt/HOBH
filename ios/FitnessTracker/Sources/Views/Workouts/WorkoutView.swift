import SwiftUI

struct WorkoutView: View {
    @StateObject private var viewModel = WorkoutViewModel()
    @State private var showSuccessAlert = false
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("Movement Details")) {
                    Picker("Movement", selection: $viewModel.selectedMovement) {
                        ForEach(viewModel.movements) { movement in
                            Text(movement.name)
                                .tag(Optional(movement))
                        }
                    }
                    
                    HStack {
                        Text("Weight (kg)")
                        Spacer()
                        TextField("0.0", value: $viewModel.weight, format: .number)
                            .keyboardType(.decimalPad)
                            .multilineTextAlignment(.trailing)
                    }
                    
                    Stepper("Reps: \(viewModel.reps)", value: $viewModel.reps, in: 1...100)
                }
                
                Section(header: Text("Additional Info")) {
                    TextEditor(text: $viewModel.notes)
                        .frame(height: 100)
                    
                    Toggle("Completed Successfully", isOn: $viewModel.isSuccessful)
                }
                
                Section {
                    Button(action: {
                        Task {
                            await viewModel.logWorkout()
                            showSuccessAlert = true
                        }
                    }) {
                        Text("Log Workout")
                            .frame(maxWidth: .infinity)
                            .foregroundColor(.white)
                    }
                    .listRowBackground(Color.blue)
                }
            }
            .navigationTitle("Log Workout")
            .alert("Success", isPresented: $showSuccessAlert) {
                Button("OK", role: .cancel) { }
            } message: {
                Text("Workout logged successfully!")
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
                await viewModel.loadMovements()
            }
        }
    }
}

struct WorkoutView_Previews: PreviewProvider {
    static var previews: some View {
        WorkoutView()
    }
}
