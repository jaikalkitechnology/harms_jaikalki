import 'package:dio/dio.dart';

import 'justice_models.dart';

class JusticeApi {
  JusticeApi(this._dio);
  final Dio _dio;

  Future<List<ComplaintListItem>> myComplaints() async {
    final res = await _dio.get<List<dynamic>>('/api/v1/justice/me');
    return (res.data ?? const [])
        .map((e) => ComplaintListItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<ComplaintListItem> submit({
    required String complaintType,
    required String privacyLevel,
    required String severity,
    required String subject,
    required String description,
    String? desiredOutcome,
    String? incidentDate,
    String? incidentLocation,
    List<Map<String, dynamic>> accused = const [],
    List<Map<String, dynamic>> witnesses = const [],
    List<Map<String, dynamic>> evidence = const [],
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '/api/v1/justice/submit',
      data: {
        'complaint_type': complaintType,
        'privacy_level': privacyLevel,
        'severity': severity,
        'subject': subject,
        'description': description,
        if (desiredOutcome != null) 'desired_outcome': desiredOutcome,
        if (incidentDate != null) 'incident_date': incidentDate,
        if (incidentLocation != null) 'incident_location': incidentLocation,
        'accused': accused,
        'witnesses': witnesses,
        'evidence': evidence,
      },
    );
    return ComplaintListItem.fromJson(res.data!);
  }

  Future<Resources> resources() async {
    final res =
        await _dio.get<Map<String, dynamic>>('/api/v1/justice/resources');
    return Resources.fromJson(res.data!);
  }
}
