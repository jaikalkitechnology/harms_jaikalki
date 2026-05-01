import 'package:dio/dio.dart';

import 'dashboard_models.dart';

class DashboardApi {
  DashboardApi(this._dio);
  final Dio _dio;

  Future<DashboardSummary> me() async {
    final res = await _dio.get<Map<String, dynamic>>('/api/v1/dashboard/me');
    return DashboardSummary.fromJson(res.data!);
  }
}
