import 'package:equatable/equatable.dart';

class HeadcountPoint extends Equatable {
  const HeadcountPoint({
    required this.period,
    required this.headcount,
    required this.joined,
    required this.exited,
  });

  final String period;
  final int headcount;
  final int joined;
  final int exited;

  factory HeadcountPoint.fromJson(Map<String, dynamic> j) => HeadcountPoint(
        period: j['period'] as String,
        headcount: (j['headcount'] as int?) ?? 0,
        joined: (j['joined'] as int?) ?? 0,
        exited: (j['exited'] as int?) ?? 0,
      );

  @override
  List<Object?> get props => [period];
}

class HeadcountTrend extends Equatable {
  const HeadcountTrend({
    required this.months,
    required this.points,
    required this.currentHeadcount,
  });

  final int months;
  final List<HeadcountPoint> points;
  final int currentHeadcount;

  factory HeadcountTrend.fromJson(Map<String, dynamic> j) => HeadcountTrend(
        months: (j['months'] as int?) ?? 12,
        points: ((j['points'] as List?) ?? const [])
            .map((e) => HeadcountPoint.fromJson(e as Map<String, dynamic>))
            .toList(),
        currentHeadcount: (j['current_headcount'] as int?) ?? 0,
      );

  @override
  List<Object?> get props => [months, currentHeadcount];
}

class DepartmentBreakdown extends Equatable {
  const DepartmentBreakdown({required this.department, required this.headcount});
  final String department;
  final int headcount;

  factory DepartmentBreakdown.fromJson(Map<String, dynamic> j) =>
      DepartmentBreakdown(
        department: j['department'] as String,
        headcount: (j['headcount'] as int?) ?? 0,
      );

  @override
  List<Object?> get props => [department];
}

class ComplianceStats extends Equatable {
  const ComplianceStats({
    required this.mandatoryCourses,
    required this.employeesTotal,
    required this.fullyCompliant,
    required this.partiallyCompliant,
    required this.nonCompliant,
    required this.coveragePct,
  });

  final int mandatoryCourses;
  final int employeesTotal;
  final int fullyCompliant;
  final int partiallyCompliant;
  final int nonCompliant;
  final double coveragePct;

  factory ComplianceStats.fromJson(Map<String, dynamic> j) => ComplianceStats(
        mandatoryCourses: (j['mandatory_courses'] as int?) ?? 0,
        employeesTotal: (j['employees_total'] as int?) ?? 0,
        fullyCompliant: (j['fully_compliant'] as int?) ?? 0,
        partiallyCompliant: (j['partially_compliant'] as int?) ?? 0,
        nonCompliant: (j['non_compliant'] as int?) ?? 0,
        coveragePct: double.tryParse(j['coverage_pct'].toString()) ?? 0,
      );

  @override
  List<Object?> get props => [coveragePct];
}

class AttritionStats extends Equatable {
  const AttritionStats({
    required this.periodMonths,
    required this.startingHeadcount,
    required this.exits,
    required this.attritionPct,
  });

  final int periodMonths;
  final int startingHeadcount;
  final int exits;
  final double attritionPct;

  factory AttritionStats.fromJson(Map<String, dynamic> j) => AttritionStats(
        periodMonths: (j['period_months'] as int?) ?? 12,
        startingHeadcount: (j['starting_headcount'] as int?) ?? 0,
        exits: (j['exits'] as int?) ?? 0,
        attritionPct: double.tryParse(j['attrition_pct'].toString()) ?? 0,
      );

  @override
  List<Object?> get props => [attritionPct];
}

class VerificationStats extends Equatable {
  const VerificationStats({
    required this.total,
    required this.completed,
    required this.inProgress,
    required this.auditPending,
    required this.breachPct,
    required this.avgHours,
  });

  final int total;
  final int completed;
  final int inProgress;
  final int auditPending;
  final double breachPct;
  final double avgHours;

  factory VerificationStats.fromJson(Map<String, dynamic> j) =>
      VerificationStats(
        total: (j['total'] as int?) ?? 0,
        completed: (j['completed'] as int?) ?? 0,
        inProgress: (j['in_progress'] as int?) ?? 0,
        auditPending: (j['audit_pending'] as int?) ?? 0,
        breachPct: double.tryParse(j['breach_pct'].toString()) ?? 0,
        avgHours: double.tryParse(j['avg_hours'].toString()) ?? 0,
      );

  @override
  List<Object?> get props => [total];
}

class TrainingStats extends Equatable {
  const TrainingStats({
    required this.sessionsTotal,
    required this.sessionsCompleted,
    required this.upcomingSessions,
    required this.totalAttendees,
  });

  final int sessionsTotal;
  final int sessionsCompleted;
  final int upcomingSessions;
  final int totalAttendees;

  factory TrainingStats.fromJson(Map<String, dynamic> j) => TrainingStats(
        sessionsTotal: (j['sessions_total'] as int?) ?? 0,
        sessionsCompleted: (j['sessions_completed'] as int?) ?? 0,
        upcomingSessions: (j['upcoming_sessions'] as int?) ?? 0,
        totalAttendees: (j['total_attendees'] as int?) ?? 0,
      );

  @override
  List<Object?> get props => [sessionsTotal];
}

class SalesStatsLite extends Equatable {
  const SalesStatsLite({
    required this.leadsCount,
    required this.leadsWon,
    required this.winRatePct,
    required this.ordersTotal,
  });

  final int leadsCount;
  final int leadsWon;
  final double winRatePct;
  final double ordersTotal;

  factory SalesStatsLite.fromJson(Map<String, dynamic> j) => SalesStatsLite(
        leadsCount: (j['leads_count'] as int?) ?? 0,
        leadsWon: (j['leads_won'] as int?) ?? 0,
        winRatePct: double.tryParse(j['win_rate_pct'].toString()) ?? 0,
        ordersTotal:
            double.tryParse(j['orders_total'].toString()) ?? 0,
      );

  @override
  List<Object?> get props => [leadsCount];
}

class DirectorDashboard extends Equatable {
  const DirectorDashboard({
    required this.headcount,
    required this.attrition,
    required this.departmentBreakdown,
    required this.compliance,
    required this.verification,
    required this.training,
    this.sales,
  });

  final HeadcountTrend headcount;
  final AttritionStats attrition;
  final List<DepartmentBreakdown> departmentBreakdown;
  final ComplianceStats compliance;
  final VerificationStats verification;
  final TrainingStats training;
  final SalesStatsLite? sales;

  factory DirectorDashboard.fromJson(Map<String, dynamic> j) =>
      DirectorDashboard(
        headcount:
            HeadcountTrend.fromJson(j['headcount'] as Map<String, dynamic>),
        attrition:
            AttritionStats.fromJson(j['attrition'] as Map<String, dynamic>),
        departmentBreakdown:
            ((j['department_breakdown'] as List?) ?? const [])
                .map((e) =>
                    DepartmentBreakdown.fromJson(e as Map<String, dynamic>))
                .toList(),
        compliance:
            ComplianceStats.fromJson(j['compliance'] as Map<String, dynamic>),
        verification: VerificationStats.fromJson(
            j['verification'] as Map<String, dynamic>),
        training:
            TrainingStats.fromJson(j['training'] as Map<String, dynamic>),
        sales: j['sales'] != null
            ? SalesStatsLite.fromJson(j['sales'] as Map<String, dynamic>)
            : null,
      );

  @override
  List<Object?> get props => [headcount, attrition];
}
