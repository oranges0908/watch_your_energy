import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:watch_your_energy/providers/app_state_provider.dart';

/// Two ChoiceChips — ⚡ 正常 / 🌙 低能量.
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
                label: const Text('⚡ 正常'),
                selected: !isLow,
                onSelected: isLoading
                    ? null
                    : (selected) {
                        if (selected && isLow) notifier.onEnergyToggle();
                      },
              ),
              const SizedBox(width: 8),
              ChoiceChip(
                label: const Text('🌙 低能量'),
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
                '已切换到低能量模式 · 轻量但有进展',
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
