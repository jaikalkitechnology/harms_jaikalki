import 'package:dio/dio.dart';

import '../../../core/constants/app_constants.dart';
import 'payroll_models.dart';

class PayrollApi {
  PayrollApi(this._dio);
  final Dio _dio;

  Future<List<Payslip>> myPayslips() async {
    final res = await _dio.get<List<dynamic>>('/api/v1/payroll/payslips/me');
    return (res.data ?? const [])
        .map((e) => Payslip.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  String payslipPdfUrl(int payslipId) =>
      '${AppConstants.apiBaseUrl}/api/v1/payroll/payslips/$payslipId/pdf';

  /// Download the payslip PDF through the authenticated client.
  /// Launching the raw URL in a browser fails with 403 (no token).
  Future<List<int>> downloadPayslipPdf(int payslipId) async {
    final res = await _dio.get<List<int>>(
      '/api/v1/payroll/payslips/$payslipId/pdf',
      options: Options(responseType: ResponseType.bytes),
    );
    return res.data ?? const <int>[];
  }

  Future<List<Reimbursement>> myReimbursements() async {
    final res = await _dio.get<List<dynamic>>(
      '/api/v1/payroll/reimbursements/me',
    );
    return (res.data ?? const [])
        .map((e) => Reimbursement.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Reimbursement> submitReimbursement({
    required String category,
    required num amount,
    required String billDate,
    String? description,
    String? billUrl,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '/api/v1/payroll/reimbursements',
      data: {
        'category': category,
        'amount': amount,
        'bill_date': billDate,
        if (description != null) 'description': description,
        if (billUrl != null) 'bill_url': billUrl,
      },
    );
    return Reimbursement.fromJson(res.data!);
  }
}
