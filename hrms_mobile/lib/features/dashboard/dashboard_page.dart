import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../core/di/injection.dart';
import '../../core/routing/app_router.dart';
import '../../core/theme/app_colors.dart';
import '../../l10n/app_l10n.dart';
import '../employees/cubit/employees_cubit.dart' show LoadStatus;
import 'cubit/dashboard_cubit.dart';
import 'data/dashboard_api.dart';
import 'data/dashboard_models.dart';

class DashboardPage extends StatelessWidget {
  const DashboardPage({super.key, this.roleLabel});

  final String? roleLabel;

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => DashboardCubit(sl<DashboardApi>())..load(),
      child: const _DashboardView(),
    );
  }
}

class _DashboardView extends StatelessWidget {
  const _DashboardView();

  @override
  Widget build(BuildContext context) {
    final l = AppL10n.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Image.asset(
          'assets/branding/jaikalki-logo-horizontal-light.png',
          height: 28,
        ),
        centerTitle: false,
      ),
      body: BlocBuilder<DashboardCubit, DashboardState>(
        builder: (context, state) {
          if (state.status == LoadStatus.loading && state.summary == null) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state.summary == null) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(state.error ?? l.somethingWentWrong),
              ),
            );
          }
          final s = state.summary!;
          return RefreshIndicator(
            onRefresh: () => context.read<DashboardCubit>().load(),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _Header(summary: s),
                const SizedBox(height: 16),
                ..._sectionsForRole(context, s),
                const SizedBox(height: 80),
              ],
            ),
          );
        },
      ),
    );
  }

  List<Widget> _sectionsForRole(BuildContext context, DashboardSummary s) {
    final role = s.role;
    if (role == 'director' || role == 'super_admin') {
      return [
        _DirectorWidgets(summary: s),
        const SizedBox(height: 16),
        _CommonEmployeeWidgets(summary: s),
      ];
    }
    if (role == 'hr') {
      return [
        _HRWidgets(summary: s),
        const SizedBox(height: 16),
        _CommonEmployeeWidgets(summary: s),
      ];
    }
    if (role == 'manager') {
      return [
        _ManagerWidgets(summary: s),
        const SizedBox(height: 16),
        _CommonEmployeeWidgets(summary: s),
      ];
    }
    return [_CommonEmployeeWidgets(summary: s)];
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.summary});
  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final firstName = summary.userFullName.split(' ').first;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '★ ${(summary.role ?? 'EMPLOYEE').toUpperCase()}',
              style: theme.textTheme.labelSmall?.copyWith(
                color: AppColors.brandGoldDark,
              ),
            ),
            const SizedBox(height: 4),
            Text('Hi, $firstName', style: theme.textTheme.headlineMedium),
            if (summary.employeeCode != null) ...[
              const SizedBox(height: 2),
              Text(
                summary.employeeCode!,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: AppColors.brandBrownLight,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _CommonEmployeeWidgets extends StatelessWidget {
  const _CommonEmployeeWidgets({required this.summary});
  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    final l = AppL10n.of(context);
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '★ ${l.today.toUpperCase()}',
          style: theme.textTheme.labelSmall
              ?.copyWith(color: AppColors.brandGoldDark),
        ),
        const SizedBox(height: 8),
        _AttendanceCard(today: summary.todayAttendance),
        const SizedBox(height: 12),
        if (summary.leaveBalances.isNotEmpty) ...[
          Text(
            '★ ${l.leaveBalance.toUpperCase()}',
            style: theme.textTheme.labelSmall
                ?.copyWith(color: AppColors.brandGoldDark),
          ),
          const SizedBox(height: 8),
          _LeaveBalances(balances: summary.leaveBalances),
          const SizedBox(height: 12),
        ],
        _StatTile(
          label: l.nextPayday.toUpperCase(),
          value: l.daysToPayday(summary.nextPaydayInDays),
        ),
      ],
    );
  }
}

class _ManagerWidgets extends StatelessWidget {
  const _ManagerWidgets({required this.summary});
  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    final l = AppL10n.of(context);
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '★ TEAM',
          style: theme.textTheme.labelSmall
              ?.copyWith(color: AppColors.brandGoldDark),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: _StatTile(
                label: l.teamAttendance.toUpperCase(),
                value: '${summary.teamAttendancePct.toStringAsFixed(0)}%',
                hint: '${summary.teamPresentToday}/${summary.teamSize}',
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _StatTile(
                label: l.pendingApprovals.toUpperCase(),
                value: '${summary.pendingApprovalsCount}',
                onTap: () =>
                    GoRouter.of(context).push(AppRoutes.approvalsInbox),
              ),
            ),
          ],
        ),
        if (summary.teamToday.isNotEmpty) ...[
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Today',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: AppColors.brandBrownLight,
                    ),
                  ),
                  const SizedBox(height: 8),
                  ...summary.teamToday.take(8).map(
                        (m) => Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Row(
                            children: [
                              Expanded(child: Text(m.fullName)),
                              _StatusPill(status: m.statusToday),
                            ],
                          ),
                        ),
                      ),
                ],
              ),
            ),
          ),
        ],
      ],
    );
  }
}

class _HRWidgets extends StatelessWidget {
  const _HRWidgets({required this.summary});
  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    final l = AppL10n.of(context);
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('★ HR',
            style: theme.textTheme.labelSmall
                ?.copyWith(color: AppColors.brandGoldDark)),
        const SizedBox(height: 8),
        _StatTile(
          label: l.pendingApprovals.toUpperCase(),
          value: '${summary.pendingApprovalsCount}',
          onTap: () => GoRouter.of(context).push(AppRoutes.approvalsInbox),
        ),
        const SizedBox(height: 12),
        if (summary.birthdaysThisWeek.isNotEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    l.birthdaysThisWeek.toUpperCase(),
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: AppColors.brandGoldDark,
                    ),
                  ),
                  const SizedBox(height: 8),
                  ...summary.birthdaysThisWeek.map(
                    (b) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 4),
                      child: Row(
                        children: [
                          const Icon(Icons.cake_outlined,
                              size: 16, color: AppColors.brandGoldDark),
                          const SizedBox(width: 8),
                          Expanded(child: Text(b.fullName)),
                          if (b.dateOfBirth != null)
                            Text(
                              b.dateOfBirth!,
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: AppColors.brandBrownLight,
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        if (summary.probationExpiring.isNotEmpty) ...[
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    l.probationExpiring.toUpperCase(),
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: AppColors.warning,
                    ),
                  ),
                  const SizedBox(height: 8),
                  ...summary.probationExpiring.take(6).map(
                        (p) => Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Row(
                            children: [
                              Expanded(child: Text(p.fullName)),
                              Text(
                                '${p.daysRemaining}d',
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: AppColors.brandBrownLight,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                ],
              ),
            ),
          ),
        ],
      ],
    );
  }
}

class _DirectorWidgets extends StatelessWidget {
  const _DirectorWidgets({required this.summary});
  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    final l = AppL10n.of(context);
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('★ COMPANY',
            style: theme.textTheme.labelSmall
                ?.copyWith(color: AppColors.brandGoldDark)),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: _StatTile(
                label: l.headcount.toUpperCase(),
                value: '${summary.totalHeadcount}',
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: _StatTile(
                label: l.pendingApprovals.toUpperCase(),
                value: '${summary.pendingApprovalsCount}',
                onTap: () =>
                    GoRouter.of(context).push(AppRoutes.approvalsInbox),
              ),
            ),
          ],
        ),
        if (summary.headcountByCategory.isNotEmpty) ...[
          const SizedBox(height: 12),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'CATEGORIES',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: AppColors.brandBrownLight,
                    ),
                  ),
                  const SizedBox(height: 8),
                  ...summary.headcountByCategory.map(
                    (c) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 3),
                      child: Row(
                        children: [
                          Expanded(child: Text(c.key)),
                          Text(
                            '${c.count}',
                            style: theme.textTheme.titleMedium?.copyWith(
                              color: AppColors.brandGoldDark,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ],
    );
  }
}

class _AttendanceCard extends StatelessWidget {
  const _AttendanceCard({required this.today});
  final TodayAttendance today;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final status = today.status ?? 'absent';
    final color = switch (status) {
      'present' => AppColors.success,
      'wfh' => AppColors.info,
      'half_day' => AppColors.warning,
      _ => AppColors.error,
    };
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: () => GoRouter.of(context).push(AppRoutes.attendance),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                width: 4,
                height: 56,
                decoration: BoxDecoration(
                  color: color,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      status.toUpperCase(),
                      style: theme.textTheme.labelSmall?.copyWith(color: color),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      today.checkedIn
                          ? today.checkedOut
                              ? 'Day complete'
                              : 'Checked in${today.checkIn != null ? ' · ${today.checkIn!.split('T').last.substring(0, 5)}' : ''}'
                          : 'Tap to check in',
                      style: theme.textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
              const Icon(Icons.arrow_forward_ios,
                  size: 14, color: AppColors.brandBrownLight),
            ],
          ),
        ),
      ),
    );
  }
}

class _LeaveBalances extends StatelessWidget {
  const _LeaveBalances({required this.balances});
  final List<LeaveBalanceItem> balances;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Wrap(
          spacing: 16,
          runSpacing: 8,
          children: balances.map((b) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  b.code,
                  style: const TextStyle(
                    fontFamily: 'monospace',
                    fontSize: 10,
                    letterSpacing: 1.5,
                    color: AppColors.brandBrownLight,
                  ),
                ),
                Text(
                  '${b.balance}',
                  style: const TextStyle(
                    fontWeight: FontWeight.w700,
                    fontSize: 18,
                    color: AppColors.brandGoldDark,
                  ),
                ),
              ],
            );
          }).toList(),
        ),
      ),
    );
  }
}

class _StatTile extends StatelessWidget {
  const _StatTile({
    required this.label,
    required this.value,
    this.hint,
    this.onTap,
  });
  final String label;
  final String value;
  final String? hint;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(18),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: AppColors.brandBrownLight,
                ),
              ),
              const SizedBox(height: 6),
              Text(value, style: theme.textTheme.headlineSmall),
              if (hint != null) ...[
                const SizedBox(height: 2),
                Text(
                  hint!,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: AppColors.brandBrownLight,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _StatusPill extends StatelessWidget {
  const _StatusPill({required this.status});
  final String status;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      'present' => AppColors.success,
      'wfh' => AppColors.info,
      'half_day' => AppColors.warning,
      'leave' => AppColors.brandGoldDark,
      'holiday' => AppColors.brandBrownLight,
      _ => AppColors.error,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        status.toUpperCase(),
        style: TextStyle(
          fontSize: 10,
          fontFamily: 'monospace',
          letterSpacing: 1.5,
          fontWeight: FontWeight.w700,
          color: color,
        ),
      ),
    );
  }
}
