import 'package:equatable/equatable.dart';

class LeaveType extends Equatable {
  const LeaveType({
    required this.id,
    required this.code,
    required this.name,
    required this.daysPerYear,
  });

  final int id;
  final String code;
  final String name;
  final num daysPerYear;

  factory LeaveType.fromJson(Map<String, dynamic> json) => LeaveType(
        id: json['id'] as int,
        code: json['code'] as String,
        name: json['name'] as String,
        daysPerYear: num.tryParse('${json['days_per_year']}') ?? 0,
      );

  @override
  List<Object?> get props => [id];
}

class LeaveBalance extends Equatable {
  const LeaveBalance({
    required this.id,
    required this.leaveTypeId,
    this.leaveType,
    required this.year,
    required this.allocated,
    required this.used,
    required this.balance,
  });

  final int id;
  final int leaveTypeId;
  final LeaveType? leaveType;
  final int year;
  final num allocated;
  final num used;
  final num balance;

  factory LeaveBalance.fromJson(Map<String, dynamic> json) => LeaveBalance(
        id: json['id'] as int,
        leaveTypeId: json['leave_type_id'] as int,
        leaveType: json['leave_type'] == null
            ? null
            : LeaveType.fromJson(json['leave_type'] as Map<String, dynamic>),
        year: json['year'] as int,
        allocated: num.tryParse('${json['allocated']}') ?? 0,
        used: num.tryParse('${json['used']}') ?? 0,
        balance: num.tryParse('${json['balance']}') ?? 0,
      );

  @override
  List<Object?> get props => [id, used, balance];
}

class LeaveRequest extends Equatable {
  const LeaveRequest({
    required this.id,
    required this.employeeId,
    required this.leaveTypeId,
    this.leaveType,
    required this.fromDate,
    required this.toDate,
    required this.days,
    required this.halfDay,
    this.reason,
    required this.status,
    required this.appliedAt,
    this.decisionComment,
  });

  final int id;
  final int employeeId;
  final int leaveTypeId;
  final LeaveType? leaveType;
  final String fromDate;
  final String toDate;
  final num days;
  final bool halfDay;
  final String? reason;
  final String status;
  final String appliedAt;
  final String? decisionComment;

  factory LeaveRequest.fromJson(Map<String, dynamic> json) => LeaveRequest(
        id: json['id'] as int,
        employeeId: json['employee_id'] as int,
        leaveTypeId: json['leave_type_id'] as int,
        leaveType: json['leave_type'] == null
            ? null
            : LeaveType.fromJson(json['leave_type'] as Map<String, dynamic>),
        fromDate: json['from_date'] as String,
        toDate: json['to_date'] as String,
        days: num.tryParse('${json['days']}') ?? 0,
        halfDay: (json['half_day'] as bool?) ?? false,
        reason: json['reason'] as String?,
        status: json['status'] as String,
        appliedAt: json['applied_at'] as String,
        decisionComment: json['decision_comment'] as String?,
      );

  @override
  List<Object?> get props => [id, status];
}
