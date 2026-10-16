import 'package:dio/dio.dart';

double _d(Object? v) => double.tryParse('${v ?? 0}') ?? 0;

/// What I can earn this period from one scheme.
class IncentiveProjection {
  const IncentiveProjection(this.j);
  final Map<String, dynamic> j;

  String get schemeName => j['scheme_name'] as String? ?? 'Incentive';
  String? get description => j['description'] as String?;
  String get metric => j['metric'] as String? ?? 'sales_amount';
  String get unit => j['unit'] as String? ?? '';
  bool get isMoney => metric == 'sales_amount';
  String get periodStart => j['period_start'] as String? ?? '';
  String get periodEnd => j['period_end'] as String? ?? '';
  double get target => _d(j['target_amount']);
  double get achieved => _d(j['achieved_amount']);
  double get pct => _d(j['achievement_pct']);
  double get earningNow => _d(j['earning_now']);
  List<Map<String, dynamic>> get slabs =>
      ((j['slabs'] as List?) ?? const []).cast<Map<String, dynamic>>();
  Map<String, dynamic>? get nextSlab => j['next_slab'] as Map<String, dynamic>?;
  List<String> get warnings => ((j['warnings'] as List?) ?? const []).cast<String>();
}

/// One person's incentive for one run (history or review).
class IncentiveLine {
  const IncentiveLine(this.j);
  final Map<String, dynamic> j;

  int get id => j['id'] as int;
  String get schemeName => j['scheme_name'] as String? ?? '';
  String get periodLabel => j['period_label'] as String? ?? '';
  String get runStatus => j['run_status'] as String? ?? 'review';
  String get employeeName => j['employee_name'] as String? ?? '';
  String? get designation => j['designation'] as String?;
  String get metric => j['metric'] as String? ?? 'sales_amount';
  double get target => _d(j['target_amount']);
  double get achieved => _d(j['achieved_amount']);
  double get pct => _d(j['achievement_pct']);
  double? get attendance => j['attendance_pct'] == null ? null : _d(j['attendance_pct']);
  bool get eligible => j['eligible'] as bool? ?? false;
  List<String> get reasons => ((j['reasons'] as List?) ?? const []).cast<String>();
  double get calculated => _d(j['calculated_amount']);
  double? get amount => j['amount'] == null ? null : _d(j['amount']);
  String get reviewStatus => j['review_status'] as String? ?? 'pending';
  String? get reviewNote => j['review_note'] as String?;
  bool get paid => j['paid'] as bool? ?? false;
  bool get inPayroll => j['in_payroll'] as bool? ?? false;
  String? get payoutLabel => j['payout_label'] as String?;
}

class IncentivesApi {
  IncentivesApi(this._dio);
  final Dio _dio;
  static const _v1 = '/api/v1/incentives';

  Future<({List<IncentiveProjection> current, List<IncentiveLine> history})> mine() async {
    final res = await _dio.get<Map<String, dynamic>>('$_v1/me');
    final j = res.data ?? const {};
    return (
      current: ((j['current'] as List?) ?? const [])
          .map((e) => IncentiveProjection(e as Map<String, dynamic>))
          .toList(),
      history: ((j['history'] as List?) ?? const [])
          .map((e) => IncentiveLine(e as Map<String, dynamic>))
          .toList(),
    );
  }

  Future<List<IncentiveLine>> reviewQueue() async {
    final res = await _dio.get<List<dynamic>>('$_v1/review');
    return (res.data ?? const []).map((e) => IncentiveLine(e as Map<String, dynamic>)).toList();
  }

  Future<int> pendingReviews() async {
    final res = await _dio.get<Map<String, dynamic>>('$_v1/review/count');
    return (res.data?['pending'] as int?) ?? 0;
  }

  Future<IncentiveLine> review(int lineId, String action, {double? amount, String? note}) async {
    final res = await _dio.post<Map<String, dynamic>>('$_v1/lines/$lineId/review', data: {
      'action': action,
      if (amount != null) 'amount': amount,
      if (note != null && note.isNotEmpty) 'note': note,
    });
    return IncentiveLine(res.data!);
  }
}
