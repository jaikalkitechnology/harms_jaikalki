import 'package:dio/dio.dart';

import 'dwp_models.dart';

class DwpApi {
  DwpApi(this._dio);
  final Dio _dio;

  Future<DwpTemplateWithPrefill> morningTemplate() async {
    final res =
        await _dio.get<Map<String, dynamic>>('/api/v1/dwp/template/morning');
    return DwpTemplateWithPrefill.fromJson(res.data!);
  }

  Future<DwpTemplateWithPrefill> eodTemplate() async {
    final res = await _dio.get<Map<String, dynamic>>('/api/v1/dwp/template/eod');
    return DwpTemplateWithPrefill.fromJson(res.data!);
  }

  Future<DwpSubmission> submitMorning({
    required int templateId,
    required Map<String, dynamic> fields,
    num? totalHours,
    int? moodRating,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '/api/v1/dwp/morning/submit',
      data: {
        'template_id': templateId,
        'fields': fields,
        if (totalHours != null) 'total_hours': totalHours,
        if (moodRating != null) 'mood_rating': moodRating,
      },
    );
    return DwpSubmission.fromJson(res.data!);
  }

  Future<DwpSubmission> submitEod({
    required int templateId,
    required Map<String, dynamic> fields,
    num? totalHours,
    int? moodRating,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '/api/v1/dwp/eod/submit',
      data: {
        'template_id': templateId,
        'fields': fields,
        if (totalHours != null) 'total_hours': totalHours,
        if (moodRating != null) 'mood_rating': moodRating,
      },
    );
    return DwpSubmission.fromJson(res.data!);
  }

  Future<List<DwpSubmission>> myToday() async {
    final res = await _dio.get<List<dynamic>>('/api/v1/dwp/me/today');
    return (res.data ?? const [])
        .map((e) => DwpSubmission.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<DwpSubmission>> myHistory({int limit = 30}) async {
    final res = await _dio.get<List<dynamic>>(
      '/api/v1/dwp/me/history',
      queryParameters: {'limit': limit},
    );
    return (res.data ?? const [])
        .map((e) => DwpSubmission.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
