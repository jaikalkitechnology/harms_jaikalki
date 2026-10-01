import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/attendance_api.dart';
import '../data/attendance_models.dart';

/// Read-only calendar of past attendance.
///
/// Sundays + holidays render in red so the employee knows those days
/// were never expected to be punched. Tapping any day brings up a
/// bottom-sheet with the recorded check-in/out and notes.
class AttendanceCalendarPage extends StatefulWidget {
  const AttendanceCalendarPage({super.key});

  @override
  State<AttendanceCalendarPage> createState() => _AttendanceCalendarPageState();
}

class _AttendanceCalendarPageState extends State<AttendanceCalendarPage> {
  late int _year;
  late int _month;
  final AttendanceApi _api = sl<AttendanceApi>();
  Future<AttendanceCalendar>? _future;

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();
    _year = now.year;
    _month = now.month;
    _future = _api.myCalendar(year: _year, month: _month);
  }

  void _shift(int delta) {
    var ny = _year;
    var nm = _month + delta;
    if (nm < 1) {
      nm = 12;
      ny -= 1;
    } else if (nm > 12) {
      nm = 1;
      ny += 1;
    }
    setState(() {
      _year = ny;
      _month = nm;
      _future = _api.myCalendar(year: _year, month: _month);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Attendance calendar')),
      body: FutureBuilder<AttendanceCalendar>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(
                  'Could not load calendar.\n${snapshot.error}',
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: AppColors.textMuted),
                ),
              ),
            );
          }
          final cal = snapshot.data!;
          return RefreshIndicator(
            onRefresh: () async => setState(() {
              _future = _api.myCalendar(year: _year, month: _month);
            }),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _MonthHeader(
                  year: _year,
                  month: _month,
                  onPrev: () => _shift(-1),
                  onNext: () => _shift(1),
                ),
                const SizedBox(height: 16),
                _LegendRow(),
                const SizedBox(height: 12),
                _SummaryStrip(cal: cal),
                const SizedBox(height: 16),
                _CalendarGrid(
                  cal: cal,
                  api: _api,
                  onChanged: () => setState(() {
                    _future =
                        _api.myCalendar(year: _year, month: _month);
                  }),
                ),
                const SizedBox(height: 24),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _MonthHeader extends StatelessWidget {
  const _MonthHeader({
    required this.year,
    required this.month,
    required this.onPrev,
    required this.onNext,
  });
  final int year;
  final int month;
  final VoidCallback onPrev;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    final label = DateFormat('MMMM yyyy').format(DateTime(year, month, 1));
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        IconButton.filledTonal(
          onPressed: onPrev,
          icon: const Icon(Icons.chevron_left),
        ),
        Text(label, style: Theme.of(context).textTheme.titleLarge),
        IconButton.filledTonal(
          onPressed: onNext,
          icon: const Icon(Icons.chevron_right),
        ),
      ],
    );
  }
}

class _LegendRow extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 6,
      children: const [
        _LegendDot(color: AppColors.successText, label: 'Present'),
        _LegendDot(color: AppColors.infoText, label: 'WFH'),
        _LegendDot(color: AppColors.warning, label: 'Half day'),
        _LegendDot(color: AppColors.brandGold, label: 'Leave'),
        _LegendDot(color: AppColors.errorText, label: 'Absent / Holiday / Sun'),
      ],
    );
  }
}

class _LegendDot extends StatelessWidget {
  const _LegendDot({required this.color, required this.label});
  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.14),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: color,
              borderRadius: BorderRadius.circular(999),
            ),
          ),
          const SizedBox(width: 6),
          Text(
            label,
            style: TextStyle(fontSize: 11, color: color),
          ),
        ],
      ),
    );
  }
}

class _SummaryStrip extends StatelessWidget {
  const _SummaryStrip({required this.cal});
  final AttendanceCalendar cal;

  @override
  Widget build(BuildContext context) {
    final items = [
      ('Working', cal.workingDays.toString(), null),
      ('Present', cal.daysPresent.toString(), AppColors.successText),
      ('WFH', cal.daysWfh.toString(), AppColors.infoText),
      ('Half-day', cal.daysHalfDay.toString(), AppColors.warning),
      (
        'Leave',
        cal.daysLeavePending > 0
            ? '${cal.daysLeave} (${cal.daysLeavePending}?)'
            : cal.daysLeave.toString(),
        AppColors.brandGold,
      ),
      ('Absent', cal.daysAbsent.toString(), AppColors.errorText),
      ('Holiday', cal.daysHoliday.toString(), AppColors.errorText),
      ('Sundays', cal.daysWeekoff.toString(), AppColors.errorText),
    ];
    return SizedBox(
      height: 64,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: items.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, i) {
          final (label, value, color) = items[i];
          return Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: AppColors.brandBrownLight),
              color: AppColors.brandBrownDark,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  label.toUpperCase(),
                  style: const TextStyle(
                    fontSize: 9,
                    color: AppColors.textMuted,
                    letterSpacing: 1.2,
                    fontFamily: 'monospace',
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w700,
                    color: color ?? AppColors.warmWhite,
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _CalendarGrid extends StatelessWidget {
  const _CalendarGrid({
    required this.cal,
    required this.api,
    required this.onChanged,
  });
  final AttendanceCalendar cal;
  final AttendanceApi api;
  final VoidCallback onChanged;

  @override
  Widget build(BuildContext context) {
    final first = DateTime(cal.year, cal.month, 1);
    final firstWd = (first.weekday + 6) % 7; // 0 Mon — 6 Sun
    final cells = <_CellModel>[];
    for (int i = 0; i < firstWd; i++) cells.add(_CellModel.blank());
    for (final d in cal.days) cells.add(_CellModel.day(d));
    while (cells.length % 7 != 0) cells.add(_CellModel.blank());

    return Column(
      children: [
        Row(
          children: const [
            _Wd('Mon'), _Wd('Tue'), _Wd('Wed'),
            _Wd('Thu'), _Wd('Fri'), _Wd('Sat'), _Wd('Sun'),
          ],
        ),
        const SizedBox(height: 6),
        GridView.builder(
          physics: const NeverScrollableScrollPhysics(),
          shrinkWrap: true,
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 7,
            mainAxisSpacing: 4,
            crossAxisSpacing: 4,
            // Slightly taller than wide so the day number + status
            // token always fit on the narrowest phones.
            childAspectRatio: 0.78,
          ),
          itemCount: cells.length,
          itemBuilder: (context, i) {
            final c = cells[i];
            if (c.day == null) return const SizedBox.shrink();
            return _DayTile(
              day: c.day!,
              api: api,
              onChanged: onChanged,
            );
          },
        ),
      ],
    );
  }
}

class _Wd extends StatelessWidget {
  const _Wd(this.label);
  final String label;
  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Center(
        child: Text(
          label.toUpperCase(),
          style: TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.w600,
            color: label == 'Sun' ? AppColors.errorText : AppColors.textMuted,
            letterSpacing: 1.5,
            fontFamily: 'monospace',
          ),
        ),
      ),
    );
  }
}

class _CellModel {
  final CalendarDay? day;
  _CellModel.blank() : day = null;
  _CellModel.day(this.day);
}

class _DayTile extends StatelessWidget {
  const _DayTile({
    required this.day,
    required this.api,
    required this.onChanged,
  });
  final CalendarDay day;
  final AttendanceApi api;
  final VoidCallback onChanged;

  bool get _isUpcoming => day.status == 'upcoming';
  bool get _isNotInService => day.status == 'not_in_service';

  bool get _isToday {
    final now = DateTime.now();
    final iso = '${now.year.toString().padLeft(4, '0')}-'
        '${now.month.toString().padLeft(2, '0')}-'
        '${now.day.toString().padLeft(2, '0')}';
    return day.date.startsWith(iso);
  }

  /// Status colour on the dark theme, or null for "no status".
  Color? _tone() {
    if (_isNotInService) return null;
    // Holidays and Sundays stay red even before they arrive.
    if (day.isHoliday || day.isSunday) return AppColors.errorText;
    if (_isUpcoming) return null;
    switch (day.status) {
      case 'present':
        return AppColors.successText;
      case 'wfh':
        return AppColors.infoText;
      case 'half_day':
        return AppColors.warning;
      case 'leave':
        return AppColors.brandGold;
      case 'absent':
        return AppColors.errorText;
      default:
        return null;
    }
  }

  Color _bg() {
    if (_isNotInService) return Colors.white.withOpacity(0.02);
    if (_isUpcoming && _tone() == null) return Colors.white.withOpacity(0.04);
    return (_tone() ?? Colors.white).withOpacity(_tone() == null ? 0.06 : 0.16);
  }

  Color _border() {
    if (_isToday) return AppColors.brandGold;
    if (_isNotInService) return Colors.white.withOpacity(0.05);
    if (_isUpcoming && _tone() == null) return Colors.white.withOpacity(0.10);
    return (_tone() ?? Colors.white).withOpacity(0.35);
  }

  Color _numColor() {
    if (_isNotInService) return AppColors.textFaint.withOpacity(0.5);
    if (day.isHoliday || day.isSunday) return AppColors.errorText;
    if (_isUpcoming) return AppColors.textFaint;
    return AppColors.warmWhite;
  }

  Color _badgeColor() => _tone() ?? AppColors.textMuted;

  String _badge() {
    if (_isNotInService) return '—';
    if (day.isHoliday) return 'HOL';
    if (day.isSunday) return 'SUN';
    if (_isUpcoming) return '';
    switch (day.status) {
      case 'present':
        return 'P';
      case 'wfh':
        return 'WFH';
      case 'half_day':
        return '½';
      case 'leave':
        return day.leaveStatus == 'pending' ? 'L?' : 'L';
      case 'absent':
        return 'A';
      default:
        return '';
    }
  }

  @override
  Widget build(BuildContext context) {
    final dayNum = int.parse(day.date.substring(8, 10));
    return InkWell(
      onTap: () => _showDetail(context),
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 3, vertical: 3),
        decoration: BoxDecoration(
          color: _bg(),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: _border(), width: _isToday ? 1.5 : 1),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Flexible(
                  child: FittedBox(
                    fit: BoxFit.scaleDown,
                    alignment: Alignment.centerLeft,
                    child: Text(
                      '$dayNum',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: _numColor(),
                      ),
                    ),
                  ),
                ),
                if (day.isLate)
                  Container(
                    width: 6,
                    height: 6,
                    decoration: const BoxDecoration(
                      color: AppColors.warning,
                      shape: BoxShape.circle,
                    ),
                  ),
              ],
            ),
            SizedBox(
              width: double.infinity,
              child: FittedBox(
                fit: BoxFit.scaleDown,
                alignment: Alignment.centerLeft,
                child: Text(
                  _badge(),
                  maxLines: 1,
                  style: TextStyle(
                    fontSize: 9.5,
                    fontWeight: FontWeight.w700,
                    color: _badgeColor(),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _showDetail(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (sheetCtx) {
        Future<void> mark(String status) async {
          try {
            await api.selfMark(date: day.date, status: status);
            if (sheetCtx.mounted) Navigator.of(sheetCtx).pop();
            onChanged();
            if (context.mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Attendance marked')),
              );
            }
          } catch (e) {
            final msg = RegExp(r'detail"?\s*:\s*"([^"]+)"')
                    .firstMatch(e.toString())
                    ?.group(1) ??
                'Could not mark — outside your allowed window?';
            if (sheetCtx.mounted) {
              ScaffoldMessenger.of(sheetCtx).showSnackBar(
                SnackBar(content: Text(msg)),
              );
            }
          }
        }

        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(20, 4, 20, 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  DateFormat('EEEE, d MMMM yyyy')
                      .format(DateTime.parse(day.date)),
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 6),
                if (day.isHoliday)
                  Text(
                    'Holiday — ${day.holidayName ?? ''}',
                    style: const TextStyle(color: AppColors.errorText),
                  )
                else if (day.isSunday)
                  const Text(
                    'Sunday — week off',
                    style: TextStyle(color: AppColors.errorText),
                  )
                else if (_isUpcoming)
                  const Text(
                    'Upcoming day — nothing to show yet.',
                    style: TextStyle(color: AppColors.textMuted),
                  )
                else ...[
                  _kv('Status', day.status.toUpperCase()),
                  if (day.workMode != null) _kv('Mode', day.workMode!),
                  if (day.checkIn != null)
                    _kv(
                      'Check-in',
                      DateFormat('hh:mm a')
                          .format(DateTime.parse(day.checkIn!).toLocal()),
                    ),
                  if (day.checkOut != null)
                    _kv(
                      'Check-out',
                      DateFormat('hh:mm a')
                          .format(DateTime.parse(day.checkOut!).toLocal()),
                    ),
                  if (day.totalMinutes > 0)
                    _kv(
                      'Hours',
                      '${(day.totalMinutes / 60).floor()}h ${day.totalMinutes % 60}m',
                    ),
                  if (day.leaveType != null) _kv('Leave', day.leaveType!),
                  if (day.isLate)
                    _kv(
                      'Late',
                      day.lateRemark?.isNotEmpty == true
                          ? day.lateRemark!
                          : 'Marked late',
                    ),
                  if (day.notes != null && day.notes!.isNotEmpty)
                    _kv('Notes', day.notes!),
                ],
                if (day.isEditable &&
                    !_isUpcoming &&
                    !day.isHoliday &&
                    !day.isSunday) ...[
                  const SizedBox(height: 16),
                  Text(
                    'Mark attendance',
                    style: Theme.of(sheetCtx).textTheme.labelLarge,
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: FilledButton(
                          onPressed: () => mark('present'),
                          child: const Text('Present'),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () => mark('wfh'),
                          child: const Text('WFH'),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  const Text(
                    'Today is always allowed. Past days only if your '
                    'admin opened a back-date window.',
                    style: TextStyle(
                      fontSize: 11,
                      color: AppColors.textMuted,
                    ),
                  ),
                ],
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _kv(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppColors.textMuted)),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.right,
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}
