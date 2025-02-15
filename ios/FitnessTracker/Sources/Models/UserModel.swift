import Foundation

struct User: Codable, Identifiable {
    let id: Int
    let username: String
    let email: String?
    let isActive: Bool
    let createdAt: Date
    
    enum CodingKeys: String, CodingKey {
        case id
        case username
        case email
        case isActive = "is_active"
        case createdAt = "created_at"
    }
}

struct AuthToken: Codable {
    let accessToken: String
    let tokenType: String
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case tokenType = "token_type"
    }
}

struct LoginCredentials: Codable {
    let username: String
    let password: String
}

struct RegisterCredentials: Codable {
    let username: String
    let email: String?
    let password: String
}
