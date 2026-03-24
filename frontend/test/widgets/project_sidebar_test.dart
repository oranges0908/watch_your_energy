import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:watch_your_energy/models/app_state.dart';
import 'package:watch_your_energy/models/project.dart';
import 'package:watch_your_energy/models/step.dart';
import 'package:watch_your_energy/providers/app_state_provider.dart';
import 'package:watch_your_energy/providers/project_provider.dart';
import 'package:watch_your_energy/services/api_service.dart';
import 'package:watch_your_energy/theme/app_theme.dart';
import 'package:watch_your_energy/widgets/project_sidebar.dart';

// ── Mock ──────────────────────────────────────────────────────────────────────

class MockApiService extends Mock implements ApiService {}

// ── Fixtures ──────────────────────────────────────────────────────────────────

ProjectModel _makeProject(String id, String title, {int progress = 10}) =>
    ProjectModel(id: id, title: title, progressPct: progress);

AppState _makeState(ProjectModel project) => AppState(
      step: const StepModel(
        id: 's1',
        description: '写项目1的第一句话',
        estimatedMin: 10,
        pattern: 'Push',
        stepType: 'Push',
        blockTitle: '项目1',
        energyLevel: 'normal',
      ),
      project: project,
      energyMode: 'normal',
      onboardingComplete: true,
    );

// Fake notifier: extends AppStateNotifier so overrideWith type-checks.
// Overrides only build(). switchProject uses the real implementation,
// which calls patchActiveProject via the mocked apiServiceProvider.
class _FakeNotifier extends AppStateNotifier {
  _FakeNotifier(this._state);
  final AppState _state;

  @override
  Future<AppState> build() async => _state;
}

// ── Helper ────────────────────────────────────────────────────────────────────

/// Plain MaterialApp with Scaffold+Drawer — provides Navigator and Overlay.
Widget _buildApp(
  MockApiService api,
  List<ProjectModel> projects,
  ProjectModel activeProject,
) {
  return ProviderScope(
    overrides: [
      apiServiceProvider.overrideWithValue(api),
      projectListProvider.overrideWith((ref) async => projects),
      appStateProvider.overrideWith(
        () => _FakeNotifier(_makeState(activeProject)),
      ),
    ],
    child: MaterialApp(
      theme: AppTheme.theme,
      home: Scaffold(
        drawer: const ProjectSidebar(),
        body: Builder(
          builder: (ctx) => TextButton(
            onPressed: () => Scaffold.of(ctx).openDrawer(),
            child: const Text('open'),
          ),
        ),
      ),
    ),
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────────

void main() {
  late MockApiService mockApi;

  setUp(() {
    mockApi = MockApiService();
  });

  // ── 项目上限 ──────────────────────────────────────────────────────────────

  testWidgets('projects.length=3：「新建Project」disabled', (tester) async {
    final projects = [
      _makeProject('p1', '优化简历'),
      _makeProject('p2', '学习Flutter'),
      _makeProject('p3', '读书计划'),
    ];

    await tester.pumpWidget(_buildApp(mockApi, projects, projects[0]));
    await tester.pumpAndSettle();

    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    final tile = tester.widget<ListTile>(
      find.ancestor(
        of: find.text('新建 Project'),
        matching: find.byType(ListTile),
      ),
    );
    expect(tile.enabled, isFalse);
  });

  testWidgets('projects.length=2：「新建Project」enabled', (tester) async {
    final projects = [
      _makeProject('p1', '优化简历'),
      _makeProject('p2', '学习Flutter'),
    ];

    await tester.pumpWidget(_buildApp(mockApi, projects, projects[0]));
    await tester.pumpAndSettle();

    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    final tile = tester.widget<ListTile>(
      find.ancestor(
        of: find.text('新建 Project'),
        matching: find.byType(ListTile),
      ),
    );
    expect(tile.enabled, isTrue);
  });

  // ── 切换项目 ──────────────────────────────────────────────────────────────

  testWidgets('tap非活跃项目 → 调用patchActiveProject', (tester) async {
    final p1 = _makeProject('p1', '优化简历');
    final p2 = _makeProject('p2', '学习Flutter');

    when(() => mockApi.patchActiveProject('p2'))
        .thenAnswer((_) async => _makeState(p2));

    await tester.pumpWidget(_buildApp(mockApi, [p1, p2], p1));
    await tester.pumpAndSettle();

    await tester.tap(find.text('open'));
    await tester.pumpAndSettle();

    await tester.tap(find.text('学习Flutter'));
    await tester.pumpAndSettle();

    verify(() => mockApi.patchActiveProject('p2')).called(1);
  });
}
