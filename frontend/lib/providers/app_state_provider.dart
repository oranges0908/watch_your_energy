import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:watch_your_energy/models/app_state.dart';
import 'package:watch_your_energy/providers/feedback_provider.dart';
import 'package:watch_your_energy/services/api_service.dart';

/// Provides the [ApiService] instance; override in tests with a mock.
final apiServiceProvider = Provider<ApiService>((ref) => DioApiService());

/// Core state notifier. Single source of truth for: current step, project, energy mode.
///
/// Pattern for all mutating actions:
///   1. Set state to AsyncLoading with previous data preserved.
///   2. Call API.
///   3. On success: set state to AsyncData(newState).
///   4. On failure: roll back to previous state (no crash).
class AppStateNotifier extends AsyncNotifier<AppState> {
  @override
  Future<AppState> build() async {
    final api = ref.read(apiServiceProvider);
    // Start a new session on first build (handles interruption detection).
    try {
      final sessionState = await api.postSession();
      // If session returned a state, use it. Otherwise fall back to getState.
      if (sessionState.hasStep || !sessionState.hasProject) {
        final fullState = await api.getState();
        // Merge: use energy_mode and onboarding_complete from getState.
        return AppState(
          step: fullState.step,
          project: fullState.project,
          energyMode: fullState.energyMode,
          onboardingComplete: fullState.onboardingComplete,
        );
      }
      return sessionState;
    } catch (_) {
      return api.getState();
    }
  }

  // ── Actions ───────────────────────────────────────────────────────────────

  Future<void> onStart() async {
    final stepId = state.value?.step?.id;
    if (stepId == null) return;
    await _mutate(() => ref.read(apiServiceProvider).postStepStart(stepId));
  }

  Future<void> onComplete() async {
    final stepId = state.value?.step?.id;
    if (stepId == null) return;

    final prev = state;
    state = const AsyncLoading<AppState>().copyWithPrevious(prev);

    try {
      final result =
          await ref.read(apiServiceProvider).postStepComplete(stepId);
      state = AsyncData(result.state);

      // Set feedback message and auto-clear after 2 seconds.
      if (result.feedbackMessage != null) {
        ref.read(feedbackMessageProvider.notifier).state =
            result.feedbackMessage;
        Future.delayed(const Duration(seconds: 2), () {
          // Only clear if the message hasn't been replaced.
          if (ref.read(feedbackMessageProvider) == result.feedbackMessage) {
            ref.read(feedbackMessageProvider.notifier).state = null;
          }
        });
      }
    } catch (_) {
      state = prev; // roll back
    }
  }

  Future<void> onSkip() async {
    final stepId = state.value?.step?.id;
    if (stepId == null) return;
    await _mutate(() => ref.read(apiServiceProvider).postStepSkip(stepId));
  }

  Future<void> onStuck() async {
    final stepId = state.value?.step?.id;
    if (stepId == null) return;
    await _mutate(() => ref.read(apiServiceProvider).postStepStuck(stepId));
  }

  Future<void> createProject(
      String title, List<int> completedPositions) async {
    await _mutate(
      () =>
          ref.read(apiServiceProvider).postProject(title, completedPositions),
    );
  }

  Future<void> switchProject(String projectId) async {
    await _mutate(
      () => ref.read(apiServiceProvider).patchActiveProject(projectId),
    );
  }

  Future<void> onEnergyToggle() async {
    final current = state.value?.energyMode ?? 'normal';
    final next = current == 'low' ? 'normal' : 'low';
    await _mutate(() => ref.read(apiServiceProvider).patchEnergy(next));
  }

  // ── Private ───────────────────────────────────────────────────────────────

  /// Generic mutate helper: loading → call → success or rollback.
  Future<void> _mutate(Future<AppState> Function() call) async {
    final prev = state;
    state = const AsyncLoading<AppState>().copyWithPrevious(prev);
    try {
      final next = await call();
      // Preserve energy_mode from current state if the response doesn't change it.
      final currentEnergyMode = state.value?.energyMode ?? prev.value?.energyMode ?? 'normal';
      state = AsyncData(next.copyWith(
        energyMode: next.energyMode != 'normal' ? next.energyMode : currentEnergyMode,
        onboardingComplete: next.onboardingComplete || (prev.value?.onboardingComplete ?? false),
      ));
    } catch (_) {
      state = prev; // roll back on any error
    }
  }
}

final appStateProvider =
    AsyncNotifierProvider<AppStateNotifier, AppState>(AppStateNotifier.new);
