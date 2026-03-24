import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:watch_your_energy/providers/app_state_provider.dart';
import 'package:watch_your_energy/providers/execution_state_provider.dart';
import 'package:watch_your_energy/widgets/action_buttons.dart';
import 'package:watch_your_energy/widgets/completion_flash.dart';
import 'package:watch_your_energy/widgets/project_header.dart';
import 'package:watch_your_energy/widgets/step_card.dart';

class HomePage extends ConsumerWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncState = ref.watch(appStateProvider);
    final executionState = ref.watch(executionStateProvider);
    final notifier = ref.read(appStateProvider.notifier);

    final isLoading = asyncState.isLoading;
    final appState = asyncState.value; // null only on first load

    // First load with no cached data → full-screen spinner
    if (appState == null && isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    // Error with no cached data → error + retry
    if (asyncState.hasError && appState == null) {
      return Scaffold(
        body: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('加载失败: ${asyncState.error}'),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: () => ref.invalidate(appStateProvider),
                child: const Text('重试'),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      body: SafeArea(
        child: Stack(
          fit: StackFit.expand,
          children: [
            Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                ProjectHeader(project: appState?.project),
                const SizedBox(height: 16),
                // EnergyToggle — implemented in I7
                Expanded(
                  child: AnimatedStepCard(
                    step: appState?.step,
                    executionState: executionState,
                  ),
                ),
                ActionButtons(
                  executionState: executionState,
                  isLoading: isLoading,
                  onStart: () {
                    ref.read(executionStateProvider.notifier).state =
                        ExecutionState.executing;
                  },
                  onComplete: () async {
                    await notifier.onComplete();
                    ref.read(executionStateProvider.notifier).state =
                        ExecutionState.idle;
                  },
                  onSkip: () => notifier.onSkip(),
                  onStuck: () async {
                    await notifier.onStuck();
                    ref.read(executionStateProvider.notifier).state =
                        ExecutionState.idle;
                  },
                ),
              ],
            ),
            const CompletionFlash(),
          ],
        ),
      ),
    );
  }
}
