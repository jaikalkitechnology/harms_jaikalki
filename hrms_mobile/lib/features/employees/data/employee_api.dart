import 'package:dio/dio.dart';

import 'employee_models.dart';

class EmployeeApi {
  EmployeeApi(this._dio);
  final Dio _dio;

  Future<List<EmployeeListItem>> list({String? search}) async {
    final res = await _dio.get<List<dynamic>>(
      '/api/v1/employees',
      queryParameters: {if (search != null && search.isNotEmpty) 'search': search},
    );
    return (res.data ?? const [])
        .map((e) => EmployeeListItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<EmployeeDetail> me() async {
    final res = await _dio.get<Map<String, dynamic>>('/api/v1/employees/me');
    return EmployeeDetail.fromJson(res.data!);
  }

  Future<EmployeeDetail> get(int id) async {
    final res = await _dio.get<Map<String, dynamic>>('/api/v1/employees/$id');
    return EmployeeDetail.fromJson(res.data!);
  }

  Future<SalaryBreakup> calculate(int templateId, {num? ctc}) async {
    final res = await _dio.get<Map<String, dynamic>>(
      '/api/v1/salary-templates/$templateId/calculate',
      queryParameters: {if (ctc != null) 'ctc': ctc},
    );
    return SalaryBreakup.fromJson(res.data!);
  }
}
