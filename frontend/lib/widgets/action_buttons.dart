import 'package:flutter/material.dart';
import 'package:watch_your_energy/providers/execution_state_provider.dart';

/// Action button row for the home page.
///
/// idle      state: [开始（主）] [换一个] [我卡住了]
/// executing state: [完成（主）] [我卡住了]
/// isLoading : buttons disabled; primary button shows a spinner.
class ActionButtons extends StatelessWidget {
  final ExecutionState executionState;
  final bool isLoading;
  final VoidCallback? onStart;
  final VoidCallback? onComplete;
  final VoidCallback? onSkip;
  final VoidCallback? onStuck;

  const ActionButtons({
    super.key,
    required this.executionState,
    required this.isLoading,
    this.onStart,
    this.onComplete,
    this.onSkip,
    this.onStuck,
  });

  @override
  Widget build(BuildContext context) {
    final isExecuting = executionState == ExecutionState.executing;

    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 8, 24, 32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (!isExecuting) ...[
            FilledButton(
              onPressed: isLoading ? null : onStart,
              child: const Text('开始'),
            ),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: isLoading ? null : onSkip,
              child: isLoading
                  ? const SizedBox(
                      height: 18,
                      width: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('换一个'),
            ),
            const SizedBox(height: 4),
            TextButton(
              onPressed: isLoading ? null : onStuck,
              child: const Text('我卡住了'),
            ),
          ] else ...[
            FilledButton(
              onPressed: isLoading ? null : onComplete,
              child: isLoading
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor:
                            AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                  : const Text('完成'),
            ),
            const SizedBox(height: 12),
            OutlinedButton(
              onPressed: isLoading ? null : onStuck,
              child: const Text('我卡住了'),
            ),
          ],
        ],
      ),
    );
  }
}
