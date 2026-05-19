import 'dart:io';

import 'package:dio/dio.dart';
import 'package:http_parser/http_parser.dart';

import 'attendance_models.dart';

class AttendanceApi {
  AttendanceApi(this._dio);
  final Dio _dio;

  Future<AttendanceRecord> checkInJson({
    required double lat,
    required double lng,
    required String workMode,
    String? selfieUrl,
    String? notes,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '/api/v1/attendance/check-in',
      data: {
        'lat': lat,
        'lng': lng,
        'work_mode': workMode,
        if (selfieUrl != null) 'selfie_url': selfieUrl,
        if (notes != null) 'notes': notes,
      },
    );
    return AttendanceRecord.fromJson(res.data!);
  }

  Future<AttendanceRecord> checkInWithSelfie({
    required double lat,
    required double lng,
    required String workMode,
    File? selfie,
    String? notes,
  }) async {
    final form = FormData.fromMap({
      'lat': lat,
      'lng': lng,
      'work_mode': workMode,
      if (notes != null) 'notes': notes,
      if (selfie != null)
        'selfie': await MultipartFile.fromFile(
          selfie.path,
          filename: 'selfie.jpg',
          contentType: MediaType('image', 'jpeg'),
        ),
    });
    final res = await _dio.post<Map<String, dynamic>>(
      '/api/v1/attendance/check-in/with-selfie',
      data: form,
    );
    return AttendanceRecord.fromJson(res.data!);
  }

  Future<AttendanceRecord> checkOut({double? lat, double? lng}) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '/api/v1/attendance/check-out',
      data: {
        if (lat != null) 'lat': lat,
        if (lng != null) 'lng': lng,
      },
    );
    return AttendanceRecord.fromJson(res.data!);
  }

  Future<AttendanceCalendar> myCalendar({required int year, required int month}) async {
    final res = await _dio.get<Map<String, dynamic>>(
      '/api/v1/attendance/me/calendar',
      queryParameters: {'year': year, 'month': month},
    );
    return AttendanceCalendar.fromJson(res.data!);
  }

  /// Employee self-marks one day. Backend allows today always, and
  /// back-dated only inside an admin-granted window.
  Future<AttendanceRecord> selfMark({
    required String date,
    required String status,
    String workMode = 'office',
    String? notes,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '/api/v1/attendance/me/mark',
      data: {
        'date': date,
        'status': status,
        'work_mode': workMode,
        if (notes != null) 'notes': notes,
      },
    );
    return AttendanceRecord.fromJson(res.data!);
  }

  Future<List<AttendanceRecord>> myRecords({String? from, String? to}) async {
    final res = await _dio.get<List<dynamic>>(
      '/api/v1/attendance/me',
      queryParameters: {
        if (from != null) 'from_date': from,
        if (to != null) 'to_date': to,
      },
    );
    return (res.data ?? const [])
        .map((e) => AttendanceRecord.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
