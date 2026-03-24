import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:watch_your_energy/models/app_state.dart';
import 'package:watch_your_energy/models/project.dart';
import 'package:watch_your_energy/models/step.dart';
import 'package:watch_your_energy/providers/app_state_provider.dart';
import 'package:watch_your_energy/providers/error_message_provider.dart';
import 'package:watch_your_energy/providers/feedback_provider.dart';
import 'package:watch_your_energy/services/api_service.dart';

// ── Mock ─────────────────────────────────────────────────────────────────────

class MockApiService extends Mock implements ApiService {}

// ── Fixtures ──────────────────────────────────────────────────────────────────

StepModel _makeStep({String id = 'step-1', String desc = '写项目1的第一句话'}) {
  return StepModel(
    id: id,
    description: desc,
    estimatedMin: 10,
    pattern: 'Continuation',
    stepType: 'Bootstrap',
    blockTitle: '项目1',
    energyLevel: 'normal',
  );
}

ProjectModel _makeProject({int progress = 0}) {
  return ProjectModel(id: 'proj-1', title: '优化简历', progressPct: progress);
}

AppState _makeState({
  String stepId = 'step-1',
  int progress = 0,
  String energyMode = 'normal',
}) {
  return AppState(
    step: _makeStep(id: stepId),
    project: _makeProject(progress: progress),
    energyMode: energyMode,
    onboardingComplete: true,
  );
}

// ── Helper ────────────────────────────────────────────────────────────────────

ProviderContainer makeContainer(MockApiService mock) {
  return ProviderContainer(overrides: [
    apiServiceProvider.overrideWithValue(mock),
  ]);
}

// ── Tests ─────────────────────────────────────────────────────────────────────

void main() {
  late MockApiService mockApi;
  late ProviderContainer container;

  setUp(() {
    mockApi = MockApiService();
    container = makeContainer(mockApi);
  });

  tearDown(() => container.dispose());

  // ── Build ────────────────────────────────────────────────────────────────

  test('build(): calls postSession + getState, emits AsyncData', () async {
    final expected = _makeState();
    when(() => mockApi.postSession()).thenAnswer((_) async => expected);
    when(() => mockApi.getState()).thenAnswer((_) async => expected);

    await container.read(appStateProvider.future);

    final result = container.read(appStateProvider).value;
    expect(result, isNotNull);
    expect(result!.step?.id, 'step-1');
  });

  test('build(): falls back to getState when postSession throws', () async {
    final expected = _makeState();
    when(() => mockApi.postSession()).thenThrow(Exception('network error'));
    when(() => mockApi.getState()).thenAnswer((_) async => expected);

    await container.read(appStateProvider.future);

    final result = container.read(appStateProvider).value;
    expect(result?.step?.id, 'step-1');
  });

  // ── onComplete ───────────────────────────────────────────────────────────

  test('onComplete(): sets loading → calls postStepComplete → updates state', () async {
    final initialState = _makeState(stepId: 'step-1', progress: 0);
    final nextState = _makeState(stepId: 'step-2', progress: 20);

    when(() => mockApi.postSession()).thenAnswer((_) async => initialState);
    when(() => mockApi.getState()).thenAnswer((_) async => initialState);
    when(() => mockApi.postStepComplete('step-1')).thenAnswer(
      (_) async => (state: nextState, feedbackMessage: '项目1已推进'),
    );

    await container.read(appStateProvider.future);

    await container.read(appStateProvider.notifier).onComplete();

    final result = container.read(appStateProvider).value;
    expect(result?.step?.id, 'step-2');
    expect(result?.project?.progressPct, 20);
  });

  test('onComplete(): sets feedbackMessageProvider', () async {
    final initialState = _makeState(stepId: 'step-1');
    final nextState = _makeState(stepId: 'step-2');

    when(() => mockApi.postSession()).thenAnswer((_) async => initialState);
    when(() => mockApi.getState()).thenAnswer((_) async => initialState);
    when(() => mockApi.postStepComplete('step-1')).thenAnswer(
      (_) async => (state: nextState, feedbackMessage: '项目1已推进'),
    );

    await container.read(appStateProvider.future);
    await container.read(appStateProvider.notifier).onComplete();

    expect(container.read(feedbackMessageProvider), '项目1已推进');
  });

  // ── onSkip ───────────────────────────────────────────────────────────────

  test('onSkip(): calls postStepSkip and updates state to new step', () async {
    final initialState = _makeState(stepId: 'step-1');
    final nextState = _makeState(stepId: 'step-skip');

    when(() => mockApi.postSession()).thenAnswer((_) async => initialState);
    when(() => mockApi.getState()).thenAnswer((_) async => initialState);
    when(() => mockApi.postStepSkip('step-1'))
        .thenAnswer((_) async => nextState);

    await container.read(appStateProvider.future);
    await container.read(appStateProvider.notifier).onSkip();

    final result = container.read(appStateProvider).value;
    expect(result?.step?.id, 'step-skip');
  });

  // ── onStuck ──────────────────────────────────────────────────────────────

  test('onStuck(): calls postStepStuck', () async {
    final initialState = _makeState(stepId: 'step-1');
    final nextState = _makeState(stepId: 'step-stuck');

    when(() => mockApi.postSession()).thenAnswer((_) async => initialState);
    when(() => mockApi.getState()).thenAnswer((_) async => initialState);
    when(() => mockApi.postStepStuck('step-1'))
        .thenAnswer((_) async => nextState);

    await container.read(appStateProvider.future);
    await container.read(appStateProvider.notifier).onStuck();

    final result = container.read(appStateProvider).value;
    expect(result?.step?.id, 'step-stuck');
  });

  // ── API failure → rollback ───────────────────────────────────────────────

  test('onSkip(): rolls back to previous state on API error', () async {
    final initialState = _makeState(stepId: 'step-1');

    when(() => mockApi.postSession()).thenAnswer((_) async => initialState);
    when(() => mockApi.getState()).thenAnswer((_) async => initialState);
    when(() => mockApi.postStepSkip('step-1'))
        .thenThrow(Exception('server error'));

    await container.read(appStateProvider.future);
    await container.read(appStateProvider.notifier).onSkip();

    // State should be rolled back, not null, not error
    final state = container.read(appStateProvider);
    expect(state.hasError, isFalse);
    expect(state.value?.step?.id, 'step-1');
  });

  test('onComplete(): rolls back on API error, does not crash', () async {
    final initialState = _makeState(stepId: 'step-1');

    when(() => mockApi.postSession()).thenAnswer((_) async => initialState);
    when(() => mockApi.getState()).thenAnswer((_) async => initialState);
    when(() => mockApi.postStepComplete('step-1'))
        .thenThrow(Exception('timeout'));

    await container.read(appStateProvider.future);
    await container.read(appStateProvider.notifier).onComplete();

    final state = container.read(appStateProvider);
    expect(state.hasError, isFalse);
    expect(state.value?.step?.id, 'step-1');
  });

  // ── onEnergyToggle ───────────────────────────────────────────────────────

  test('onEnergyToggle(): switches normal → low', () async {
    final initialState = _makeState(energyMode: 'normal');
    final lowState = AppState(
      step: _makeStep(),
      project: _makeProject(),
      energyMode: 'low',
      onboardingComplete: true,
    );

    when(() => mockApi.postSession()).thenAnswer((_) async => initialState);
    when(() => mockApi.getState()).thenAnswer((_) async => initialState);
    when(() => mockApi.patchEnergy('low')).thenAnswer((_) async => lowState);

    await container.read(appStateProvider.future);
    await container.read(appStateProvider.notifier).onEnergyToggle();

    final result = container.read(appStateProvider).value;
    expect(result?.energyMode, 'low');
  });

  // ── archiveProject ────────────────────────────────────────────────────────

  test('archiveProject(): calls deleteProject + getState, updates state',
      () async {
    final initialState = _makeState(stepId: 'step-1');
    final afterArchiveState = _makeState(stepId: 'step-2', progress: 0);

    var getStateCallCount = 0;
    when(() => mockApi.postSession()).thenAnswer((_) async => initialState);
    when(() => mockApi.getState()).thenAnswer((_) async {
      return getStateCallCount++ == 0 ? initialState : afterArchiveState;
    });
    when(() => mockApi.deleteProject('proj-1')).thenAnswer((_) async {});

    await container.read(appStateProvider.future);
    await container.read(appStateProvider.notifier).archiveProject('proj-1');

    verify(() => mockApi.deleteProject('proj-1')).called(1);
    final result = container.read(appStateProvider).value;
    expect(result?.step?.id, 'step-2');
  });

  // ── errorMessageProvider ──────────────────────────────────────────────────

  test('API error in _mutate → errorMessageProvider set to 网络异常', () async {
    final initialState = _makeState(stepId: 'step-1');

    when(() => mockApi.postSession()).thenAnswer((_) async => initialState);
    when(() => mockApi.getState()).thenAnswer((_) async => initialState);
    when(() => mockApi.postStepSkip('step-1'))
        .thenThrow(Exception('network error'));

    await container.read(appStateProvider.future);
    await container.read(appStateProvider.notifier).onSkip();

    expect(container.read(errorMessageProvider), '网络异常，请重试');
    // State rolled back
    expect(container.read(appStateProvider).value?.step?.id, 'step-1');
  });

  test('archiveProject() error → errorMessageProvider set', () async {
    final initialState = _makeState(stepId: 'step-1');

    when(() => mockApi.postSession()).thenAnswer((_) async => initialState);
    when(() => mockApi.getState()).thenAnswer((_) async => initialState);
    when(() => mockApi.deleteProject('proj-1'))
        .thenThrow(Exception('server error'));

    await container.read(appStateProvider.future);
    await container.read(appStateProvider.notifier).archiveProject('proj-1');

    expect(container.read(errorMessageProvider), '网络异常，请重试');
    expect(container.read(appStateProvider).value?.step?.id, 'step-1');
  });
}
