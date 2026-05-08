import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../../employees/cubit/employees_cubit.dart' show LoadStatus;
import '../cubit/attendance_cubit.dart';
import '../data/attendance_api.dart';
import '../data/attendance_models.dart';

class AttendanceHomePage extends StatelessWidget {
  const AttendanceHomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => AttendanceCubit(sl<AttendanceApi>())..load(),
      child: const _AttendanceView(),
    );
  }
}

class _AttendanceView extends StatelessWidget {
  const _AttendanceView();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Attendance')),
      body: BlocConsumer<AttendanceCubit, AttendanceState>(
        listener: (context, state) {
          if (state.error != null && !state.busy) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.error!)),
            );
          }
        },
        builder: (context, state) {
          if (state.status == LoadStatus.loading && state.history.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }
          return RefreshIndicator(
            onRefresh: () => context.read<AttendanceCubit>().load(),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _TodayCard(today: state.today, busy: state.busy),
                const SizedBox(height: 20),
                Text('★ HISTORY',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: AppColors.brandGoldDark,
                    )),
                const SizedBox(height: 8),
                if (state.history.isEmpty)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 16),
                    child: Text('No attendance records yet'),
                  )
                else
                  ...state.history
                      .take(30)
                      .map((r) => _HistoryRow(record: r)),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _TodayCard extends StatelessWidget {
  const _TodayCard({required this.today, required this.busy});
  final AttendanceRecord? today;
  final bool busy;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final cubit = context.read<AttendanceCubit>();
    final hasCheckIn = today?.checkIn != null;
    final hasCheckOut = today?.checkOut != null;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('★ TODAY',
                style: theme.textTheme.labelSmall?.copyWith(
                  color: AppColors.brandGoldDark,
                )),
            const SizedBox(height: 4),
            Text(
              DateFormat('EEEE, d MMMM').format(DateTime.now()),
              style: theme.textTheme.headlineSmall,
            ),
            const SizedBox(height: 16),
            if (today != null) ...[
              _Stat(
                label: 'Check-in',
                value: today!.checkIn != null
                    ? DateFormat('hh:mm a')
                        .format(DateTime.parse(today!.checkIn!).toLocal())
                    : '—',
              ),
              if (today!.checkInDistanceM != null)
                _Stat(
                  label: 'Distance from office',
                  value: '${today!.checkInDistanceM}m',
                ),
              _Stat(
                label: 'Check-out',
                value: today!.checkOut != null
                    ? DateFormat('hh:mm a')
                        .format(DateTime.parse(today!.checkOut!).toLocal())
                    : '—',
              ),
              _Stat(
                label: 'Hours',
                value:
                    '${(today!.totalMinutes / 60).floor()}h ${today!.totalMinutes % 60}m',
              ),
              const SizedBox(height: 8),
              _StatusChip(status: today!.status),
              const SizedBox(height: 16),
            ],
            if (!hasCheckIn) ...[
              FilledButton.icon(
                onPressed: busy ? null : () => cubit.checkIn(workMode: 'office'),
                icon: const Icon(Icons.check_circle_outline),
                label: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 6),
                  child: busy
                      ? const SizedBox(
                          height: 18,
                          width: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Text('Check in (Office)'),
                ),
              ),
              const SizedBox(height: 8),
              OutlinedButton.icon(
                onPressed: busy ? null : () => cubit.checkIn(workMode: 'wfh'),
                icon: const Icon(Icons.house_outlined),
                label: const Text('Check in (WFH · selfie required)'),
              ),
            ] else if (!hasCheckOut)
              FilledButton.icon(
                onPressed: busy ? null : () => cubit.checkOut(),
                icon: const Icon(Icons.logout),
                label: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 6),
                  child: busy
                      ? const SizedBox(
                          height: 18,
                          width: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Text('Check out'),
                ),
              )
            else
              Row(
                children: [
                  const Icon(Icons.check_circle, color: AppColors.success, size: 18),
                  const SizedBox(width: 8),
                  Text('All marked for today',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: AppColors.success,
                      )),
                ],
              ),
          ],
        ),
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label,
              style: const TextStyle(color: AppColors.brandBrownLight)),
          Text(value,
              style: const TextStyle(
                color: context.textPrimary,
                fontWeight: FontWeight.w600,
              )),
        ],
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.status});
  final String status;

  Color _color() {
    switch (status) {
      case 'present':
        return AppColors.success;
      case 'wfh':
        return AppColors.info;
      case 'half_day':
        return AppColors.warning;
      case 'absent':
        return AppColors.error;
      default:
        return AppColors.brandBrownLight;
    }
  }

  @override
  Widget build(BuildContext context) {
    final c = _color();
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: c.withOpacity(0.15),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        status.toUpperCase(),
        style: TextStyle(
          fontSize: 10,
          fontFamily: 'monospace',
          letterSpacing: 1.5,
          fontWeight: FontWeight.w700,
          color: c,
        ),
      ),
    );
  }
}

class _HistoryRow extends StatelessWidget {
  const _HistoryRow({required this.record});
  final AttendanceRecord record;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        title: Text(DateFormat('d MMM yyyy · EEEE')
            .format(DateTime.parse(record.date))),
        subtitle: Text(
          [
            if (record.checkIn != null)
              DateFormat('hh:mm a').format(DateTime.parse(record.checkIn!).toLocal()),
            if (record.checkOut != null)
              '→ ${DateFormat('hh:mm a').format(DateTime.parse(record.checkOut!).toLocal())}',
            '${(record.totalMinutes / 60).floor()}h ${record.totalMinutes % 60}m',
          ].where((s) => s.isNotEmpty).join(' · '),
        ),
        trailing: _StatusChip(status: record.status),
      ),
    );
  }
}
