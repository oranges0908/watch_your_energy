import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:mocktail/mocktail.dart';
import 'package:watch_your_energy/models/app_state.dart';
import 'package:watch_your_energy/models/project.dart';
import 'package:watch_your_energy/models/step.dart';
import 'package:watch_your_energy/pages/progress_page.dart';
import 'package:watch_your_energy/providers/app_state_provider.dart';
import 'package:watch_your_energy/providers/project_provider.dart';
import 'package:watch_your_energy/services/api_service.dart';
import 'package:watch_your_energy/theme/app_theme.dart';

// ── Mock ──────────────────────────────────────────────────────────────────────

class MockApiService extends Mock implements ApiService {}

// ── Fixtures ──────────────────────────────────────────────────────────────────

const _kProject = ProjectModel(id: 'proj-1', title: '优化简历', progressPct: 100);

const _kStep = StepModel(
  id: 's1',
  description: '写项目1的第一句话',
  estimatedMin: 10,
  pattern: 'Push',
  stepType: 'Push',
  blockTitle: '项目1',
  energyLevel: 'normal',
);

BlockModel _makeBlock(String id, String title, String status,
    {int progress = 100}) =>
    BlockModel(
      id: id,
      title: title,
      position: 0,
      status: status,
      progressPct: progress,
    );

AppState _makeState() => const AppState(
      step: _kStep,
      project: _kProject,
      energyMode: 'normal',
      onboardingComplete: true,
    );

ProjectDetail _makeDetail(List<BlockModel> blocks) =>
    ProjectDetail(project: _kProject, blocks: blocks);

// All blocks completed
final _allCompleteBlocks = [
  _makeBlock('b1', '项目1', 'completed'),
  _makeBlock('b2', '项目2', 'completed'),
  _makeBlock('b3', '项目3', 'completed'),
  _makeBlock('b4', '总结', 'completed'),
];

// Not all blocks completed
final _partialBlocks = [
  _makeBlock('b1', '项目1', 'completed'),
  _makeBlock('b2', '项目2', 'in_progress', progress: 40),
  _makeBlock('b3', '项目3', 'not_started', progress: 0),
  _makeBlock('b4', '总结', 'not_started', progress: 0),
];

// Fake notifier that extends AppStateNotifier.
class _FakeNotifier extends AppStateNotifier {
  _FakeNotifier(this._state);
  final AppState _state;

  @override
  Future<AppState> build() async => _state;
}

// ── Helper ────────────────────────────────────────────────────────────────────

Widget _buildApp(
  MockApiService api,
  List<BlockModel> blocks, {
  String initialRoute = '/progress',
}) {
  final router = GoRouter(
    initialLocation: initialRoute,
    routes: [
      GoRoute(
        path: '/',
        builder: (_, __) => const Scaffold(body: Text('首页')),
      ),
      GoRoute(
        path: '/progress',
        builder: (_, __) => const ProgressPage(),
      ),
    ],
  );

  return ProviderScope(
    overrides: [
      apiServiceProvider.overrideWithValue(api),
      appStateProvider.overrideWith(() => _FakeNotifier(_makeState())),
      projectDetailProvider('proj-1').overrideWith(
        (ref) async => _makeDetail(blocks),
      ),
    ],
    child: MaterialApp.router(
      theme: AppTheme.theme,
      routerConfig: router,
    ),
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────────

void main() {
  late MockApiService mockApi;

  setUp(() {
    mockApi = MockApiService();
  });

  // ── Archive button visibility ─────────────────────────────────────────────

  testWidgets('all blocks completed → 显示「Archive project」按钮', (tester) async {
    await tester.pumpWidget(_buildApp(mockApi, _allCompleteBlocks));
    await tester.pumpAndSettle();

    expect(find.text('Archive project'), findsOneWidget);
  });

  testWidgets('blocks未全部完成 → 不显示「Archive project」按钮', (tester) async {
    await tester.pumpWidget(_buildApp(mockApi, _partialBlocks));
    await tester.pumpAndSettle();

    expect(find.text('Archive project'), findsNothing);
  });

  // ── Archive action ────────────────────────────────────────────────────────

  testWidgets('tap「Archive project」→ 调用deleteProject + 导航到"/"', (tester) async {
    when(() => mockApi.deleteProject('proj-1')).thenAnswer((_) async {});
    when(() => mockApi.getState()).thenAnswer((_) async => const AppState(
          step: null,
          project: null,
          energyMode: 'normal',
          onboardingComplete: true,
        ));
    when(() => mockApi.getProjects()).thenAnswer((_) async => const []);

    await tester.pumpWidget(_buildApp(mockApi, _allCompleteBlocks));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Archive project'));
    await tester.pumpAndSettle();

    verify(() => mockApi.deleteProject('proj-1')).called(1);
    // Navigated to '/'
    expect(find.text('首页'), findsOneWidget);
  });
}
