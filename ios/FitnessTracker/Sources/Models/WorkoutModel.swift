import Foundation

struct Workout: Codable, Identifiable {
    let id: Int
    let userId: Int
    let movementName: String
    let weight: Double
    let reps: Int
    let date: Date
    let notes: String?
    let completedSuccessfully: Bool
    
    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case movementName = "movement_name"
        case weight
        case reps
        case date
        case notes
        case completedSuccessfully = "completed_successfully"
    }
}

struct WorkoutCreate: Codable {
    let movementName: String
    let weight: Double
    let reps: Int
    let notes: String?
    let completedSuccessfully: Bool
    let date: Date?
    
    enum CodingKeys: String, CodingKey {
        case movementName = "movement_name"
        case weight
        case reps
        case notes
        case completedSuccessfully = "completed_successfully"
        case date
    }
}
