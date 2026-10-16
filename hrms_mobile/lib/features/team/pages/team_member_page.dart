import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/di/injection.dart';
import '../../../core/routing/app_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../attendance/data/attendance_models.dart';
import '../data/team_api.dart';
import '../widgets/team_widgets.dart';

String _day(String? iso) {
  final d = iso == null ? null : DateTime.tryParse(iso);
  return d == null ? '' : DateFormat('d MMM yyyy').format(d);
}

/// One team member: who they report to, today, target, their team,
/// this month's attendance, recent daily plans and leave.
class TeamMemberPage extends StatefulWidget {
  const TeamMemberPage({super.key, required this.employeeId});
  final int employeeId;

  @override
  State<TeamMemberPage> createState() => _TeamMemberPageState();
}

class _TeamMemberPageState extends State<TeamMemberPage> {
  late Future<TeamMemberDetail> _member = sl<TeamApi>().member(widget.employeeId);
  late Future<List<Map<String, dynamic>>> _plans =
      sl<TeamApi>().dailyPlans(widget.employeeId).catchError((_) => <Map<String, dynamic>>[]);

  Future<void> _refresh() async {
    setState(() {
      _member = sl<TeamApi>().member(widget.employeeId);
      _plans = sl<TeamApi>()
          .dailyPlans(widget.employeeId)
          .catchError((_) => <Map<String, dynamic>>[]);
    });
    await _member;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Team member')),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<TeamMemberDetail>(
          future: _member,
          builder: (context, snap) {
            if (snap.hasError) {
              return ListView(
                padding: const EdgeInsets.all(24),
                children: const [
                  SizedBox(height: 80),
                  Text('Could not load this person.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: AppColors.textMuted)),
                ],
              );
            }
            if (!snap.hasData) return const Center(child: CircularProgressIndicator());
            final m = snap.data!;
            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
              children: [
                _Header(m: m),
                const SizedBox(height: 16),
                _TodayCard(m: m),
                if (m.team != null) ...[
                  const SizedBox(height: 12),
                  _Heading('THEIR TEAM · ${m.directReports} DIRECT'),
                  Card(
                    margin: EdgeInsets.zero,
                    child: ListTile(
                      leading: const Icon(Icons.groups_outlined, color: AppColors.brandGold),
                      title: Text(rollupLine(m.team!),
                          style: TextStyle(color: context.textPrimary, fontSize: 13.5)),
                      trailing: const Icon(Icons.chevron_right),
                      onTap: () => context.push(
                        '${AppRoutes.myTeam}?root=${m.employeeId}&name=${Uri.encodeComponent(m.name)}',
                      ),
                    ),
                  ),
                ],
                const SizedBox(height: 16),
                const _Heading('ATTENDANCE'),
                _MonthCalendar(employeeId: m.employeeId),
                const SizedBox(height: 16),
                const _Heading('RECENT DAILY PLANS'),
                FutureBuilder<List<Map<String, dynamic>>>(
                  future: _plans,
                  builder: (context, ps) {
                    final plans = ps.data ?? const [];
                    if (!ps.hasData) {
                      return const Padding(
                        padding: EdgeInsets.all(12),
                        child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
                      );
                    }
                    if (plans.isEmpty) {
                      return const Text('No daily plans submitted yet.',
                          style: TextStyle(color: AppColors.textMuted));
                    }
                    return Column(children: [for (final p in plans.take(6)) _PlanTile(p: p)]);
                  },
                ),
                const SizedBox(height: 16),
                const _Heading('RECENT LEAVE'),
                if (m.recentLeaves.isEmpty)
                  const Text('No leave taken.', style: TextStyle(color: AppColors.textMuted))
                else
                  for (final l in m.recentLeaves)
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 5),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(
                              '${l['leave_type']} · ${_day(l['from_date'] as String?)}'
                              '${l['to_date'] != l['from_date'] ? ' – ${_day(l['to_date'] as String?)}' : ''}',
                              style: TextStyle(color: context.textPrimary, fontSize: 13),
                            ),
                          ),
                          Text(
                            '${l['status']}',
                            style: TextStyle(
                              fontSize: 12,
                              color: l['status'] == 'approved'
                                  ? AppColors.successText
                                  : l['status'] == 'pending'
                                      ? AppColors.warning
                                      : AppColors.textMuted,
                            ),
                          ),
                        ],
                      ),
                    ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _Heading extends StatelessWidget {
  const _Heading(this.text);
  final String text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 8, left: 2),
        child: Text(
          text,
          style: Theme.of(context)
              .textTheme
              .labelSmall
              ?.copyWith(color: AppColors.brandGoldDark, letterSpacing: 1),
        ),
      );
}

class _Header extends StatelessWidget {
  const _Header({required this.m});
  final TeamMemberDetail m;

  @override
  Widget build(BuildContext context) {
    Future<void> open(String url) async {
      await launchUrl(Uri.parse(url));
    }

    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        PersonAvatar(name: m.name, photoUrl: m.photoUrl, radius: 28),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(m.name,
                  style: TextStyle(
                    color: context.textPrimary,
                    fontSize: 19,
                    fontWeight: FontWeight.w700,
                  )),
              Text(
                [m.designation, m.department, m.code].whereType<String>().join(' · '),
                style: const TextStyle(color: AppColors.textMuted, fontSize: 12.5),
              ),
              if (m.chain.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(
                    'Reports to ${m.chain.join(' → ')}',
                    style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
                  ),
                ),
              if (m.phone != null || m.email != null)
                Wrap(
                  spacing: 4,
                  children: [
                    if (m.phone != null)
                      TextButton.icon(
                        onPressed: () => open('tel:${m.phone}'),
                        icon: const Icon(Icons.call_outlined, size: 16),
                        label: const Text('Call'),
                      ),
                    if (m.email != null)
                      TextButton.icon(
                        onPressed: () => open('mailto:${m.email}'),
                        icon: const Icon(Icons.mail_outline, size: 16),
                        label: const Text('Email'),
                      ),
                  ],
                ),
            ],
          ),
        ),
      ],
    );
  }
}

class _TodayCard extends StatelessWidget {
  const _TodayCard({required this.m});
  final TeamMemberDetail m;

  @override
  Widget build(BuildContext context) {
    final t = m.target;
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text('Today',
                    style: TextStyle(color: context.textPrimary, fontWeight: FontWeight.w600)),
                const Spacer(),
                StatusPill(m.today),
              ],
            ),
            const SizedBox(height: 8),
            PlanMarks(morning: m.dwpMorning, eod: m.dwpEod),
            const SizedBox(height: 12),
            if (t == null)
              const Text('No target set', style: TextStyle(color: AppColors.textMuted, fontSize: 12))
            else
              TargetProgress(
                pct: t.pct,
                caption: '${t.periodType[0].toUpperCase()}${t.periodType.substring(1)} target · '
                    '${rupees(t.achievedAmount)} of ${rupees(t.targetAmount)}',
              ),
          ],
        ),
      ),
    );
  }
}

class _MonthCalendar extends StatefulWidget {
  const _MonthCalendar({required this.employeeId});
  final int employeeId;

  @override
  State<_MonthCalendar> createState() => _MonthCalendarState();
}

class _MonthCalendarState extends State<_MonthCalendar> {
  DateTime _month = DateTime(DateTime.now().year, DateTime.now().month);
  late Future<AttendanceCalendar> _future = _load();

  Future<AttendanceCalendar> _load() =>
      sl<TeamApi>().calendar(widget.employeeId, _month.year, _month.month);

  void _shift(int d) => setState(() {
        _month = DateTime(_month.year, _month.month + d);
        _future = _load();
      });

  static Color _tone(String s) => switch (s) {
        'present' => AppColors.successText.withOpacity(0.55),
        'wfh' => AppColors.infoText.withOpacity(0.5),
        'half_day' => AppColors.brandGold.withOpacity(0.55),
        'leave' => AppColors.infoText.withOpacity(0.25),
        'absent' => AppColors.errorText.withOpacity(0.55),
        'holiday' || 'week_off' => AppColors.textFaint.withOpacity(0.25),
        _ => Colors.transparent,
      };

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(10, 4, 10, 12),
        child: Column(
          children: [
            Row(
              children: [
                IconButton(onPressed: () => _shift(-1), icon: const Icon(Icons.chevron_left)),
                Expanded(
                  child: Text(
                    DateFormat('MMMM yyyy').format(_month),
                    textAlign: TextAlign.center,
                    style: TextStyle(color: context.textPrimary, fontWeight: FontWeight.w600),
                  ),
                ),
                IconButton(onPressed: () => _shift(1), icon: const Icon(Icons.chevron_right)),
              ],
            ),
            FutureBuilder<AttendanceCalendar>(
              future: _future,
              builder: (context, snap) {
                if (snap.hasError) {
                  return const Padding(
                    padding: EdgeInsets.all(12),
                    child: Text('Could not load attendance.',
                        style: TextStyle(color: AppColors.textMuted)),
                  );
                }
                if (!snap.hasData) {
                  return const Padding(
                    padding: EdgeInsets.all(20),
                    child: CircularProgressIndicator(strokeWidth: 2),
                  );
                }
                final c = snap.data!;
                final lead = c.days.isEmpty ? 0 : c.days.first.weekday;
                return Column(
                  children: [
                    GridView.count(
                      crossAxisCount: 7,
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      mainAxisSpacing: 4,
                      crossAxisSpacing: 4,
                      childAspectRatio: 1.25,
                      children: [
                        for (final d in const ['M', 'T', 'W', 'T', 'F', 'S', 'S'])
                          Center(
                            child: Text(d,
                                style: const TextStyle(color: AppColors.textFaint, fontSize: 11)),
                          ),
                        for (var i = 0; i < lead; i++) const SizedBox.shrink(),
                        for (final d in c.days)
                          Container(
                            alignment: Alignment.center,
                            decoration: BoxDecoration(
                              color: _tone(d.status),
                              borderRadius: BorderRadius.circular(6),
                              border: d.isLate
                                  ? Border.all(color: AppColors.warning, width: 1.5)
                                  : null,
                            ),
                            child: Text(
                              '${int.parse(d.date.substring(8))}',
                              style: TextStyle(color: context.textPrimary, fontSize: 12),
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 10),
                    Wrap(
                      spacing: 14,
                      runSpacing: 4,
                      children: [
                        _Stat('Present', c.daysPresent, AppColors.successText),
                        _Stat('WFH', c.daysWfh, AppColors.infoText),
                        _Stat('Leave', c.daysLeave, AppColors.infoText),
                        _Stat('Absent', c.daysAbsent, AppColors.errorText),
                        _Stat('Working days', c.workingDays, AppColors.textMuted),
                      ],
                    ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat(this.label, this.value, this.color);
  final String label;
  final int value;
  final Color color;

  @override
  Widget build(BuildContext context) => Text.rich(
        TextSpan(children: [
          TextSpan(text: '$label ', style: const TextStyle(color: AppColors.textMuted)),
          TextSpan(
            text: '$value',
            style: TextStyle(color: color, fontWeight: FontWeight.w700),
          ),
        ]),
        style: const TextStyle(fontSize: 12),
      );
}

class _PlanTile extends StatelessWidget {
  const _PlanTile({required this.p});
  final Map<String, dynamic> p;

  @override
  Widget build(BuildContext context) {
    final fields = ((p['fields'] as List?) ?? const [])
        .cast<Map<String, dynamic>>()
        .where((f) => (f['value'] as String?)?.isNotEmpty ?? false)
        .take(3);
    final hours = p['total_hours'];
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    '${_day(p['date'] as String?)} · ${p['type'] == 'morning' ? 'Morning plan' : 'End of day'}',
                    style: TextStyle(color: context.textPrimary, fontWeight: FontWeight.w600, fontSize: 13),
                  ),
                ),
                if (hours != null)
                  Text('${double.tryParse('$hours')?.toStringAsFixed(1) ?? hours} h',
                      style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
              ],
            ),
            for (final f in fields)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(
                  '${(f['field_key'] as String).replaceAll('_', ' ')}: ${f['value']}',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
