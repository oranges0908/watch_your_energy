import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:watch_your_energy/providers/app_state_provider.dart';
import 'package:watch_your_energy/providers/project_provider.dart';

/// Left-side Drawer — lists active projects and a "New Project" button.
/// Width ≈ 40% of screen per spec.
class ProjectSidebar extends ConsumerWidget {
  const ProjectSidebar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncProjects = ref.watch(projectListProvider);
    final activeId = ref.watch(appStateProvider).value?.project?.id;
    final notifier = ref.read(appStateProvider.notifier);

    return Drawer(
      width: MediaQuery.of(context).size.width * 0.4,
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Padding(
              padding: EdgeInsets.fromLTRB(16, 16, 16, 8),
              child: Text(
                '我的项目',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: asyncProjects.when(
                loading: () =>
                    const Center(child: CircularProgressIndicator()),
                error: (_, __) =>
                    const Center(child: Text('加载失败')),
                data: (projects) => ListView.builder(
                  itemCount: projects.length,
                  itemBuilder: (context, index) {
                    final p = projects[index];
                    final isActive = p.id == activeId;
                    return ListTile(
                      title: Text(
                        p.title,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(
                          fontWeight: isActive
                              ? FontWeight.w600
                              : FontWeight.normal,
                        ),
                      ),
                      subtitle: Text('${p.progressPct}%'),
                      selected: isActive,
                      selectedColor:
                          Theme.of(context).colorScheme.primary,
                      onTap: isActive
                          ? null
                          : () async {
                              await notifier.switchProject(p.id);
                              if (context.mounted) {
                                Navigator.of(context).pop();
                              }
                            },
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
                  message: canCreate ? '' : '最多同时推进3个',
                  child: ListTile(
                    enabled: canCreate,
                    leading: Icon(
                      Icons.add,
                      color: canCreate ? null : Colors.grey,
                    ),
                    title: Text(
                      '新建 Project',
                      style: TextStyle(
                        color: canCreate ? null : Colors.grey,
                      ),
                    ),
                    onTap: canCreate
                        ? () {
                            Navigator.of(context).pop();
                            context.go('/create');
                          }
                        : null,
                  ),
                );
              },
              orElse: () => const SizedBox(height: 56),
            ),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
  }
}
