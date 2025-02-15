import Foundation

struct ProgressData: Codable {
    let workoutHistory: [WorkoutHistory]
    let movements: [MovementProgress]
    let insights: [String]
    
    struct WorkoutHistory: Codable, Identifiable {
        let id: Int
        let date: Date
        let movement: String
        let weight: Double
        let reps: Int
        let totalVolume: Double
    }
    
    struct MovementProgress: Codable, Identifiable {
        let id: Int
        let name: String
        let currentLevel: String
        let personalBest: Double
        let progressToNext: Double
    }
}
