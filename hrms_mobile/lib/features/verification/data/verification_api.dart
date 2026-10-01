import 'package:dio/dio.dart';
import 'package:http_parser/http_parser.dart';
import 'package:image_picker/image_picker.dart' show XFile;

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

  /// Upload a verification photo / signature / document. Returns the
  /// public URL the backend stored it at, ready to be put into
  /// `form_data`, the `photos[]` list, or `signature_url`.
  Future<String> uploadFile({
    required XFile file,
    required String kind, // photo | signature | document
    String? fieldKey,
  }) async {
    // XFile.name is the real file name on web too (path is a blob: URL).
    final name = file.name.isNotEmpty ? file.name : file.path.split('/').last;
    final ext = name.split('.').last.toLowerCase();
    final mime = switch (ext) {
      'jpg' || 'jpeg' => MediaType('image', 'jpeg'),
      'png' => MediaType('image', 'png'),
      'webp' => MediaType('image', 'webp'),
      'heic' => MediaType('image', 'heic'),
      'pdf' => MediaType('application', 'pdf'),
      _ => MediaType('application', 'octet-stream'),
    };
    final form = FormData.fromMap({
      'kind': kind,
      if (fieldKey != null) 'field_key': fieldKey,
      'file': MultipartFile.fromBytes(
        await file.readAsBytes(),
        filename: name,
        contentType: mime,
      ),
    });
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/verification/upload',
      data: form,
    );
    final url = res.data?['url'];
    if (url is! String || url.isEmpty) {
      throw StateError('Upload succeeded but server returned no URL');
    }
    return url;
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
