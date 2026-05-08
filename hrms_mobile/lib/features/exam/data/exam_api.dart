import 'dart:io';

import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';

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

  /// Download the certificate PDF and save it to the app's downloads
  /// directory. Returns the local file path so callers can open or
  /// share it.
  Future<File> downloadCertificate(CertificateOut cert) async {
    final res = await _dio.get<List<int>>(
      '$_v1/exams/certificates/${cert.id}/pdf',
      options: Options(
        responseType: ResponseType.bytes,
        followRedirects: true,
      ),
    );
    final bytes = res.data ?? const <int>[];
    if (bytes.isEmpty) {
      throw StateError('Empty PDF response');
    }
    final dir = await _writableDir();
    final safe = cert.certificateNumber.replaceAll(RegExp(r'[^A-Za-z0-9._-]'), '-');
    final file = File('${dir.path}/$safe.pdf');
    await file.writeAsBytes(bytes, flush: true);
    return file;
  }

  Future<Directory> _writableDir() async {
    try {
      return await getApplicationDocumentsDirectory();
    } catch (_) {
      return Directory.systemTemp;
    }
  }
}
