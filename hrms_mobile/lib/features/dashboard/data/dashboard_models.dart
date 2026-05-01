import 'package:equatable/equatable.dart';

class DashboardSummary extends Equatable {
  const DashboardSummary({
    required this.role,
    required this.userFullName,
    required this.companyName,
    required this.nextPaydayInDays,
    required this.todayAttendance,
    required this.leaveBalances,
    required this.pendingApprovalsCount,
    required this.pendingByType,
    required this.teamSize,
    required this.teamPresentToday,
    required this.teamAttendancePct,
    required this.teamToday,
    required this.birthdaysThisWeek,
    required this.probationExpiring,
    required this.totalHeadcount,
    required this.headcountByCategory,
    this.employeeCode,
  });

  final String? role;
  final String userFullName;
  final String? employeeCode;
  final String companyName;
  final int nextPaydayInDays;

  final TodayAttendance todayAttendance;
  final List<LeaveBalanceItem> leaveBalances;

  final int pendingApprovalsCount;
  final List<TypeCount> pendingByType;

  final int teamSize;
  final int teamPresentToday;
  final double teamAttendancePct;
  final List<TeamMember> teamToday;

  final List<BirthdayItem> birthdaysThisWeek;
  final List<ProbationExpiringItem> probationExpiring;

  final int totalHeadcount;
  final List<TypeCount> headcountByCategory;

  factory DashboardSummary.fromJson(Map<String, dynamic> json) {
    return DashboardSummary(
      role: json['role'] as String?,
      userFullName: (json['user_full_name'] as String?) ?? '',
      employeeCode: json['employee_code'] as String?,
      companyName: (json['company_name'] as String?) ?? '',
      nextPaydayInDays: (json['next_payday_in_days'] as int?) ?? 0,
      todayAttendance: TodayAttendance.fromJson(
        (json['today_attendance'] as Map?)?.cast<String, dynamic>() ?? const {},
      ),
      leaveBalances: ((json['leave_balances'] as List?) ?? const [])
          .map((e) => LeaveBalanceItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      pendingApprovalsCount: (json['pending_approvals_count'] as int?) ?? 0,
      pendingByType: ((json['pending_by_type'] as List?) ?? const [])
          .map((e) => TypeCount.fromJson(
                e as Map<String, dynamic>,
                keyName: 'request_type',
              ))
          .toList(),
      teamSize: (json['team_size'] as int?) ?? 0,
      teamPresentToday: (json['team_present_today'] as int?) ?? 0,
      teamAttendancePct: (json['team_attendance_pct'] as num?)?.toDouble() ?? 0.0,
      teamToday: ((json['team_today'] as List?) ?? const [])
          .map((e) => TeamMember.fromJson(e as Map<String, dynamic>))
          .toList(),
      birthdaysThisWeek: ((json['birthdays_today'] as List?) ?? const [])
          .map((e) => BirthdayItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      probationExpiring: ((json['probation_expiring_30d'] as List?) ?? const [])
          .map((e) =>
              ProbationExpiringItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      totalHeadcount: (json['total_headcount'] as int?) ?? 0,
      headcountByCategory: ((json['headcount_by_category'] as List?) ?? const [])
          .map((e) => TypeCount.fromJson(
                e as Map<String, dynamic>,
                keyName: 'category',
              ))
          .toList(),
    );
  }

  @override
  List<Object?> get props => [
        role,
        userFullName,
        nextPaydayInDays,
        todayAttendance,
        leaveBalances,
        pendingApprovalsCount,
        teamSize,
        teamAttendancePct,
        totalHeadcount,
      ];
}

class TodayAttendance extends Equatable {
  const TodayAttendance({
    this.checkedIn = false,
    this.checkedOut = false,
    this.checkIn,
    this.checkOut,
    this.status,
    this.workMode,
    this.distanceM,
  });
  final bool checkedIn;
  final bool checkedOut;
  final String? checkIn;
  final String? checkOut;
  final String? status;
  final String? workMode;
  final int? distanceM;

  factory TodayAttendance.fromJson(Map<String, dynamic> json) =>
      TodayAttendance(
        checkedIn: (json['checked_in'] as bool?) ?? false,
        checkedOut: (json['checked_out'] as bool?) ?? false,
        checkIn: json['check_in'] as String?,
        checkOut: json['check_out'] as String?,
        status: json['status'] as String?,
        workMode: json['work_mode'] as String?,
        distanceM: json['distance_m'] as int?,
      );

  @override
  List<Object?> get props =>
      [checkedIn, checkedOut, checkIn, checkOut, status];
}

class LeaveBalanceItem extends Equatable {
  const LeaveBalanceItem({
    required this.code,
    required this.name,
    required this.balance,
  });
  final String code;
  final String name;
  final num balance;

  factory LeaveBalanceItem.fromJson(Map<String, dynamic> json) =>
      LeaveBalanceItem(
        code: json['code'] as String,
        name: json['name'] as String,
        balance: num.tryParse('${json['balance']}') ?? 0,
      );

  @override
  List<Object?> get props => [code, balance];
}

class TypeCount extends Equatable {
  const TypeCount({required this.key, required this.count});
  final String key;
  final int count;

  factory TypeCount.fromJson(Map<String, dynamic> json,
          {required String keyName}) =>
      TypeCount(
        key: '${json[keyName]}',
        count: (json['count'] as int?) ?? 0,
      );

  @override
  List<Object?> get props => [key, count];
}

class TeamMember extends Equatable {
  const TeamMember({
    required this.employeeId,
    required this.employeeCode,
    required this.fullName,
    required this.statusToday,
  });
  final int employeeId;
  final String employeeCode;
  final String fullName;
  final String statusToday;

  factory TeamMember.fromJson(Map<String, dynamic> json) => TeamMember(
        employeeId: json['employee_id'] as int,
        employeeCode: json['employee_code'] as String,
        fullName: json['full_name'] as String,
        statusToday: (json['status_today'] as String?) ?? 'absent',
      );

  @override
  List<Object?> get props => [employeeId, statusToday];
}

class BirthdayItem extends Equatable {
  const BirthdayItem({
    required this.employeeId,
    required this.employeeCode,
    required this.fullName,
    this.dateOfBirth,
  });
  final int employeeId;
  final String employeeCode;
  final String fullName;
  final String? dateOfBirth;

  factory BirthdayItem.fromJson(Map<String, dynamic> json) => BirthdayItem(
        employeeId: json['employee_id'] as int,
        employeeCode: json['employee_code'] as String,
        fullName: json['full_name'] as String,
        dateOfBirth: json['date_of_birth'] as String?,
      );

  @override
  List<Object?> get props => [employeeId];
}

class ProbationExpiringItem extends Equatable {
  const ProbationExpiringItem({
    required this.employeeId,
    required this.employeeCode,
    required this.fullName,
    required this.probationEndDate,
    required this.daysRemaining,
  });
  final int employeeId;
  final String employeeCode;
  final String fullName;
  final String probationEndDate;
  final int daysRemaining;

  factory ProbationExpiringItem.fromJson(Map<String, dynamic> json) =>
      ProbationExpiringItem(
        employeeId: json['employee_id'] as int,
        employeeCode: json['employee_code'] as String,
        fullName: json['full_name'] as String,
        probationEndDate: json['probation_end_date'] as String,
        daysRemaining: (json['days_remaining'] as int?) ?? 0,
      );

  @override
  List<Object?> get props => [employeeId, daysRemaining];
}
