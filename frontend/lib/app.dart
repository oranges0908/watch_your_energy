import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:watch_your_energy/pages/create_project_page.dart';
import 'package:watch_your_energy/pages/home_page.dart';
import 'package:watch_your_energy/pages/progress_page.dart';
import 'package:watch_your_energy/theme/app_theme.dart';

final _router = GoRouter(
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomePage(),
    ),
    GoRoute(
      path: '/progress',
      builder: (context, state) => const ProgressPage(),
    ),
    GoRoute(
      path: '/create',
      builder: (context, state) => const CreateProjectPage(),
    ),
  ],
);

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'WatchYourEnergy',
      theme: AppTheme.theme,
      routerConfig: _router,
    );
  }
}
