git clone <repository-url>
cd FitnessTracker
```

### 3. Open the Project
1. Double click `FitnessTracker.xcodeproj`, or
2. Open Xcode and select "Open a project or file"
3. Navigate to the FitnessTracker folder and select `FitnessTracker.xcodeproj`

### 4. Configure Development Team
1. In Xcode, select the FitnessTracker project in the navigator
2. Select the FitnessTracker target
3. Under "Signing & Capabilities":
   - Check "Automatically manage signing"
   - Select your team from the dropdown
   - If you don't have a team, sign in with your Apple ID

### 5. Run the App
1. Select an iOS simulator from the scheme menu (e.g., "iPhone 15 Pro")
2. Click the Run button (▶️) or press Cmd+R
3. The app will build and launch in the simulator

## Testing on Real Devices
To test on your iPhone or iPad:
1. Connect your iOS device to your Mac using a USB cable
2. Trust your Mac on your iOS device if prompted
3. In Xcode, select your device from the scheme menu
4. Trust your development certificate on your iOS device
5. Click Run to install and launch the app

## Development Guidelines
- Follow SwiftUI best practices
- Use MVVM architecture pattern
- Implement offline-first approach
- Follow Apple Human Interface Guidelines
- Test on multiple device sizes
- Use SwiftUI previews for rapid development

## Project Structure
```
FitnessTracker/
├── Sources/
│   ├── App/
│   │   └── FitnessTrackerApp.swift
│   ├── Models/
│   │   ├── WorkoutModel.swift
│   │   ├── UserModel.swift
│   │   └── AchievementModel.swift
│   ├── Views/
│   │   ├── Authentication/
│   │   ├── Workouts/
│   │   ├── Progress/
│   │   └── Settings/
│   ├── ViewModels/
│   ├── Services/
│   │   ├── APIService.swift
│   │   ├── AuthService.swift
│   │   └── StorageService.swift
│   └── Utilities/
├── Resources/
│   ├── Assets.xcassets/
│   └── Localizable.strings
├── Tests/
└── FitnessTracker.xcodeproj/