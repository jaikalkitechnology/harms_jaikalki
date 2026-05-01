import 'package:dio/dio.dart';

import 'exam_models.dart';

class ExamApi {
  ExamApi(this._dio);
  final Dio _dio;

  static const _v1 = '/api/v1';

  Future<List<ExamSummary>> exams() async {
    final res = await _dio.get<List<dynamic>>('$_v1/exams/');
    return (res.data ?? const [])
        .map((e) => ExamSummary.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<ExamSession> start(int examId) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/exams/$examId/start',
    );
    return ExamSession.fromJson(res.data!);
  }

  Future<void> flag({
    required int attemptId,
    required String flagType,
    String? note,
  }) async {
    await _dio.post(
      '$_v1/exams/attempts/$attemptId/flag',
      data: {
        'flag_type': flagType,
        if (note != null) 'note': note,
      },
    );
  }

  Future<AttemptResult> submit({
    required int attemptId,
    required List<Map<String, dynamic>> answers,
    List<Map<String, dynamic>>? cheatingFlags,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/exams/attempts/$attemptId/submit',
      data: {
        'answers': answers,
        'cheating_flags': cheatingFlags ?? [],
      },
    );
    return AttemptResult.fromJson(res.data!);
  }

  Future<List<AttemptResult>> myAttempts() async {
    final res = await _dio.get<List<dynamic>>('$_v1/exams/me/attempts');
    return (res.data ?? const [])
        .map((e) => AttemptResult.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<CertificateOut>> myCertificates() async {
    final res = await _dio.get<List<dynamic>>('$_v1/exams/me/certificates');
    return (res.data ?? const [])
        .map((e) => CertificateOut.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
