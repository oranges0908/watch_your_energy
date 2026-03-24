import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:watch_your_energy/models/app_state.dart';
import 'package:watch_your_energy/models/project.dart';
import 'package:watch_your_energy/models/step.dart';
import 'package:watch_your_energy/pages/home_page.dart';
import 'package:watch_your_energy/providers/app_state_provider.dart';
import 'package:watch_your_energy/services/api_service.dart';
import 'package:watch_your_energy/theme/app_theme.dart';

// ── Mock ──────────────────────────────────────────────────────────────────────

class MockApiService extends Mock implements ApiService {}

// ── Fixtures ──────────────────────────────────────────────────────────────────

StepModel _makeStep({
  String id = 'step-1',
  String desc = '写项目1的第一句话',
  int estimatedMin = 10,
}) {
  return StepModel(
    id: id,
    description: desc,
    estimatedMin: estimatedMin,
    pattern: 'Continuation',
    stepType: 'Push',
    blockTitle: '项目1',
    energyLevel: 'normal',
  );
}

AppState _makeState({String stepId = 'step-1', String desc = '写项目1的第一句话'}) {
  return AppState(
    step: _makeStep(id: stepId, desc: desc),
    project: const ProjectModel(id: 'proj-1', title: '优化简历', progressPct: 20),
    energyMode: 'normal',
    onboardingComplete: true,
  );
}

// ── Helper ────────────────────────────────────────────────────────────────────

Widget _buildApp(MockApiService api) {
  return ProviderScope(
    overrides: [apiServiceProvider.overrideWithValue(api)],
    child: MaterialApp(theme: AppTheme.theme, home: const HomePage()),
  );
}

// ── Tests ─────────────────────────────────────────────────────────────────────

void main() {
  late MockApiService mockApi;

  setUp(() {
    mockApi = MockApiService();
  });

  // ── Loading ───────────────────────────────────────────────────────────────

  testWidgets('AsyncLoading无previous → 显示全屏Spinner', (tester) async {
    // Never-completing futures keep the provider in AsyncLoading.
    final c1 = Completer<AppState>();
    final c2 = Completer<AppState>();
    when(() => mockApi.postSession()).thenAnswer((_) => c1.future);
    when(() => mockApi.getState()).thenAnswer((_) => c2.future);

    await tester.pumpWidget(_buildApp(mockApi));
    await tester.pump(Duration.zero);

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.text('写项目1的第一句话'), findsNothing);

    // Clean up to avoid pending timer warnings.
    c1.completeError(Exception('cleanup'));
    c2.completeError(Exception('cleanup'));
  });

  // ── AsyncData ─────────────────────────────────────────────────────────────

  testWidgets('AsyncData → 显示StepCard内容', (tester) async {
    final state = _makeState();
    when(() => mockApi.postSession()).thenAnswer((_) async => state);
    when(() => mockApi.getState()).thenAnswer((_) async => state);

    await tester.pumpWidget(_buildApp(mockApi));
    await tester.pumpAndSettle();

    expect(find.text('写项目1的第一句话'), findsOneWidget);
    expect(find.text('预计 10 分钟'), findsOneWidget);
    expect(find.text('优化简历'), findsOneWidget);
    expect(find.text('20%'), findsOneWidget);
  });

  // ── 开始 button ───────────────────────────────────────────────────────────

  testWidgets('tap 开始 → ActionButtons切换为executing态', (tester) async {
    final state = _makeState();
    when(() => mockApi.postSession()).thenAnswer((_) async => state);
    when(() => mockApi.getState()).thenAnswer((_) async => state);

    await tester.pumpWidget(_buildApp(mockApi));
    await tester.pumpAndSettle();

    // idle: 开始 / 换一个 visible
    expect(find.text('开始'), findsOneWidget);
    expect(find.text('换一个'), findsOneWidget);

    await tester.tap(find.text('开始'));
    await tester.pump();

    // executing: 完成 / 我卡住了; no 换一个
    expect(find.text('完成'), findsOneWidget);
    expect(find.text('我卡住了'), findsOneWidget);
    expect(find.text('换一个'), findsNothing);
  });

  // ── 换一个 button ─────────────────────────────────────────────────────────

  testWidgets('tap 换一个 → 调用onSkip()', (tester) async {
    final initial = _makeState(stepId: 'step-1');
    final next = _makeState(stepId: 'step-2', desc: '整理项目2的大纲');

    when(() => mockApi.postSession()).thenAnswer((_) async => initial);
    when(() => mockApi.getState()).thenAnswer((_) async => initial);
    when(() => mockApi.postStepSkip('step-1')).thenAnswer((_) async => next);

    await tester.pumpWidget(_buildApp(mockApi));
    await tester.pumpAndSettle();

    await tester.tap(find.text('换一个'));
    await tester.pumpAndSettle();

    verify(() => mockApi.postStepSkip('step-1')).called(1);
    expect(find.text('整理项目2的大纲'), findsOneWidget);
  });

  // ── 完成 button ───────────────────────────────────────────────────────────

  testWidgets('tap 完成 → onComplete()调用 + feedbackMessageProvider被设置',
      (tester) async {
    final initial = _makeState(stepId: 'step-1');
    final next = _makeState(stepId: 'step-2', desc: '整理项目2的大纲');

    when(() => mockApi.postSession()).thenAnswer((_) async => initial);
    when(() => mockApi.getState()).thenAnswer((_) async => initial);
    when(() => mockApi.postStepComplete('step-1')).thenAnswer(
      (_) async => (state: next, feedbackMessage: '项目1已推进'),
    );

    await tester.pumpWidget(_buildApp(mockApi));
    await tester.pumpAndSettle();

    await tester.tap(find.text('开始'));
    await tester.pump();

    await tester.tap(find.text('完成'));
    await tester.pumpAndSettle();

    verify(() => mockApi.postStepComplete('step-1')).called(1);
    expect(find.text('项目1已推进'), findsOneWidget);
    // Returns to idle after complete
    expect(find.text('开始'), findsOneWidget);

    // Advance clock to consume the 2-second auto-clear timer.
    await tester.pump(const Duration(seconds: 3));
  });

  // ── 我卡住了 button (executing) ───────────────────────────────────────────

  testWidgets('tap 我卡住了(executing态) → 调用onStuck()', (tester) async {
    final initial = _makeState(stepId: 'step-1');
    final next = _makeState(stepId: 'step-stuck', desc: '把第一句话缩短为10字以内');

    when(() => mockApi.postSession()).thenAnswer((_) async => initial);
    when(() => mockApi.getState()).thenAnswer((_) async => initial);
    when(() => mockApi.postStepStuck('step-1')).thenAnswer((_) async => next);

    await tester.pumpWidget(_buildApp(mockApi));
    await tester.pumpAndSettle();

    await tester.tap(find.text('开始'));
    await tester.pump();

    await tester.tap(find.text('我卡住了'));
    await tester.pumpAndSettle();

    verify(() => mockApi.postStepStuck('step-1')).called(1);
    expect(find.text('把第一句话缩短为10字以内'), findsOneWidget);
    // Returns to idle after stuck
    expect(find.text('开始'), findsOneWidget);
  });
}
