import SwiftUI

struct HomeView: View {
    @StateObject private var viewModel = HomeViewModel()

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 20) {
                    if let stats = viewModel.stats {
                        // Metrics Grid
                        LazyVGrid(columns: [
                            GridItem(.flexible()),
                            GridItem(.flexible())
                        ], spacing: 15) {
                            MetricCard(
                                title: "Total Workouts",
                                value: "\(stats.totalWorkouts)",
                                icon: "figure.walk"
                            )
                            MetricCard(
                                title: "Success Rate",
                                value: String(format: "%.1f%%", stats.successRate),
                                icon: "chart.line.uptrend.xyaxis"
                            )
                        }
                        .padding(.horizontal)

                        // Recent Achievements - Modified to show only 2 items horizontally
                        if !stats.recentAchievements.isEmpty {
                            VStack(alignment: .leading, spacing: 10) {
                                Text("Recent Achievements")
                                    .font(.headline)
                                    .padding(.horizontal)

                                LazyVGrid(columns: [
                                    GridItem(.flexible()),
                                    GridItem(.flexible())
                                ], spacing: 15) {
                                    ForEach(Array(stats.recentAchievements.prefix(2)), id: \.name) { achievement in
                                        AchievementCard(achievement: achievement)
                                    }
                                }
                                .padding(.horizontal)
                            }
                        }

                        // Training Load Status
                        VStack(alignment: .leading, spacing: 10) {
                            Text("Training Load Status")
                                .font(.headline)
                                .padding(.horizontal)

                            LazyVGrid(columns: [
                                GridItem(.flexible()),
                                GridItem(.flexible()),
                                GridItem(.flexible())
                            ], spacing: 15) {
                                LoadStatusCard(
                                    title: "Current Load",
                                    value: String(format: "%.1f", stats.trainingLoad.currentLoad),
                                    status: stats.trainingLoad.loadStatus
                                )
                                LoadStatusCard(
                                    title: "Recovery",
                                    value: "\(stats.trainingLoad.recoveryScore)%",
                                    status: stats.trainingLoad.recoveryStatus
                                )
                                LoadStatusCard(
                                    title: "Readiness",
                                    value: "\(stats.trainingLoad.readinessScore)%",
                                    status: stats.trainingLoad.readinessStatus
                                )
                            }
                            .padding(.horizontal)
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
            .navigationTitle("Dashboard")
            .refreshable {
                await viewModel.loadDashboard()
            }
            .task {
                await viewModel.loadDashboard()
            }
        }
    }
}

struct MetricCard: View {
    let title: String
    let value: String
    let icon: String

    var body: some View {
        VStack(spacing: 10) {
            Image(systemName: icon)
                .font(.title)
            Text(value)
                .font(.title2)
                .bold()
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
}

struct AchievementCard: View {
    let achievement: HomeViewModel.DashboardStats.Achievement

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("🏅 \(achievement.name)")
                .font(.headline)
                .lineLimit(1)
            Text(achievement.description)
                .font(.caption)
                .foregroundColor(.secondary)
                .lineLimit(2)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
}

struct LoadStatusCard: View {
    let title: String
    let value: String
    let status: String

    var body: some View {
        VStack(spacing: 8) {
            Text(title)
                .font(.caption)
                .foregroundColor(.secondary)
            Text(value)
                .font(.headline)
            Text(status)
                .font(.caption2)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(Color(.systemGray6))
        .cornerRadius(10)
    }
}

struct HomeView_Previews: PreviewProvider {
    static var previews: some View {
        HomeView()
    }
}