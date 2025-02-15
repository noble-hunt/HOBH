import SwiftUI
import Charts

struct ProgressView: View {
    @StateObject private var viewModel = ProgressViewModel()
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    // Time Range Picker
                    Picker("Time Range", selection: $viewModel.selectedTimeRange) {
                        ForEach(ProgressViewModel.TimeRange.allCases, id: \.self) { range in
                            Text(range.rawValue).tag(range)
                        }
                    }
                    .pickerStyle(.segmented)
                    .padding(.horizontal)
                    .onChange(of: viewModel.selectedTimeRange) { _ in
                        Task {
                            await viewModel.loadProgress()
                        }
                    }
                    
                    if let progressData = viewModel.progressData {
                        // Progress Chart
                        VStack(alignment: .leading) {
                            Text("Workout Progress")
                                .font(.headline)
                                .padding(.horizontal)
                            
                            Chart {
                                ForEach(progressData.workoutHistory) { workout in
                                    LineMark(
                                        x: .value("Date", workout.date),
                                        y: .value("Weight", workout.weight)
                                    )
                                }
                            }
                            .frame(height: 200)
                            .padding()
                        }
                        
                        // Movement Progress
                        VStack(alignment: .leading) {
                            Text("Movement Progress")
                                .font(.headline)
                                .padding(.horizontal)
                            
                            ForEach(progressData.movements) { movement in
                                MovementProgressCard(movement: movement)
                                    .padding(.horizontal)
                            }
                        }
                        
                        // Insights
                        if !progressData.insights.isEmpty {
                            VStack(alignment: .leading) {
                                Text("Training Insights")
                                    .font(.headline)
                                    .padding(.horizontal)
                                
                                ForEach(progressData.insights, id: \.self) { insight in
                                    InsightCard(text: insight)
                                        .padding(.horizontal)
                                }
                            }
                        }
                    } else if viewModel.isLoading {
                        ProgressView()
                    } else if let error = viewModel.error {
                        Text(error)
                            .foregroundColor(.red)
                    }
                }
                .padding(.vertical)
            }
            .navigationTitle("Progress")
            .task {
                await viewModel.loadProgress()
            }
        }
    }
}

struct MovementProgressCard: View {
    let movement: ProgressData.MovementProgress
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(movement.name)
                .font(.headline)
            Text("Current Level: \(movement.currentLevel)")
                .font(.subheadline)
            Text("Personal Best: \(String(format: "%.1f", movement.personalBest))kg")
                .font(.subheadline)
            
            // Progress Bar
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    Rectangle()
                        .frame(width: geometry.size.width, height: 8)
                        .opacity(0.3)
                        .foregroundColor(.gray)
                    
                    Rectangle()
                        .frame(width: geometry.size.width * movement.progressToNext / 100, height: 8)
                        .foregroundColor(.blue)
                }
                .cornerRadius(4)
            }
            .frame(height: 8)
            
            Text("\(Int(movement.progressToNext))% to next level")
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
}

struct InsightCard: View {
    let text: String
    
    var body: some View {
        Text(text)
            .padding()
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color(.systemGray6))
            .cornerRadius(10)
    }
}

struct ProgressView_Previews: PreviewProvider {
    static var previews: some View {
        ProgressView()
    }
}
