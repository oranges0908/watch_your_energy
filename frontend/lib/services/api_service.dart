import 'package:dio/dio.dart';
import 'package:watch_your_energy/models/app_state.dart';
import 'package:watch_your_energy/models/project.dart';
import 'package:watch_your_energy/models/step.dart';

// Base URL can be overridden at build time:
//   flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
const String kApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://localhost:8000',
);

/// Abstract interface — makes the service mockable in tests.
abstract class ApiService {
  Future<AppState> getState();

  /// Returns updated AppState including step; also returns trigger (ignored by caller).
  Future<AppState> postSession();
  Future<AppState> patchEnergy(String mode);

  Future<List<ProjectModel>> getProjects();
  Future<AppState> postProject(String title, List<int> completedPositions);
  Future<AppState> patchActiveProject(String projectId);
  Future<ProjectDetail> getProjectDetail(String projectId);

  Future<AppState> postStepStart(String stepId);

  /// Returns new AppState. Caller can read feedbackMessage from a separate provider.
  Future<({AppState state, String? feedbackMessage})> postStepComplete(
      String stepId);

  Future<AppState> postStepSkip(String stepId);
  Future<AppState> postStepStuck(String stepId);
}

class DioApiService implements ApiService {
  DioApiService({Dio? dio})
      : _dio = dio ??
            Dio(BaseOptions(
              baseUrl: kApiBaseUrl,
              connectTimeout: const Duration(seconds: 10),
              receiveTimeout: const Duration(seconds: 30),
            ));

  final Dio _dio;

  // ── State ────────────────────────────────────────────────────────────────

  @override
  Future<AppState> getState() async {
    final resp = await _dio.get<Map<String, dynamic>>('/state');
    return AppState.fromJson(resp.data!);
  }

  @override
  Future<AppState> postSession() async {
    final resp = await _dio.post<Map<String, dynamic>>('/state/session');
    return _fromStepProjectResponse(resp.data!);
  }

  @override
  Future<AppState> patchEnergy(String mode) async {
    final resp = await _dio.patch<Map<String, dynamic>>(
      '/state/energy',
      data: {'mode': mode},
    );
    final data = resp.data!;
    return _fromStepProjectResponse(data,
        energyMode: data['energy_mode'] as String? ?? mode);
  }

  // ── Projects ─────────────────────────────────────────────────────────────

  @override
  Future<List<ProjectModel>> getProjects() async {
    final resp = await _dio.get<List<dynamic>>('/projects');
    return (resp.data as List)
        .map((e) => ProjectModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  @override
  Future<AppState> postProject(
      String title, List<int> completedPositions) async {
    final resp = await _dio.post<Map<String, dynamic>>(
      '/projects',
      data: {
        'title': title,
        'completed_block_positions': completedPositions,
      },
    );
    return _fromStepProjectResponse(resp.data!);
  }

  @override
  Future<AppState> patchActiveProject(String projectId) async {
    final resp = await _dio.patch<Map<String, dynamic>>(
      '/projects/$projectId/active',
    );
    return _fromStepProjectResponse(resp.data!);
  }

  @override
  Future<ProjectDetail> getProjectDetail(String projectId) async {
    final resp =
        await _dio.get<Map<String, dynamic>>('/projects/$projectId');
    final data = resp.data!;
    final project = ProjectModel.fromJson(data);
    final blocks = (data['blocks'] as List)
        .map((e) => BlockModel.fromJson(e as Map<String, dynamic>))
        .toList();
    return ProjectDetail(project: project, blocks: blocks);
  }

  // ── Steps ─────────────────────────────────────────────────────────────────

  @override
  Future<AppState> postStepStart(String stepId) async {
    final resp = await _dio.post<Map<String, dynamic>>(
      '/steps/start',
      data: {'step_id': stepId},
    );
    return _fromStepProjectResponse(resp.data!);
  }

  @override
  Future<({AppState state, String? feedbackMessage})> postStepComplete(
      String stepId) async {
    final resp = await _dio.post<Map<String, dynamic>>(
      '/steps/complete',
      data: {'step_id': stepId},
    );
    final data = resp.data!;
    return (
      state: _fromStepProjectResponse(data),
      feedbackMessage: data['feedback_message'] as String?,
    );
  }

  @override
  Future<AppState> postStepSkip(String stepId) async {
    final resp = await _dio.post<Map<String, dynamic>>(
      '/steps/skip',
      data: {'step_id': stepId},
    );
    return _fromStepProjectResponse(resp.data!);
  }

  @override
  Future<AppState> postStepStuck(String stepId) async {
    final resp = await _dio.post<Map<String, dynamic>>(
      '/steps/stuck',
      data: {'step_id': stepId},
    );
    return _fromStepProjectResponse(resp.data!);
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  /// Convert a {step, project, ...} response shape into AppState.
  /// The step-action endpoints don't return energy_mode/onboarding_complete,
  /// so we inject sensible defaults (caller can override with energyMode).
  static AppState _fromStepProjectResponse(
    Map<String, dynamic> data, {
    String energyMode = 'normal',
    bool onboardingComplete = true,
  }) {
    final stepData = data['step'] as Map<String, dynamic>?;
    final projectData = data['project'] as Map<String, dynamic>?;
    return AppState(
      step: stepData != null ? StepModel.fromJson(stepData) : null,
      project: projectData != null ? ProjectModel.fromJson(projectData) : null,
      energyMode: data['energy_mode'] as String? ?? energyMode,
      onboardingComplete:
          data['onboarding_complete'] as bool? ?? onboardingComplete,
    );
  }
}
