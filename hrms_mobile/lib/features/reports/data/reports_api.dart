import 'package:dio/dio.dart';

import 'reports_models.dart';

class ReportsApi {
  ReportsApi(this._dio);
  final Dio _dio;

  static const _v1 = '/api/v1';

  Future<DirectorDashboard> directorDashboard() async {
    final res = await _dio.get<Map<String, dynamic>>(
      '$_v1/reports/director-dashboard',
    );
    return DirectorDashboard.fromJson(res.data!);
  }
}
