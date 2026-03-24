import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:watch_your_energy/providers/app_state_provider.dart';

/// Skeleton home page — full UI implemented in I5.
/// Shows current step description (or loading/empty state).
class HomePage extends ConsumerWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncState = ref.watch(appStateProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('WatchYourEnergy')),
      body: asyncState.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (appState) {
          if (!appState.hasStep) {
            return const Center(child: Text('暂无待执行步骤'));
          }
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Text(
                appState.step!.description,
                style: Theme.of(context).textTheme.titleLarge,
                textAlign: TextAlign.center,
              ),
            ),
          );
        },
      ),
    );
  }
}
