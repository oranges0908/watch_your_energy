import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:watch_your_energy/providers/app_state_provider.dart';
import 'package:watch_your_energy/providers/project_provider.dart';

const _kBlockTitles = ['项目1', '项目2', '项目3', '总结'];

class CreateProjectPage extends ConsumerStatefulWidget {
  const CreateProjectPage({super.key});

  @override
  ConsumerState<CreateProjectPage> createState() =>
      _CreateProjectPageState();
}

class _CreateProjectPageState extends ConsumerState<CreateProjectPage> {
  int _step = 1;
  String _title = '';
  final Set<int> _checkedPositions = {};
  bool _isSubmitting = false;

  // ── Helpers ───────────────────────────────────────────────────────────────

  bool get _canGoNext => _title.trim().isNotEmpty;

  void _goToStep2() => setState(() => _step = 2);

  void _goToStep1() => setState(() => _step = 1);

  Future<void> _submit() async {
    setState(() => _isSubmitting = true);
    try {
      await ref
          .read(appStateProvider.notifier)
          .createProject(_title.trim(), _checkedPositions.toList());
      ref.invalidate(projectListProvider);
      if (mounted) context.go('/');
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('创建失败，请重试')),
        );
      }
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  // ── Build ─────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('新建项目'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: _step == 2 ? _goToStep1 : () => context.pop(),
        ),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: _step == 1 ? _buildStep1() : _buildStep2(),
        ),
      ),
    );
  }

  // ── Step 1 ────────────────────────────────────────────────────────────────

  Widget _buildStep1() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          '你想推进什么？',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 16),
        TextField(
          autofocus: true,
          maxLines: 1,
          decoration: const InputDecoration(
            hintText: '例：优化简历',
            border: OutlineInputBorder(),
          ),
          onChanged: (v) => setState(() => _title = v),
        ),
        const Spacer(),
        FilledButton(
          onPressed: _canGoNext ? _goToStep2 : null,
          child: const Text('下一步'),
        ),
      ],
    );
  }

  // ── Step 2 ────────────────────────────────────────────────────────────────

  Widget _buildStep2() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          '已完成哪些部分？',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 4),
        Text(
          '勾选已完成的结构块，跳过这些块直接继续',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.outline,
              ),
        ),
        const SizedBox(height: 16),
        ..._kBlockTitles.asMap().entries.map((entry) {
          final position = entry.key;
          final title = entry.value;
          return CheckboxListTile(
            title: Text(title),
            value: _checkedPositions.contains(position),
            onChanged: (checked) {
              setState(() {
                if (checked == true) {
                  _checkedPositions.add(position);
                } else {
                  _checkedPositions.remove(position);
                }
              });
            },
          );
        }),
        const Spacer(),
        FilledButton(
          onPressed: _isSubmitting ? null : _submit,
          child: _isSubmitting
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                )
              : const Text('创建并开始'),
        ),
      ],
    );
  }
}
