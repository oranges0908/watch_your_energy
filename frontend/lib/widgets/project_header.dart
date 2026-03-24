import 'package:flutter/material.dart';
import 'package:watch_your_energy/models/project.dart';

/// Shows project title, progress %, and an animated progress bar.
/// The 「切换」button is a placeholder — wired up in I6.
class ProjectHeader extends StatelessWidget {
  final ProjectModel? project;
  final VoidCallback? onSwitch;

  const ProjectHeader({super.key, this.project, this.onSwitch});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final pct = project?.progressPct ?? 0;
    final title = project?.title ?? '—';

    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 16, 16, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  title,
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Text(
                '$pct%',
                style: theme.textTheme.titleMedium?.copyWith(
                  color: theme.colorScheme.primary,
                  fontWeight: FontWeight.w600,
                ),
              ),
              const SizedBox(width: 4),
              TextButton(
                onPressed: onSwitch,
                style: TextButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 8),
                  minimumSize: Size.zero,
                  tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                ),
                child: const Text('切换'),
              ),
            ],
          ),
          const SizedBox(height: 8),
          TweenAnimationBuilder<double>(
            duration: const Duration(milliseconds: 500),
            curve: Curves.easeInOut,
            tween: Tween<double>(begin: 0, end: pct / 100.0),
            builder: (context, value, _) => LinearProgressIndicator(
              value: value,
              borderRadius: BorderRadius.circular(4),
            ),
          ),
        ],
      ),
    );
  }
}
