import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:watch_your_energy/providers/app_state_provider.dart';

/// Two ChoiceChips — ⚡ Normal / 🌙 Low energy.
/// Shows a hint text when low-energy mode is active.
/// Disabled during API loading.
class EnergyToggle extends ConsumerWidget {
  const EnergyToggle({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncState = ref.watch(appStateProvider);
    final isLoading = asyncState.isLoading;
    final isLow = asyncState.value?.isLowEnergy ?? false;
    final notifier = ref.read(appStateProvider.notifier);

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 4),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              ChoiceChip(
                label: const Text('⚡ Normal'),
                selected: !isLow,
                onSelected: isLoading
                    ? null
                    : (selected) {
                        if (selected && isLow) notifier.onEnergyToggle();
                      },
              ),
              const SizedBox(width: 8),
              ChoiceChip(
                label: const Text('🌙 Low energy'),
                selected: isLow,
                onSelected: isLoading
                    ? null
                    : (selected) {
                        if (selected && !isLow) notifier.onEnergyToggle();
                      },
              ),
              if (isLoading) ...[
                const SizedBox(width: 8),
                const SizedBox(
                  height: 16,
                  width: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              ],
            ],
          ),
          if (isLow)
            Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Text(
                'Low energy mode · light steps, still making progress',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.grey,
                    ),
              ),
            ),
        ],
      ),
    );
  }
}
