import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:mocktail/mocktail.dart';
import 'package:watch_your_energy/models/app_state.dart';
import 'package:watch_your_energy/models/project.dart';
import 'package:watch_your_energy/models/step.dart';
import 'package:watch_your_energy/pages/create_project_page.dart';
import 'package:watch_your_energy/providers/app_state_provider.dart';
import 'package:watch_your_energy/providers/project_provider.dart';
import 'package:watch_your_energy/services/api_service.dart';
import 'package:watch_your_energy/theme/app_theme.dart';

// ── Mock ──────────────────────────────────────────────────────────────────────

class MockApiService extends Mock implements ApiService {}

// ── Fixtures ──────────────────────────────────────────────────────────────────

AppState _makeState() => const AppState(
      step: StepModel(
        id: 's1',
        description: '写项目1的第一句话',
        estimatedMin: 10,
        pattern: 'Bootstrap',
        stepType: 'Bootstrap',
        blockTitle: '项目1',
        energyLevel: 'normal',
      ),
      project: ProjectModel(id: 'p1', title: '优化简历', progressPct: 0),
      energyMode: 'normal',
      onboardingComplete: true,
    );

// ── Helper ────────────────────────────────────────────────────────────────────

Widget _buildApp(MockApiService api) {
  final router = GoRouter(
    initialLocation: '/create',
    routes: [
      GoRoute(
        path: '/',
        builder: (_, __) => const Scaffold(body: Text('首页')),
      ),
      GoRoute(
        path: '/create',
        builder: (_, __) => const CreateProjectPage(),
      ),
    ],
  );

  return ProviderScope(
    overrides: [
      apiServiceProvider.overrideWithValue(api),
      // Keep appStateProvider in an initial loading state so it doesn't
      // attempt real API calls and interfere with create-page tests.
      projectListProvider.overrideWith(
        (ref) async => const <ProjectModel>[],
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
    // appStateProvider build() → postSession + getState
    const emptyState = AppState(
      step: null,
      project: null,
      energyMode: 'normal',
      onboardingComplete: false,
    );
    when(() => mockApi.postSession()).thenAnswer((_) async => emptyState);
    when(() => mockApi.getState()).thenAnswer((_) async => emptyState);
  });

  // ── Step 1 ────────────────────────────────────────────────────────────────

  testWidgets('Step1: 空title时「下一步」禁用', (tester) async {
    await tester.pumpWidget(_buildApp(mockApi));
    await tester.pumpAndSettle();

    final btn = tester.widget<FilledButton>(find.byType(FilledButton));
    expect(btn.onPressed, isNull);
  });

  testWidgets('Step1: 输入后「下一步」可点击', (tester) async {
    await tester.pumpWidget(_buildApp(mockApi));
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField), '优化简历');
    await tester.pump();

    final btn = tester.widget<FilledButton>(find.byType(FilledButton));
    expect(btn.onPressed, isNotNull);
  });

  testWidgets('Step1→Step2: tap下一步显示4个CheckboxListTile', (tester) async {
    await tester.pumpWidget(_buildApp(mockApi));
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField), '优化简历');
    await tester.pump();
    await tester.tap(find.text('下一步'));
    await tester.pump();

    expect(find.byType(CheckboxListTile), findsNWidgets(4));
    expect(find.text('项目1'), findsOneWidget);
    expect(find.text('项目2'), findsOneWidget);
    expect(find.text('项目3'), findsOneWidget);
    expect(find.text('总结'), findsOneWidget);
  });

  testWidgets('Step2: 「创建并开始」按钮可点击', (tester) async {
    await tester.pumpWidget(_buildApp(mockApi));
    await tester.pumpAndSettle();

    await tester.enterText(find.byType(TextField), '优化简历');
    await tester.pump();
    await tester.tap(find.text('下一步'));
    await tester.pump();

    final btn = tester.widget<FilledButton>(find.byType(FilledButton));
    expect(btn.onPressed, isNotNull);
  });

  testWidgets('提交成功：调用postProject并导航到"/"', (tester) async {
    final newState = _makeState();
    when(() => mockApi.postProject('优化简历', any())).thenAnswer(
      (_) async => newState,
    );
    when(() => mockApi.getProjects())
        .thenAnswer((_) async => [newState.project!]);

    await tester.pumpWidget(_buildApp(mockApi));
    await tester.pumpAndSettle();

    // Step 1: enter title
    await tester.enterText(find.byType(TextField), '优化简历');
    await tester.pump();
    await tester.tap(find.text('下一步'));
    await tester.pump();

    // Step 2: tap 创建并开始
    await tester.tap(find.text('创建并开始'));
    await tester.pumpAndSettle();

    verify(() => mockApi.postProject('优化简历', any())).called(1);
    // Navigated to '/' — home page text should be visible
    expect(find.text('首页'), findsOneWidget);
  });
}
