import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:watch_your_energy/models/project.dart';
import 'package:watch_your_energy/providers/app_state_provider.dart';

/// Fetches the list of active projects from the backend.
final projectListProvider =
    FutureProvider.autoDispose<List<ProjectModel>>((ref) async {
  final api = ref.watch(apiServiceProvider);
  return api.getProjects();
});

/// Fetches project details (project + blocks) for the progress page.
final projectDetailProvider = FutureProvider.autoDispose
    .family<ProjectDetail, String>((ref, projectId) async {
  final api = ref.watch(apiServiceProvider);
  return api.getProjectDetail(projectId);
});
