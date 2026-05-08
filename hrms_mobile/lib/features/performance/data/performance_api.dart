import 'package:dio/dio.dart';

import 'performance_models.dart';

class PerformanceApi {
  PerformanceApi(this._dio);
  final Dio _dio;

  static const _v1 = '/api/v1';

  Future<List<Goal>> myGoals({int? cycleId}) async {
    final res = await _dio.get<List<dynamic>>(
      '$_v1/performance/goals/me',
      queryParameters: cycleId != null ? {'cycle_id': cycleId} : null,
    );
    return (res.data ?? const [])
        .map((e) => Goal.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Goal> createGoal({
    required String title,
    int? cycleId,
    String? description,
    int weightPct = 100,
    String category = 'business',
    String? dueDate,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/performance/goals',
      data: {
        'title': title,
        if (cycleId != null) 'cycle_id': cycleId,
        if (description != null) 'description': description,
        'weight_pct': weightPct,
        'category': category,
        if (dueDate != null) 'due_date': dueDate,
      },
    );
    return Goal.fromJson(res.data!);
  }

  Future<Goal> updateGoal({
    required int goalId,
    int? progressPct,
    String? status,
  }) async {
    final res = await _dio.patch<Map<String, dynamic>>(
      '$_v1/performance/goals/$goalId',
      data: {
        if (progressPct != null) 'progress_pct': progressPct,
        if (status != null) 'status': status,
      },
    );
    return Goal.fromJson(res.data!);
  }

  Future<List<PerfReview>> myReviews({int? cycleId}) async {
    final res = await _dio.get<List<dynamic>>(
      '$_v1/performance/reviews/me',
      queryParameters: cycleId != null ? {'cycle_id': cycleId} : null,
    );
    return (res.data ?? const [])
        .map((e) => PerfReview.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<PerfReview> submitSelfReview({
    required int cycleId,
    double? overallRating,
    String? achievements,
    String? improvementAreas,
    String? recommendations,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/performance/cycles/$cycleId/self-review',
      data: {
        if (overallRating != null) 'overall_rating': overallRating,
        if (achievements != null) 'achievements': achievements,
        if (improvementAreas != null) 'improvement_areas': improvementAreas,
        if (recommendations != null) 'recommendations': recommendations,
      },
    );
    return PerfReview.fromJson(res.data!);
  }

  Future<PerfReview> acknowledgeReview(int reviewId) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/performance/reviews/$reviewId/acknowledge',
    );
    return PerfReview.fromJson(res.data!);
  }

  Future<List<FeedbackRequest>> pendingFeedback() async {
    final res =
        await _dio.get<List<dynamic>>('$_v1/performance/feedback/me/pending');
    return (res.data ?? const [])
        .map((e) => FeedbackRequest.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> submitFeedback({
    required int requestId,
    required double rating,
    String? strengths,
    String? improvementAreas,
    Map<String, dynamic>? competencies,
  }) async {
    await _dio.post(
      '$_v1/performance/feedback/requests/$requestId/respond',
      data: {
        'overall_rating': rating,
        if (strengths != null) 'strengths': strengths,
        if (improvementAreas != null) 'improvement_areas': improvementAreas,
        if (competencies != null) 'competencies': competencies,
      },
    );
  }
}
