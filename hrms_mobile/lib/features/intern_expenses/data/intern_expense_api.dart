import 'package:dio/dio.dart';

import 'intern_expense_models.dart';

class InternExpenseApi {
  InternExpenseApi(this._dio);
  final Dio _dio;

  Future<List<InternExpense>> mine({String? status}) async {
    final res = await _dio.get<List<dynamic>>(
      '/api/v1/interns/expenses/me',
      queryParameters: {if (status != null) 'status': status},
    );
    return (res.data ?? const [])
        .map((e) => InternExpense.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<InternExpense> submit({
    required String expenseDate,
    required String expenseType,
    required num amount,
    String? description,
    String? receiptUrl,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '/api/v1/interns/expenses',
      data: {
        'expense_date': expenseDate,
        'expense_type': expenseType,
        'amount': amount,
        if (description != null) 'description': description,
        if (receiptUrl != null) 'receipt_url': receiptUrl,
      },
    );
    return InternExpense.fromJson(res.data!);
  }
}
