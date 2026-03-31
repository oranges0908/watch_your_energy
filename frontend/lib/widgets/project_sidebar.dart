import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:watch_your_energy/providers/app_state_provider.dart';
import 'package:watch_your_energy/providers/project_provider.dart';

/// Fixed left-side project list panel.
/// Width is controlled by the parent (home_page uses SizedBox).
class ProjectSidebar extends ConsumerWidget {
  const ProjectSidebar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncProjects = ref.watch(projectListProvider);
    final activeId = ref.watch(appStateProvider).value?.project?.id;
    final notifier = ref.read(appStateProvider.notifier);
    final theme = Theme.of(context);

    return ColoredBox(
      color: theme.colorScheme.surfaceContainerLow,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 16, 12, 8),
            child: Text(
              'My Projects',
              style: theme.textTheme.labelLarge?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: asyncProjects.when(
              loading: () =>
                  const Center(child: CircularProgressIndicator()),
              error: (_, __) =>
                  const Center(child: Text('Failed to load')),
              data: (projects) => ListView.builder(
                itemCount: projects.length,
                itemBuilder: (context, index) {
                  final p = projects[index];
                  final isActive = p.id == activeId;
                  return ListTile(
                    dense: true,
                    contentPadding:
                        const EdgeInsets.symmetric(horizontal: 12),
                    title: Text(
                      p.title,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: isActive
                            ? FontWeight.w600
                            : FontWeight.normal,
                      ),
                    ),
                    subtitle: Text(
                      '${p.progressPct}%',
                      style: const TextStyle(fontSize: 11),
                    ),
                    selected: isActive,
                    selectedColor: theme.colorScheme.primary,
                    selectedTileColor:
                        theme.colorScheme.primaryContainer.withValues(alpha: 0.3),
                    onTap: isActive
                        ? null
                        : () => notifier.switchProject(p.id),
                  );
                },
              ),
            ),
          ),
          const Divider(height: 1),
          asyncProjects.maybeWhen(
            data: (projects) {
              final canCreate = projects.length < 3;
              return Tooltip(
                message: canCreate ? '' : 'Maximum 3 active projects',
                child: ListTile(
                  dense: true,
                  contentPadding:
                      const EdgeInsets.symmetric(horizontal: 12),
                  enabled: canCreate,
                  leading: Icon(
                    Icons.add,
                    size: 18,
                    color: canCreate ? null : Colors.grey,
                  ),
                  title: Text(
                    'New',
                    style: TextStyle(
                      fontSize: 13,
                      color: canCreate ? null : Colors.grey,
                    ),
                  ),
                  onTap: canCreate ? () => context.go('/create') : null,
                ),
              );
            },
            orElse: () => const SizedBox(height: 48),
          ),
          const SizedBox(height: 8),
        ],
      ),
    );
  }
}
