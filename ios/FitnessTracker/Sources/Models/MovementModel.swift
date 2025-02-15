import Foundation

struct Movement: Codable, Identifiable {
    let id: Int
    let name: String
    let category: String
    
    enum CodingKeys: String, CodingKey {
        case id
        case name
        case category
    }
}

struct MovementLog: Codable {
    let movement: String
    let weight: Double
    let reps: Int
    let notes: String?
    let completedSuccessfully: Bool
    
    enum CodingKeys: String, CodingKey {
        case movement
        case weight
        case reps
        case notes
        case completedSuccessfully = "completed_successfully"
    }
}
