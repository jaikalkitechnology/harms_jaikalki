import 'package:equatable/equatable.dart';

class InternExpense extends Equatable {
  const InternExpense({
    required this.id,
    required this.expenseDate,
    required this.expenseType,
    required this.amount,
    this.description,
    this.receiptUrl,
    required this.status,
    this.rejectionReason,
  });

  final int id;
  final String expenseDate;
  final String expenseType;
  final num amount;
  final String? description;
  final String? receiptUrl;
  final String status;
  final String? rejectionReason;

  factory InternExpense.fromJson(Map<String, dynamic> json) => InternExpense(
        id: json['id'] as int,
        expenseDate: json['expense_date'] as String,
        expenseType: json['expense_type'] as String,
        amount: num.tryParse('${json['amount']}') ?? 0,
        description: json['description'] as String?,
        receiptUrl: json['receipt_url'] as String?,
        status: json['status'] as String,
        rejectionReason: json['rejection_reason'] as String?,
      );

  @override
  List<Object?> get props => [id, status];
}
