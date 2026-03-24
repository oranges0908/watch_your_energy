import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Holds the last feedback message from a completed step (e.g. "项目1已推进").
/// Set by AppStateNotifier.onComplete(); cleared automatically after 2 seconds.
final feedbackMessageProvider = StateProvider<String?>((ref) => null);
