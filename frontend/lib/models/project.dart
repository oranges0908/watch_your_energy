class ProjectModel {
  final String id;
  final String title;
  final int progressPct;

  const ProjectModel({
    required this.id,
    required this.title,
    required this.progressPct,
  });

  factory ProjectModel.fromJson(Map<String, dynamic> json) {
    return ProjectModel(
      id: json['id'] as String,
      title: json['title'] as String,
      progressPct: json['progress_pct'] as int,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is ProjectModel && id == other.id;

  @override
  int get hashCode => id.hashCode;
}

class BlockModel {
  final String id;
  final String title;
  final int position;
  final String status;
  final int progressPct;

  const BlockModel({
    required this.id,
    required this.title,
    required this.position,
    required this.status,
    required this.progressPct,
  });

  factory BlockModel.fromJson(Map<String, dynamic> json) {
    return BlockModel(
      id: json['id'] as String,
      title: json['title'] as String,
      position: json['position'] as int,
      status: json['status'] as String,
      progressPct: json['progress_pct'] as int,
    );
  }

  bool get isCompleted => status == 'completed';
}
