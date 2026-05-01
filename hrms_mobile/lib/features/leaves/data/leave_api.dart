import 'package:dio/dio.dart';

import 'leave_models.dart';

class LeaveApi {
  LeaveApi(this._dio);
  final Dio _dio;

  Future<List<LeaveType>> types() async {
    final res = await _dio.get<List<dynamic>>('/api/v1/leaves/types');
    return (res.data ?? const [])
        .map((e) => LeaveType.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<LeaveBalance>> balance() async {
    final res = await _dio.get<List<dynamic>>('/api/v1/leaves/balance');
    return (res.data ?? const [])
        .map((e) => LeaveBalance.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<LeaveRequest>> myRequests() async {
    final res = await _dio.get<List<dynamic>>('/api/v1/leaves/requests');
    return (res.data ?? const [])
        .map((e) => LeaveRequest.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<LeaveRequest>> pending() async {
    final res =
        await _dio.get<List<dynamic>>('/api/v1/leaves/pending-approvals');
    return (res.data ?? const [])
        .map((e) => LeaveRequest.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<LeaveRequest> apply({
    required int leaveTypeId,
    required String fromDate,
    required String toDate,
    String? reason,
    bool halfDay = false,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '/api/v1/leaves/apply',
      data: {
        'leave_type_id': leaveTypeId,
        'from_date': fromDate,
        'to_date': toDate,
        if (reason != null) 'reason': reason,
        'half_day': halfDay,
      },
    );
    return LeaveRequest.fromJson(res.data!);
  }

  Future<LeaveRequest> approve(int id, {String? comment}) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '/api/v1/leaves/$id/approve',
      data: {'decision_comment': comment},
    );
    return LeaveRequest.fromJson(res.data!);
  }

  Future<LeaveRequest> reject(int id, {String? comment}) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '/api/v1/leaves/$id/reject',
      data: {'decision_comment': comment},
    );
    return LeaveRequest.fromJson(res.data!);
  }

  Future<LeaveRequest> cancel(int id) async {
    final res =
        await _dio.delete<Map<String, dynamic>>('/api/v1/leaves/requests/$id');
    return LeaveRequest.fromJson(res.data!);
  }
}
