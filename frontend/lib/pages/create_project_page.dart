import 'package:flutter/material.dart';

/// Skeleton create-project page — full UI implemented in I6.
class CreateProjectPage extends StatelessWidget {
  const CreateProjectPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('新建项目')),
      body: const Center(child: Text('新建项目页（I6实现）')),
    );
  }
}
