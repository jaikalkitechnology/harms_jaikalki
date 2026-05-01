import 'package:dio/dio.dart';

import 'field_models.dart';

class FieldApi {
  FieldApi(this._dio);
  final Dio _dio;

  static const _v1 = '/api/v1';

  Future<List<FieldJob>> myJobsToday() async {
    final res = await _dio.get<List<dynamic>>('$_v1/field/jobs/today');
    return (res.data ?? const [])
        .map((e) => FieldJob.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<FieldJob>> myJobs({String? date}) async {
    final res = await _dio.get<List<dynamic>>(
      '$_v1/field/jobs/me',
      queryParameters: date != null ? {'date': date} : null,
    );
    return (res.data ?? const [])
        .map((e) => FieldJob.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Visit> checkIn({
    required int jobId,
    required double lat,
    required double lng,
    required String selfieUrl,
    bool isMock = false,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/field/jobs/$jobId/checkin',
      data: {
        'lat': lat,
        'lng': lng,
        'is_mock': isMock,
        'selfie_url': selfieUrl,
      },
    );
    return Visit.fromJson(res.data!);
  }

  Future<Visit> submitVisitForm({
    required int visitId,
    required Map<String, dynamic> visitForm,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/field/visits/$visitId/visit-form',
      data: {'visit_form': visitForm},
    );
    return Visit.fromJson(res.data!);
  }

  Future<VisitPhoto> addPhoto({
    required int visitId,
    required String photoUrl,
    String photoType = 'other',
    double? lat,
    double? lng,
    bool watermarked = false,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/field/visits/$visitId/photos',
      data: {
        'photo_url': photoUrl,
        'photo_type': photoType,
        if (lat != null) 'geo_lat': lat,
        if (lng != null) 'geo_lng': lng,
        'watermarked': watermarked,
      },
    );
    return VisitPhoto.fromJson(res.data!);
  }

  Future<Visit> checkOut({
    required int visitId,
    double? lat,
    double? lng,
    String? outcome,
    String? notes,
    String? signatureUrl,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/field/visits/$visitId/checkout',
      data: {
        if (lat != null) 'lat': lat,
        if (lng != null) 'lng': lng,
        if (outcome != null) 'outcome': outcome,
        if (notes != null) 'notes': notes,
        if (signatureUrl != null) 'signature_url': signatureUrl,
      },
    );
    return Visit.fromJson(res.data!);
  }

  Future<Visit> getVisit(int visitId) async {
    final res = await _dio.get<Map<String, dynamic>>(
      '$_v1/field/visits/$visitId',
    );
    return Visit.fromJson(res.data!);
  }

  Future<void> trackLocation({
    required double lat,
    required double lng,
    int? accuracyM,
    int? batteryPct,
    bool isMock = false,
  }) async {
    await _dio.post(
      '$_v1/field/location/track',
      data: {
        'lat': lat,
        'lng': lng,
        if (accuracyM != null) 'accuracy_m': accuracyM,
        if (batteryPct != null) 'battery_pct': batteryPct,
        'is_mock': isMock,
      },
    );
  }

  Future<List<LiveMapEntry>> teamLiveMap() async {
    final res = await _dio.get<List<dynamic>>('$_v1/field/team/live-map');
    return (res.data ?? const [])
        .map((e) => LiveMapEntry.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
