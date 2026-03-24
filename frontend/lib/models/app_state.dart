import 'package:watch_your_energy/models/step.dart';
import 'package:watch_your_energy/models/project.dart';

class AppState {
  final StepModel? step;
  final ProjectModel? project;
  final String energyMode;
  final bool onboardingComplete;

  const AppState({
    required this.step,
    required this.project,
    required this.energyMode,
    required this.onboardingComplete,
  });

  bool get isLowEnergy => energyMode == 'low';
  bool get hasStep => step != null;
  bool get hasProject => project != null;

  factory AppState.fromJson(Map<String, dynamic> json) {
    final stepJson = json['step'] as Map<String, dynamic>?;
    final projectJson = json['project'] as Map<String, dynamic>?;
    return AppState(
      step: stepJson != null ? StepModel.fromJson(stepJson) : null,
      project: projectJson != null ? ProjectModel.fromJson(projectJson) : null,
      energyMode: json['energy_mode'] as String? ?? 'normal',
      onboardingComplete: json['onboarding_complete'] as bool? ?? false,
    );
  }

  /// Return a copy with specific fields replaced.
  AppState copyWith({
    StepModel? step,
    ProjectModel? project,
    String? energyMode,
    bool? onboardingComplete,
    bool clearStep = false,
  }) {
    return AppState(
      step: clearStep ? null : (step ?? this.step),
      project: project ?? this.project,
      energyMode: energyMode ?? this.energyMode,
      onboardingComplete: onboardingComplete ?? this.onboardingComplete,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is AppState &&
          step == other.step &&
          project == other.project &&
          energyMode == other.energyMode &&
          onboardingComplete == other.onboardingComplete;

  @override
  int get hashCode => Object.hash(step, project, energyMode, onboardingComplete);
}
