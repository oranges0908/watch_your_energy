import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:watch_your_energy/providers/app_state_provider.dart';
import 'package:watch_your_energy/providers/project_provider.dart';
import 'package:watch_your_energy/widgets/block_list_item.dart';

class ProgressPage extends ConsumerWidget {
  const ProgressPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncAppState = ref.watch(appStateProvider);
    final projectId = asyncAppState.value?.project?.id;
    final isLoading = asyncAppState.isLoading;

    if (projectId == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('项目进展')),
        body: const Center(child: Text('暂无活跃项目')),
      );
    }

    final asyncDetail = ref.watch(projectDetailProvider(projectId));

    return Scaffold(
      appBar: AppBar(title: const Text('项目进展')),
      body: asyncDetail.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('加载失败: $e')),
        data: (detail) {
          final allComplete =
              detail.blocks.isNotEmpty &&
              detail.blocks.every((b) => b.isCompleted);

          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // ── Project header ────────────────────────────────────────
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 16, 20, 12),
                child: Row(
                  children: [
                    Expanded(
                      child: Text(
                        detail.project.title,
                        style:
                            Theme.of(context).textTheme.titleLarge?.copyWith(
                                  fontWeight: FontWeight.w600,
                                ),
                        overflow: TextOverflow.ellipsis,
                      ),
                    ),
                    Text(
                      '${detail.project.progressPct}%',
                      style:
                          Theme.of(context).textTheme.titleLarge?.copyWith(
                                fontWeight: FontWeight.w600,
                                color: Theme.of(context).colorScheme.primary,
                              ),
                    ),
                  ],
                ),
              ),
              const Divider(height: 1),
              // ── Blocks list ───────────────────────────────────────────
              Expanded(
                child: ListView.separated(
                  itemCount: detail.blocks.length,
                  separatorBuilder: (_, __) =>
                      const Divider(height: 1, indent: 56),
                  itemBuilder: (context, index) =>
                      BlockListItem(block: detail.blocks[index]),
                ),
              ),
              // ── Archive button (only when all blocks completed) ───────
              if (allComplete)
                Padding(
                  padding: const EdgeInsets.fromLTRB(24, 8, 24, 32),
                  child: FilledButton(
                    style: FilledButton.styleFrom(
                      backgroundColor:
                          Theme.of(context).colorScheme.error,
                    ),
                    onPressed: isLoading
                        ? null
                        : () async {
                            await ref
                                .read(appStateProvider.notifier)
                                .archiveProject(projectId);
                            ref.invalidate(projectListProvider);
                            if (context.mounted) context.go('/');
                          },
                    child: isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              valueColor: AlwaysStoppedAnimation<Color>(
                                Colors.white,
                              ),
                            ),
                          )
                        : const Text('归档此项目'),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}
