import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:watch_your_energy/providers/feedback_provider.dart';

/// Bottom toast that appears when [feedbackMessageProvider] is non-null.
/// Auto-cleared after 2 seconds by [AppStateNotifier.onComplete].
/// Must be placed inside a [Stack] that fills the screen.
class CompletionFlash extends ConsumerWidget {
  const CompletionFlash({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final message = ref.watch(feedbackMessageProvider);
    final theme = Theme.of(context);

    return IgnorePointer(
      child: Align(
        alignment: Alignment.bottomCenter,
        child: AnimatedOpacity(
          opacity: message != null ? 1.0 : 0.0,
          duration: const Duration(milliseconds: 300),
          child: Padding(
            padding: const EdgeInsets.only(left: 24, right: 24, bottom: 32),
            child: Material(
              elevation: 4,
              borderRadius: BorderRadius.circular(12),
              color: theme.colorScheme.primaryContainer,
              child: Padding(
                padding: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 12,
                ),
                child: Text(
                  message ?? '',
                  style: theme.textTheme.bodyMedium?.copyWith(
                    color: theme.colorScheme.onPrimaryContainer,
                  ),
                  textAlign: TextAlign.center,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
