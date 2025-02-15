import Foundation

@MainActor
class WorkoutViewModel: ObservableObject {
    @Published var movements: [Movement] = []
    @Published var selectedMovement: Movement?
    @Published var weight: Double = 0
    @Published var reps: Int = 0
    @Published var notes: String = ""
    @Published var isSuccessful: Bool = true
    @Published var error: String?
    @Published var isLoading: Bool = false
    
    func loadMovements() async {
        isLoading = true
        do {
            let movements: [Movement] = try await APIService.shared.performRequest(
                "/movements",
                method: "GET"
            )
            self.movements = movements
            error = nil
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }
    
    func logWorkout() async {
        guard let movement = selectedMovement else {
            error = "Please select a movement"
            return
        }
        
        let log = MovementLog(
            movement: movement.name,
            weight: weight,
            reps: reps,
            notes: notes.isEmpty ? nil : notes,
            completedSuccessfully: isSuccessful
        )
        
        do {
            let _: WorkoutResponse = try await APIService.shared.performRequest(
                "/workouts",
                method: "POST",
                body: log
            )
            // Reset form
            self.weight = 0
            self.reps = 0
            self.notes = ""
            self.isSuccessful = true
            self.error = nil
        } catch {
            self.error = error.localizedDescription
        }
    }
}
