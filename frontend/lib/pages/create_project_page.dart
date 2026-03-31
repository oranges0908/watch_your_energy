import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:watch_your_energy/providers/app_state_provider.dart';
import 'package:watch_your_energy/providers/project_provider.dart';

class CreateProjectPage extends ConsumerStatefulWidget {
  const CreateProjectPage({super.key});

  @override
  ConsumerState<CreateProjectPage> createState() =>
      _CreateProjectPageState();
}

class _CreateProjectPageState extends ConsumerState<CreateProjectPage> {
  int _step = 1;
  String _title = '';

  // Step 2 state
  final List<TextEditingController> _controllers = [];
  bool _loadingSuggestions = false;
  final Set<int> _checkedPositions = {};
  bool _isSubmitting = false;

  @override
  void dispose() {
    for (final c in _controllers) {
      c.dispose();
    }
    super.dispose();
  }

  // ── Helpers ───────────────────────────────────────────────────────────────

  bool get _canGoNext => _title.trim().isNotEmpty;

  bool get _canSubmit =>
      _controllers.isNotEmpty &&
      _controllers.any((c) => c.text.trim().isNotEmpty);

  void _setTitles(List<String> titles) {
    for (final c in _controllers) {
      c.dispose();
    }
    _controllers
      ..clear()
      ..addAll(titles.map((t) => TextEditingController(text: t)));
  }

  Future<void> _goToStep2() async {
    setState(() {
      _step = 2;
      _loadingSuggestions = true;
      _checkedPositions.clear();
    });

    try {
      final titles =
          await ref.read(apiServiceProvider).suggestBlocks(_title.trim());
      if (mounted) setState(() => _setTitles(titles));
    } catch (_) {
      if (mounted) {
        setState(() => _setTitles(['Part 1', 'Part 2', 'Part 3', 'Wrap-up']));
      }
    } finally {
      if (mounted) setState(() => _loadingSuggestions = false);
    }
  }

  void _goToStep1() {
    setState(() {
      _step = 1;
      _setTitles([]);
    });
  }

  void _addBlock() {
    setState(() {
      _controllers.add(TextEditingController());
    });
  }

  void _deleteBlock(int index) {
    setState(() {
      _controllers[index].dispose();
      _controllers.removeAt(index);
      // Remap checked positions after deletion
      final updated = <int>{};
      for (final pos in _checkedPositions) {
        if (pos < index) updated.add(pos);
        if (pos > index) updated.add(pos - 1);
      }
      _checkedPositions
        ..clear()
        ..addAll(updated);
    });
  }

  Future<void> _submit() async {
    final blockTitles = _controllers
        .map((c) => c.text.trim())
        .where((t) => t.isNotEmpty)
        .toList();

    setState(() => _isSubmitting = true);
    try {
      await ref.read(appStateProvider.notifier).createProject(
            _title.trim(),
            _checkedPositions.toList(),
            blockTitles,
          );
      ref.invalidate(projectListProvider);
      if (mounted) context.go('/');
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Failed to create, please retry')),
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
        title: const Text('New Project'),
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
          'What do you want to advance?',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 16),
        TextField(
          autofocus: true,
          maxLines: 1,
          decoration: const InputDecoration(
            hintText: 'e.g. Improve my resume',
            border: OutlineInputBorder(),
          ),
          onChanged: (v) => setState(() => _title = v),
        ),
        const Spacer(),
        FilledButton(
          onPressed: _canGoNext ? _goToStep2 : null,
          child: const Text('Next'),
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
          'Confirm structure',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 4),
        Text(
          'Edit, add or remove blocks · check any already completed',
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.outline,
              ),
        ),
        const SizedBox(height: 12),
        if (_loadingSuggestions)
          const Expanded(
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  CircularProgressIndicator(),
                  SizedBox(height: 12),
                  Text('Generating block suggestions…'),
                ],
              ),
            ),
          )
        else ...[
          // Block list scrolls independently
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: List.generate(
                  _controllers.length,
                  (index) => _buildBlockRow(index),
                ),
              ),
            ),
          ),
          // Add + Submit always visible at bottom
          TextButton.icon(
            onPressed: _addBlock,
            icon: const Icon(Icons.add, size: 18),
            label: const Text('Add block'),
          ),
          const SizedBox(height: 4),
          FilledButton(
            onPressed: (_isSubmitting || !_canSubmit) ? null : _submit,
            child: _isSubmitting
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor:
                          AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  )
                : const Text('Create & Start'),
          ),
        ],
      ],
    );
  }

  Widget _buildBlockRow(int index) {
    final canDelete = _controllers.length > 1;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          // ── Completed checkbox ────────────────────────────────────────
          Checkbox(
            value: _checkedPositions.contains(index),
            onChanged: (checked) {
              setState(() {
                if (checked == true) {
                  _checkedPositions.add(index);
                } else {
                  _checkedPositions.remove(index);
                }
              });
            },
          ),
          // ── Editable title ───────────────────────────────────────────
          Expanded(
            child: TextField(
              controller: _controllers[index],
              decoration: const InputDecoration(
                border: OutlineInputBorder(),
                isDense: true,
                contentPadding:
                    EdgeInsets.symmetric(horizontal: 10, vertical: 10),
              ),
              onChanged: (_) => setState(() {}),
            ),
          ),
          // ── Delete button ─────────────────────────────────────────────
          IconButton(
            icon: Icon(
              Icons.close,
              size: 18,
              color: canDelete
                  ? Theme.of(context).colorScheme.error
                  : Colors.grey.shade300,
            ),
            tooltip: 'Remove',
            onPressed: canDelete ? () => _deleteBlock(index) : null,
          ),
        ],
      ),
    );
  }
}
