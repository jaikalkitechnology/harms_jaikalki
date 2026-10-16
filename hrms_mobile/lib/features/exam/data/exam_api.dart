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

  /// Certificate PDF bytes plus a file name — works on web too.
  /// The certificate file — a generated PDF, or whatever HR uploaded
  /// (PDF or image).
  Future<({List<int> bytes, String filename, String mimeType})> certificatePdf(
    CertificateOut cert,
  ) async {
    final res = await _dio.get<List<int>>(
      '$_v1/exams/certificates/${cert.id}/pdf',
      options: Options(responseType: ResponseType.bytes),
    );
    final bytes = res.data ?? const <int>[];
    if (bytes.isEmpty) throw StateError('Empty PDF response');
    final mime = (res.headers.value('content-type') ?? 'application/pdf')
        .split(';')
        .first
        .trim();
    const ext = {
      'image/png': 'png',
      'image/jpeg': 'jpg',
      'image/webp': 'webp',
    };
    final safe =
        cert.certificateNumber.replaceAll(RegExp(r'[^A-Za-z0-9._-]'), '-');
    return (
      bytes: bytes,
      filename: '$safe.${ext[mime] ?? 'pdf'}',
      mimeType: mime,
    );
  }
}
