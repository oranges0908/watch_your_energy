import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Holds the latest network-error message to be shown as a SnackBar.
/// Set by [AppStateNotifier] on API failure; cleared by [HomePage] after display.
final errorMessageProvider = StateProvider<String?>((ref) => null);
