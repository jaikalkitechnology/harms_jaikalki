import 'package:dio/dio.dart';

import 'approval_models.dart';

class ApprovalApi {
  ApprovalApi(this._dio);
  final Dio _dio;

  Future<List<ApprovalItem>> inbox({String? requestType}) async {
    final res = await _dio.get<List<dynamic>>(
      '/api/v1/approvals/inbox',
      queryParameters: {
        if (requestType != null) 'request_type': requestType,
      },
    );
    return (res.data ?? const [])
        .map((e) => ApprovalItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<ApprovalCount>> counts() async {
    final res = await _dio.get<List<dynamic>>('/api/v1/approvals/inbox/counts');
    return (res.data ?? const [])
        .map((e) => ApprovalCount.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<ApprovalItem> approve(int id, {String? comments}) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '/api/v1/approvals/$id/approve',
      data: {'comments': comments},
    );
    return ApprovalItem.fromJson(res.data!);
  }

  Future<ApprovalItem> reject(int id, {String? comments}) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '/api/v1/approvals/$id/reject',
      data: {'comments': comments},
    );
    return ApprovalItem.fromJson(res.data!);
  }
}
