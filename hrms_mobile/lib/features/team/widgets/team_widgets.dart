import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/theme/app_colors.dart';
import '../data/team_api.dart';

const dayStatusLabels = {
  'present': 'Present',
  'late': 'Late',
  'wfh': 'WFH',
  'half_day': 'Half day',
  'on_leave': 'On leave',
  'absent': 'Absent',
  'not_in': 'Not in yet',
  'off': 'Off',
};

Color dayStatusColor(String s) => switch (s) {
      'present' => AppColors.successText,
      'late' => AppColors.warning,
      'wfh' || 'on_leave' => AppColors.infoText,
      'half_day' => AppColors.brandGold,
      'absent' => AppColors.errorText,
      _ => AppColors.textMuted,
    };

String hhmm(String? iso) {
  final d = iso == null ? null : DateTime.tryParse(iso);
  return d == null ? '' : DateFormat('h:mm a').format(d);
}

/// "₹4.1L of ₹5.0L" or "41 of 60 visits".
String targetCaption(TeamTarget t) => t.isMoney
    ? '${rupees(t.achievedAmount)} of ${rupees(t.targetAmount)}'
    : '${t.achievedAmount.toStringAsFixed(0)} of ${t.targetAmount.toStringAsFixed(0)} '
        '${targetMetricUnits[t.metric] ?? ''}';

String rupees(double v) {
  if (v >= 10000000) return '₹${(v / 10000000).toStringAsFixed(1)}Cr';
  if (v >= 100000) return '₹${(v / 100000).toStringAsFixed(1)}L';
  if (v >= 1000) return '₹${(v / 1000).toStringAsFixed(0)}k';
  return '₹${v.toStringAsFixed(0)}';
}

class PersonAvatar extends StatelessWidget {
  const PersonAvatar({super.key, required this.name, this.photoUrl, this.radius = 20});
  final String name;
  final String? photoUrl;
  final double radius;

  @override
  Widget build(BuildContext context) {
    final initials = name
        .split(RegExp(r'\s+'))
        .where((w) => w.isNotEmpty)
        .take(2)
        .map((w) => w[0].toUpperCase())
        .join();
    return CircleAvatar(
      radius: radius,
      backgroundColor: AppColors.brandGold.withOpacity(0.18),
      foregroundImage: photoUrl != null ? NetworkImage(photoUrl!) : null,
      child: Text(
        initials,
        style: TextStyle(
          color: AppColors.brandGold,
          fontWeight: FontWeight.w700,
          fontSize: radius * 0.7,
        ),
      ),
    );
  }
}

class StatusPill extends StatelessWidget {
  const StatusPill(this.today, {super.key});
  final TeamToday today;

  @override
  Widget build(BuildContext context) {
    final c = dayStatusColor(today.status);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 3),
          decoration: BoxDecoration(
            color: c.withOpacity(0.16),
            borderRadius: BorderRadius.circular(20),
          ),
          child: Text(
            dayStatusLabels[today.status] ?? today.status,
            style: TextStyle(color: c, fontSize: 12, fontWeight: FontWeight.w600),
          ),
        ),
        if (today.checkIn != null)
          Padding(
            padding: const EdgeInsets.only(top: 3),
            child: Text(
              'in ${hhmm(today.checkIn)}',
              style: const TextStyle(color: AppColors.textFaint, fontSize: 11),
            ),
          ),
      ],
    );
  }
}

class TargetProgress extends StatelessWidget {
  const TargetProgress({super.key, required this.pct, this.caption});
  final double? pct;
  final String? caption;

  @override
  Widget build(BuildContext context) {
    final p = ((pct ?? 0) / 100).clamp(0.0, 1.0);
    final c = (pct ?? 0) >= 100
        ? AppColors.successText
        : (pct ?? 0) >= 60
            ? AppColors.brandGold
            : AppColors.warning;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: p,
                  minHeight: 6,
                  color: c,
                  backgroundColor: AppColors.textFaint.withOpacity(0.25),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Text(
              pct == null ? '—' : '${pct!.toStringAsFixed(0)}%',
              style: TextStyle(color: c, fontWeight: FontWeight.w700, fontSize: 12),
            ),
          ],
        ),
        if (caption != null)
          Padding(
            padding: const EdgeInsets.only(top: 2),
            child: Text(caption!, style: const TextStyle(color: AppColors.textMuted, fontSize: 11)),
          ),
      ],
    );
  }
}

/// "12 people · 91% present · 78% of target".
String rollupLine(TeamRollup t) => [
      '${t.size} ${t.size == 1 ? 'person' : 'people'}',
      if (t.attendancePct != null) '${t.attendancePct!.toStringAsFixed(0)}% present',
      if (t.targetPct != null) '${t.targetPct!.toStringAsFixed(0)}% of target',
      if (t.tasksOverdue > 0) '${t.tasksOverdue} overdue tasks',
      if (t.absent > 0) '${t.absent} absent',
      if (t.late > 0) '${t.late} late',
    ].join(' · ');

class PlanMarks extends StatelessWidget {
  const PlanMarks({super.key, required this.morning, required this.eod});
  final bool morning;
  final bool eod;

  @override
  Widget build(BuildContext context) {
    Widget mark(bool done, String label) => Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              done ? Icons.check_circle : Icons.radio_button_unchecked,
              size: 14,
              color: done ? AppColors.successText : AppColors.textFaint,
            ),
            const SizedBox(width: 4),
            Text(label,
                style: TextStyle(
                  fontSize: 12,
                  color: done ? AppColors.successText : AppColors.textMuted,
                )),
          ],
        );
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [mark(morning, 'Plan'), const SizedBox(width: 12), mark(eod, 'EOD')],
    );
  }
}
