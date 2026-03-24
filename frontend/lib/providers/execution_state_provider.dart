import 'package:flutter_riverpod/flutter_riverpod.dart';

enum ExecutionState { idle, executing }

/// Local UI state: whether the user has started a step and is currently working on it.
/// idle      → shows 开始 / 换一个 / 我卡住了
/// executing → shows 完成 / 我卡住了
final executionStateProvider = StateProvider<ExecutionState>(
  (ref) => ExecutionState.idle,
);
