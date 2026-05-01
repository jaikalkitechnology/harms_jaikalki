import 'package:equatable/equatable.dart';

class Payslip extends Equatable {
  const Payslip({
    required this.id,
    required this.year,
    required this.month,
    required this.basic,
    required this.hra,
    required this.gross,
    required this.totalDeductions,
    required this.netPay,
    required this.daysPaid,
    required this.daysLop,
  });

  final int id;
  final int year;
  final int month;
  final num basic;
  final num hra;
  final num gross;
  final num totalDeductions;
  final num netPay;
  final num daysPaid;
  final num daysLop;

  factory Payslip.fromJson(Map<String, dynamic> json) => Payslip(
        id: json['id'] as int,
        year: json['year'] as int,
        month: json['month'] as int,
        basic: num.tryParse('${json['basic']}') ?? 0,
        hra: num.tryParse('${json['hra']}') ?? 0,
        gross: num.tryParse('${json['gross']}') ?? 0,
        totalDeductions: num.tryParse('${json['total_deductions']}') ?? 0,
        netPay: num.tryParse('${json['net_pay']}') ?? 0,
        daysPaid: num.tryParse('${json['days_paid']}') ?? 0,
        daysLop: num.tryParse('${json['days_lop']}') ?? 0,
      );

  @override
  List<Object?> get props => [id];
}

class Reimbursement extends Equatable {
  const Reimbursement({
    required this.id,
    required this.category,
    required this.amount,
    required this.billDate,
    required this.status,
    this.description,
    this.rejectionReason,
  });

  final int id;
  final String category;
  final num amount;
  final String billDate;
  final String status;
  final String? description;
  final String? rejectionReason;

  factory Reimbursement.fromJson(Map<String, dynamic> json) => Reimbursement(
        id: json['id'] as int,
        category: json['category'] as String,
        amount: num.tryParse('${json['amount']}') ?? 0,
        billDate: json['bill_date'] as String,
        status: json['status'] as String,
        description: json['description'] as String?,
        rejectionReason: json['rejection_reason'] as String?,
      );

  @override
  List<Object?> get props => [id, status];
}
