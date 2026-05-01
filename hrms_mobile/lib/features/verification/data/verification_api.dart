import 'package:dio/dio.dart';

import 'verification_models.dart';

class VerificationApi {
  VerificationApi(this._dio);
  final Dio _dio;

  static const _v1 = '/api/v1';

  Future<List<VerificationJob>> myQueue() async {
    final res = await _dio.get<List<dynamic>>('$_v1/verification/queue');
    return (res.data ?? const [])
        .map((e) => VerificationJob.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<VerificationTemplate> getTemplate(int id) async {
    final res = await _dio.get<Map<String, dynamic>>(
      '$_v1/verification/templates/$id',
    );
    return VerificationTemplate.fromJson(res.data!);
  }

  Future<VerificationJob> startJob(int id) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/verification/$id/start',
    );
    return VerificationJob.fromJson(res.data!);
  }

  Future<VerificationJob> submit({
    required int id,
    required Map<String, dynamic> formData,
    required String result,
    List<String>? photos,
    String? signatureUrl,
    double? lat,
    double? lng,
    String? remarks,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/verification/$id/submit',
      data: {
        'form_data': formData,
        'result': result,
        if (photos != null) 'photos': photos,
        if (signatureUrl != null) 'signature_url': signatureUrl,
        if (lat != null) 'geo_lat': lat,
        if (lng != null) 'geo_lng': lng,
        if (remarks != null) 'remarks': remarks,
      },
    );
    return VerificationJob.fromJson(res.data!);
  }
}
