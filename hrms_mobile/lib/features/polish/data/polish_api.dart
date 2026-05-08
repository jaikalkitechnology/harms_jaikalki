import 'package:dio/dio.dart';

import 'polish_models.dart';

class PolishApi {
  PolishApi(this._dio);
  final Dio _dio;

  static const _v1 = '/api/v1';

  Future<List<Asset>> myAssets() async {
    final res = await _dio.get<List<dynamic>>('$_v1/polish/assets/me');
    return (res.data ?? const [])
        .map((e) => Asset.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<MeetingRoom>> rooms() async {
    final res = await _dio.get<List<dynamic>>('$_v1/polish/rooms');
    return (res.data ?? const [])
        .map((e) => MeetingRoom.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<RoomBooking> bookRoom({
    required int roomId,
    required String title,
    required String startTime,
    required String endTime,
    String? notes,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/polish/rooms/bookings',
      data: {
        'room_id': roomId,
        'title': title,
        'start_time': startTime,
        'end_time': endTime,
        if (notes != null) 'notes': notes,
      },
    );
    return RoomBooking.fromJson(res.data!);
  }

  Future<List<RoomBooking>> myBookings() async {
    final res =
        await _dio.get<List<dynamic>>('$_v1/polish/rooms/bookings/me');
    return (res.data ?? const [])
        .map((e) => RoomBooking.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<RoomBooking> cancelBooking(int bookingId) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/polish/rooms/bookings/$bookingId/cancel',
    );
    return RoomBooking.fromJson(res.data!);
  }

  Future<List<JobPosting>> publishedJobs() async {
    final res = await _dio.get<List<dynamic>>(
      '$_v1/polish/jobs',
      queryParameters: {
        'status': 'published',
        'published_to_app': true,
      },
    );
    return (res.data ?? const [])
        .map((e) => JobPosting.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<JobApplication> applyToJob({
    required int postingId,
    int? referrerEmployeeId,
    String? coverNote,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/polish/jobs/$postingId/apply',
      data: {
        if (referrerEmployeeId != null)
          'referrer_employee_id': referrerEmployeeId,
        if (coverNote != null) 'cover_note': coverNote,
      },
    );
    return JobApplication.fromJson(res.data!);
  }

  Future<List<JobApplication>> myApplications() async {
    final res =
        await _dio.get<List<dynamic>>('$_v1/polish/jobs/me/applications');
    return (res.data ?? const [])
        .map((e) => JobApplication.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> preRegisterVisitor({
    required String fullName,
    required String purpose,
    required String expectedAt,
    String? company,
    String? contactPhone,
  }) async {
    await _dio.post(
      '$_v1/polish/visitors',
      data: {
        'full_name': fullName,
        'purpose': purpose,
        'expected_at': expectedAt,
        if (company != null) 'company': company,
        if (contactPhone != null) 'contact_phone': contactPhone,
      },
    );
  }
}
