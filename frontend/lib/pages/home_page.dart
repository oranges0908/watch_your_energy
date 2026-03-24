import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:watch_your_energy/providers/app_state_provider.dart';
import 'package:watch_your_energy/providers/error_message_provider.dart';
import 'package:watch_your_energy/providers/execution_state_provider.dart';
import 'package:watch_your_energy/widgets/action_buttons.dart';
import 'package:watch_your_energy/widgets/completion_flash.dart';
import 'package:watch_your_energy/widgets/energy_toggle.dart';
import 'package:watch_your_energy/widgets/project_header.dart';
import 'package:watch_your_energy/widgets/project_sidebar.dart';
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

    // Show SnackBar on network errors; clear after display.
    ref.listen(errorMessageProvider, (_, message) {
      if (message == null) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          duration: const Duration(seconds: 3),
        ),
      );
      ref.read(errorMessageProvider.notifier).state = null;
    });

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

    // No project → redirect to create page
    if (appState != null && !appState.hasProject) {
      Future.microtask(() {
        if (context.mounted) context.go('/create');
      });
      return const Scaffold(body: SizedBox.shrink());
    }

    return Scaffold(
      drawer: const ProjectSidebar(),
      body: SafeArea(
        child: Builder(
          builder: (ctx) => Stack(
            fit: StackFit.expand,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  ProjectHeader(
                    project: appState?.project,
                    onSwitch: () => Scaffold.of(ctx).openDrawer(),
                    onViewProgress: () => ctx.push('/progress'),
                  ),
                  const EnergyToggle(),
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
      ),
    );
  }
}
