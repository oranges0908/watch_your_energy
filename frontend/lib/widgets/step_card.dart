import 'package:flutter/material.dart';
import 'package:watch_your_energy/models/step.dart';
import 'package:watch_your_energy/providers/execution_state_provider.dart';

/// Displays a single step with optional executing-state highlighting.
class StepCard extends StatelessWidget {
  final StepModel step;
  final ExecutionState executionState;

  const StepCard({
    super.key,
    required this.step,
    required this.executionState,
  });

  @override
  Widget build(BuildContext context) {
    final isExecuting = executionState == ExecutionState.executing;
    final theme = Theme.of(context);

    return AnimatedContainer(
      duration: const Duration(milliseconds: 200),
      margin: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isExecuting
              ? theme.colorScheme.primary
              : theme.colorScheme.outlineVariant,
          width: isExecuting ? 2 : 1,
        ),
        color: theme.colorScheme.surface,
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            if (isExecuting)
              Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  '正在进行中…',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: theme.colorScheme.onPrimaryContainer,
                  ),
                ),
              ),
            Text(
              step.description,
              style: theme.textTheme.titleMedium?.copyWith(height: 1.5),
            ),
            const SizedBox(height: 8),
            Text(
              '预计 ${step.estimatedMin} 分钟',
              style: theme.textTheme.bodySmall?.copyWith(
                color: theme.colorScheme.outline,
              ),
            ),
            if (step.isLowEnergy) ...[
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 10,
                  vertical: 6,
                ),
                decoration: BoxDecoration(
                  color: theme.colorScheme.secondaryContainer,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text('🌙', style: TextStyle(fontSize: 12)),
                    const SizedBox(width: 4),
                    Text(
                      '轻量但有进展',
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: theme.colorScheme.onSecondaryContainer,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Wraps [StepCard] in an [AnimatedSwitcher] so step changes fade+slide in.
class AnimatedStepCard extends StatelessWidget {
  final StepModel? step;
  final ExecutionState executionState;

  const AnimatedStepCard({
    super.key,
    required this.step,
    required this.executionState,
  });

  @override
  Widget build(BuildContext context) {
    if (step == null) {
      return const Center(child: Text('暂无待执行步骤'));
    }
    return Center(
      child: AnimatedSwitcher(
        duration: const Duration(milliseconds: 300),
        transitionBuilder: (child, animation) {
          return FadeTransition(
            opacity: animation,
            child: SlideTransition(
              position: Tween<Offset>(
                begin: const Offset(0, 0.08),
                end: Offset.zero,
              ).animate(
                CurvedAnimation(parent: animation, curve: Curves.easeOut),
              ),
              child: child,
            ),
          );
        },
        child: StepCard(
          key: ValueKey(step!.id),
          step: step!,
          executionState: executionState,
        ),
      ),
    );
  }
}
