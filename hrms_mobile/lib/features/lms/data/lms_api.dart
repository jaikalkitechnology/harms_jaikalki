import 'package:dio/dio.dart';

import 'lms_models.dart';

class LmsApi {
  LmsApi(this._dio);
  final Dio _dio;

  static const _v1 = '/api/v1';

  Future<List<CourseSummary>> courses({String? category}) async {
    final res = await _dio.get<List<dynamic>>(
      '$_v1/lms/courses',
      queryParameters: category != null ? {'category': category} : null,
    );
    return (res.data ?? const [])
        .map((e) => CourseSummary.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<CourseDetail> getCourse(int id) async {
    final res = await _dio.get<Map<String, dynamic>>(
      '$_v1/lms/courses/$id',
    );
    return CourseDetail.fromJson(res.data!);
  }

  Future<Enrollment> enroll(int courseId) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/lms/courses/$courseId/enroll',
    );
    return Enrollment.fromJson(res.data!);
  }

  Future<List<Enrollment>> myCourses() async {
    final res = await _dio.get<List<dynamic>>('$_v1/lms/my-courses');
    return (res.data ?? const [])
        .map((e) => Enrollment.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Enrollment> completeLesson({
    required int lessonId,
    int timeSpentSeconds = 0,
    String? notes,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/lms/lessons/$lessonId/complete',
      data: {
        'time_spent_seconds': timeSpentSeconds,
        if (notes != null) 'notes': notes,
      },
    );
    return Enrollment.fromJson(res.data!);
  }

  Future<LearningStats> myStats() async {
    final res = await _dio.get<Map<String, dynamic>>('$_v1/lms/stats/me');
    return LearningStats.fromJson(res.data!);
  }
}
