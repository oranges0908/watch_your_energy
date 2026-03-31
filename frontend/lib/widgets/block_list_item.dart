import 'package:flutter/material.dart';
import 'package:watch_your_energy/models/project.dart';

/// Single row in the progress page block list.
/// Shows status icon + block title + progress% for in-progress blocks.
class BlockListItem extends StatelessWidget {
  final BlockModel block;

  const BlockListItem({super.key, required this.block});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final showProgress =
        block.status == 'in_progress' || block.status == 'near_complete';

    return ListTile(
      leading: _statusIcon(block.status, theme),
      title: Text(block.title),
      subtitle: showProgress ? Text('${block.progressPct}% done') : null,
    );
  }

  Widget _statusIcon(String status, ThemeData theme) {
    switch (status) {
      case 'completed':
        return Icon(Icons.check_circle, color: theme.colorScheme.primary);
      case 'near_complete':
        return Icon(Icons.incomplete_circle, color: theme.colorScheme.primary);
      case 'in_progress':
        return Icon(Icons.timelapse,
            color: theme.colorScheme.primary.withValues(alpha: 0.7));
      default: // not_started
        return const Icon(Icons.radio_button_unchecked, color: Colors.grey);
    }
  }
}
