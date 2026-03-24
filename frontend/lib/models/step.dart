class StepModel {
  final String id;
  final String description;
  final int estimatedMin;
  final String pattern;
  final String stepType;
  final String blockTitle;
  final String energyLevel;

  const StepModel({
    required this.id,
    required this.description,
    required this.estimatedMin,
    required this.pattern,
    required this.stepType,
    required this.blockTitle,
    required this.energyLevel,
  });

  bool get isLowEnergy => energyLevel == 'low';

  factory StepModel.fromJson(Map<String, dynamic> json) {
    return StepModel(
      id: json['id'] as String,
      description: json['description'] as String,
      estimatedMin: json['estimated_min'] as int,
      pattern: json['pattern'] as String,
      stepType: json['step_type'] as String,
      blockTitle: json['block_title'] as String,
      energyLevel: json['energy_level'] as String,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) || other is StepModel && id == other.id;

  @override
  int get hashCode => id.hashCode;
}
