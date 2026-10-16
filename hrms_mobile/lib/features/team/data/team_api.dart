import 'package:dio/dio.dart';

import '../../attendance/data/attendance_models.dart';

double? _d(Object? v) => v == null ? null : double.tryParse(v.toString());
int _i(Object? v) => v is int ? v : int.tryParse('${v ?? 0}') ?? 0;

/// Whether the signed-in person has a team (and how big it is).
class TeamInfo {
  const TeamInfo({
    required this.hasTeam,
    required this.seesEveryone,
    required this.directCount,
    required this.teamSize,
  });
  final bool hasTeam;
  final bool seesEveryone;
  final int directCount;
  final int? teamSize;

  factory TeamInfo.fromJson(Map<String, dynamic> j) => TeamInfo(
        hasTeam: j['has_team'] as bool? ?? false,
        seesEveryone: j['sees_everyone'] as bool? ?? false,
        directCount: _i(j['direct_count']),
        teamSize: j['team_size'] as int?,
      );
}

class TeamToday {
  const TeamToday({required this.status, this.checkIn, this.checkOut});
  final String status;
  final String? checkIn;
  final String? checkOut;

  factory TeamToday.fromJson(Map<String, dynamic> j) => TeamToday(
        status: j['status'] as String? ?? 'not_in',
        checkIn: j['check_in'] as String?,
        checkOut: j['check_out'] as String?,
      );
}

const targetMetricUnits = {
  'leads_won': 'leads won',
  'new_leads': 'new leads',
  'field_visits': 'visits',
  'verifications': 'verifications',
  'tasks_done': 'tasks done',
};

class TeamTarget {
  const TeamTarget({
    this.metric = 'sales_amount',
    required this.periodType,
    required this.targetAmount,
    required this.achievedAmount,
    required this.pct,
  });
  final String metric;
  final String periodType;
  final double targetAmount;
  final double achievedAmount;
  final double? pct;

  bool get isMoney => metric == 'sales_amount';

  factory TeamTarget.fromJson(Map<String, dynamic> j) => TeamTarget(
        metric: j['metric'] as String? ?? 'sales_amount',
        periodType: j['period_type'] as String? ?? 'monthly',
        targetAmount: _d(j['target_amount']) ?? 0,
        achievedAmount: _d(j['achieved_amount']) ?? 0,
        pct: _d(j['achievement_pct']),
      );
}

/// Figures rolled up for a group of people.
class TeamRollup {
  const TeamRollup(this.j);
  final Map<String, dynamic> j;

  int get size => _i(j['size']);
  int get presentTotal => _i(j['present_total']);
  int get late => _i(j['late']);
  int get wfh => _i(j['wfh']);
  int get onLeave => _i(j['on_leave']);
  int get absent => _i(j['absent']);
  int get notIn => _i(j['not_in']);
  int get off => _i(j['off']);
  int get dwpMorning => _i(j['dwp_morning']);
  int get dwpEod => _i(j['dwp_eod']);
  int get withTarget => _i(j['with_target']);
  double? get attendancePct => _d(j['attendance_pct']);
  double? get targetPct => _d(j['target_pct']);
  double get targetAmount => _d(j['target_amount']) ?? 0;
  double get achievedAmount => _d(j['achieved_amount']) ?? 0;
  int get tasksOpen => _i(j['tasks_open']);
  int get tasksOverdue => _i(j['tasks_overdue']);
  int get tasksDone7d => _i(j['tasks_done_7d']);
}

class TeamMemberRow {
  const TeamMemberRow({
    required this.employeeId,
    required this.code,
    required this.name,
    required this.designation,
    required this.department,
    required this.photoUrl,
    required this.managerName,
    required this.level,
    required this.directReports,
    required this.today,
    required this.dwpMorning,
    required this.dwpEod,
    required this.target,
    required this.team,
    this.tasksOpen = 0,
    this.tasksOverdue = 0,
  });

  final int employeeId;
  final String code;
  final String name;
  final String? designation;
  final String? department;
  final String? photoUrl;
  final String? managerName;
  final int level;
  final int directReports;
  final TeamToday today;
  final bool dwpMorning;
  final bool dwpEod;
  final TeamTarget? target;
  final TeamRollup? team;
  final int tasksOpen;
  final int tasksOverdue;

  factory TeamMemberRow.fromJson(Map<String, dynamic> j) => TeamMemberRow(
        employeeId: j['employee_id'] as int,
        code: j['employee_code'] as String? ?? '',
        name: j['name'] as String? ?? '',
        designation: j['designation'] as String?,
        department: j['department'] as String?,
        photoUrl: j['photo_url'] as String?,
        managerName: j['manager_name'] as String?,
        level: _i(j['level']),
        directReports: _i(j['direct_reports']),
        today: TeamToday.fromJson(j['today'] as Map<String, dynamic>),
        dwpMorning: j['dwp_morning'] as bool? ?? false,
        dwpEod: j['dwp_eod'] as bool? ?? false,
        target: j['target'] == null
            ? null
            : TeamTarget.fromJson(j['target'] as Map<String, dynamic>),
        team: j['team'] == null ? null : TeamRollup(j['team'] as Map<String, dynamic>),
        tasksOpen: _i((j['tasks'] as Map?)?['open']),
        tasksOverdue: _i((j['tasks'] as Map?)?['overdue']),
      );

  /// Absent, late, not in yet, overdue tasks, or no morning plan on a
  /// working day.
  bool get needsAttention =>
      const {'absent', 'late', 'not_in'}.contains(today.status) ||
      tasksOverdue > 0 ||
      (!dwpMorning && !const {'on_leave', 'off'}.contains(today.status));
}

class TeamOverview {
  const TeamOverview({
    required this.rootName,
    required this.isRootMe,
    required this.summary,
    required this.directCount,
    required this.members,
  });
  final String? rootName;
  final bool isRootMe;
  final TeamRollup summary;
  final int directCount;
  final List<TeamMemberRow> members;
}

class TeamMemberDetail {
  const TeamMemberDetail(this.j);
  final Map<String, dynamic> j;

  int get employeeId => j['employee_id'] as int;
  String get name => j['name'] as String? ?? '';
  String get code => j['employee_code'] as String? ?? '';
  String? get designation => j['designation'] as String?;
  String? get department => j['department'] as String?;
  String? get photoUrl => j['photo_url'] as String?;
  String? get phone => j['phone'] as String?;
  String? get email => j['email'] as String?;
  List<String> get chain => ((j['chain'] as List?) ?? const [])
      .map((c) => (c as Map<String, dynamic>)['name'] as String)
      .toList();
  TeamToday get today => TeamToday.fromJson(j['today'] as Map<String, dynamic>);
  bool get dwpMorning => j['dwp_morning'] as bool? ?? false;
  bool get dwpEod => j['dwp_eod'] as bool? ?? false;
  TeamTarget? get target => j['target'] == null
      ? null
      : TeamTarget.fromJson(j['target'] as Map<String, dynamic>);
  int get directReports => _i(j['direct_reports']);
  int get tasksOpen => _i((j['tasks'] as Map?)?['open']);
  int get tasksOverdue => _i((j['tasks'] as Map?)?['overdue']);
  int get tasksDone7d => _i((j['tasks'] as Map?)?['done_7d']);
  TeamRollup? get team =>
      j['team'] == null ? null : TeamRollup(j['team'] as Map<String, dynamic>);
  List<Map<String, dynamic>> get recentLeaves =>
      ((j['recent_leaves'] as List?) ?? const []).cast<Map<String, dynamic>>();
}

class TeamApi {
  TeamApi(this._dio);
  final Dio _dio;
  static const _v1 = '/api/v1';

  Future<TeamInfo> me() async {
    final res = await _dio.get<Map<String, dynamic>>('$_v1/team/me');
    return TeamInfo.fromJson(res.data ?? const {});
  }

  Future<TeamOverview> overview({required bool everyone, int? rootId}) async {
    final res = await _dio.get<Map<String, dynamic>>(
      '$_v1/team/overview',
      queryParameters: {
        'scope': everyone ? 'all' : 'direct',
        if (rootId != null) 'root_id': rootId,
      },
    );
    final j = res.data!;
    final root = j['root'] as Map<String, dynamic>?;
    return TeamOverview(
      rootName: root?['name'] as String?,
      isRootMe: rootId == null,
      summary: TeamRollup(j['summary'] as Map<String, dynamic>),
      directCount: _i(j['direct_count']),
      members: ((j['members'] as List?) ?? const [])
          .map((m) => TeamMemberRow.fromJson(m as Map<String, dynamic>))
          .toList(),
    );
  }

  Future<TeamMemberDetail> member(int id) async {
    final res = await _dio.get<Map<String, dynamic>>('$_v1/team/members/$id');
    return TeamMemberDetail(res.data!);
  }

  Future<AttendanceCalendar> calendar(int id, int year, int month) async {
    final res = await _dio.get<Map<String, dynamic>>(
      '$_v1/attendance/employee/$id/calendar',
      queryParameters: {'year': year, 'month': month},
    );
    return AttendanceCalendar.fromJson(res.data!);
  }

  /// Recent daily plans (raw: date, type, total_hours, fields …).
  Future<List<Map<String, dynamic>>> dailyPlans(int id) async {
    final res = await _dio.get<List<dynamic>>(
      '$_v1/dwp/employee/$id/history',
      queryParameters: {'limit': 10},
    );
    return (res.data ?? const []).cast<Map<String, dynamic>>();
  }
}
