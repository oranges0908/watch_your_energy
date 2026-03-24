import 'package:flutter/material.dart';

/// Skeleton progress page — full UI implemented in I6.
class ProgressPage extends StatelessWidget {
  const ProgressPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('项目进展')),
      body: const Center(child: Text('进展页（I6实现）')),
    );
  }
}
