import 'package:equatable/equatable.dart';

class Goal extends Equatable {
  const Goal({
    required this.id,
    required this.title,
    required this.weightPct,
    required this.progressPct,
    required this.category,
    required this.status,
    this.description,
    this.metric,
    this.targetValue,
    this.dueDate,
  });

  final int id;
  final String title;
  final String? description;
  final String? metric;
  final String? targetValue;
  final int weightPct;
  final int progressPct;
  final String category;
  final String status;
  final String? dueDate;

  factory Goal.fromJson(Map<String, dynamic> j) => Goal(
        id: j['id'] as int,
        title: j['title'] as String,
        description: j['description'] as String?,
        metric: j['metric'] as String?,
        targetValue: j['target_value'] as String?,
        weightPct: (j['weight_pct'] as int?) ?? 0,
        progressPct: (j['progress_pct'] as int?) ?? 0,
        category: j['category'] as String,
        status: j['status'] as String,
        dueDate: j['due_date'] as String?,
      );

  @override
  List<Object?> get props => [id, status, progressPct];
}

class Cycle extends Equatable {
  const Cycle({
    required this.id,
    required this.code,
    required this.name,
    required this.cycleType,
    required this.periodStart,
    required this.periodEnd,
    required this.status,
  });

  final int id;
  final String code;
  final String name;
  final String cycleType;
  final String periodStart;
  final String periodEnd;
  final String status;

  factory Cycle.fromJson(Map<String, dynamic> j) => Cycle(
        id: j['id'] as int,
        code: j['code'] as String,
        name: j['name'] as String,
        cycleType: j['cycle_type'] as String,
        periodStart: j['period_start'] as String,
        periodEnd: j['period_end'] as String,
        status: j['status'] as String,
      );

  @override
  List<Object?> get props => [id, status];
}

class PerfReview extends Equatable {
  const PerfReview({
    required this.id,
    required this.cycleId,
    required this.reviewType,
    required this.status,
    this.overallRating,
    this.achievements,
    this.improvementAreas,
    this.recommendations,
    this.incrementRecommendationPct,
  });

  final int id;
  final int cycleId;
  final String reviewType;
  final String status;
  final double? overallRating;
  final String? achievements;
  final String? improvementAreas;
  final String? recommendations;
  final int? incrementRecommendationPct;

  factory PerfReview.fromJson(Map<String, dynamic> j) => PerfReview(
        id: j['id'] as int,
        cycleId: j['cycle_id'] as int,
        reviewType: j['review_type'] as String,
        status: j['status'] as String,
        overallRating: j['overall_rating'] != null
            ? double.tryParse(j['overall_rating'].toString())
            : null,
        achievements: j['achievements'] as String?,
        improvementAreas: j['improvement_areas'] as String?,
        recommendations: j['recommendations'] as String?,
        incrementRecommendationPct:
            j['increment_recommendation_pct'] as int?,
      );

  @override
  List<Object?> get props => [id, status];
}

class FeedbackRequest extends Equatable {
  const FeedbackRequest({
    required this.id,
    required this.subjectEmployeeId,
    required this.relation,
    required this.isAnonymous,
    required this.status,
  });

  final int id;
  final int subjectEmployeeId;
  final String relation;
  final bool isAnonymous;
  final String status;

  factory FeedbackRequest.fromJson(Map<String, dynamic> j) => FeedbackRequest(
        id: j['id'] as int,
        subjectEmployeeId: j['subject_employee_id'] as int,
        relation: j['relation'] as String,
        isAnonymous: (j['is_anonymous'] as bool?) ?? true,
        status: j['status'] as String,
      );

  @override
  List<Object?> get props => [id, status];
}
