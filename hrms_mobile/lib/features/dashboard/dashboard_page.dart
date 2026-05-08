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
      // Edge-to-edge brown header → no AppBar.
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
              padding: EdgeInsets.zero,
              children: [
                _BrandHeader(summary: s),
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _AttendanceHeroCard(today: s.todayAttendance),
                      const SizedBox(height: 20),
                      _SectionHeader(
                        title: 'Quick',
                        emphasis: 'actions',
                        link: 'VIEW ALL →',
                        onTap: () => GoRouter.of(context).push('/more'),
                      ),
                      const SizedBox(height: 10),
                      const _QuickActionsGrid(),
                      const SizedBox(height: 24),
                      ..._sectionsForRole(context, s),
                      const SizedBox(height: 80),
                    ],
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  List<Widget> _sectionsForRole(BuildContext context, DashboardSummary s) {
    final role = s.role;
    final widgets = <Widget>[
      _SectionHeader(title: 'Recent', emphasis: 'updates', link: ''),
      const SizedBox(height: 8),
      _RecentUpdates(summary: s),
      const SizedBox(height: 20),
    ];
    if (role == 'director' || role == 'super_admin') {
      widgets.add(_DirectorWidgets(summary: s));
    } else if (role == 'hr') {
      widgets.add(_HRWidgets(summary: s));
    } else if (role == 'manager') {
      widgets.add(_ManagerWidgets(summary: s));
    }
    return widgets;
  }
}

// ── Brand brown header ───────────────────────────────────────────────
class _BrandHeader extends StatelessWidget {
  const _BrandHeader({required this.summary});
  final DashboardSummary summary;

  String _greeting() {
    final h = DateTime.now().hour;
    if (h < 12) return '★ GOOD MORNING';
    if (h < 17) return '★ GOOD AFTERNOON';
    return '★ GOOD EVENING';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final firstName = summary.userFullName.split(' ').first;
    final initial =
        firstName.isNotEmpty ? firstName[0].toUpperCase() : '?';
    final rest = summary.userFullName.contains(' ')
        ? ' ${summary.userFullName.split(' ').sublist(1).join(' ')}'
        : '';

    final isPresent = summary.todayAttendance.checkedIn;
    final totalLeaves = summary.leaveBalances.fold<num>(
      0,
      (a, b) => a + b.balance,
    );

    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [Color(0xFF2D1810), Color(0xFF3D2817)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      padding: EdgeInsets.fromLTRB(
        20,
        MediaQuery.of(context).padding.top + 18,
        20,
        24,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _greeting(),
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: AppColors.brandGold,
                        letterSpacing: 1.6,
                      ),
                    ),
                    const SizedBox(height: 4),
                    RichText(
                      text: TextSpan(
                        style: theme.textTheme.headlineMedium?.copyWith(
                          color: AppColors.warmWhite,
                          fontWeight: FontWeight.w700,
                        ),
                        children: [
                          TextSpan(text: firstName),
                          if (rest.isNotEmpty)
                            TextSpan(
                              text: rest,
                              style: const TextStyle(
                                fontStyle: FontStyle.italic,
                                color: AppColors.brandGold,
                              ),
                            ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppColors.brandGold.withOpacity(0.18),
                  border: Border.all(
                    color: AppColors.brandGold.withOpacity(0.4),
                    width: 2,
                  ),
                ),
                alignment: Alignment.center,
                child: Text(
                  initial,
                  style: const TextStyle(
                    color: AppColors.warmWhite,
                    fontSize: 22,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 22),
          Container(
            padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 10),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.06),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: Colors.white.withOpacity(0.10)),
            ),
            child: Row(
              children: [
                Expanded(
                  child: _HeaderStat(
                    num: isPresent ? 'IN' : '—',
                    label: 'TODAY',
                  ),
                ),
                _HeaderDivider(),
                Expanded(
                  child: _HeaderStat(
                    num: totalLeaves.toStringAsFixed(0),
                    label: 'LEAVES',
                  ),
                ),
                _HeaderDivider(),
                Expanded(
                  child: _HeaderStat(
                    num: '${summary.nextPaydayInDays}d',
                    label: 'PAYDAY',
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _HeaderStat extends StatelessWidget {
  const _HeaderStat({required this.num, required this.label});
  final String num;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(
          num,
          style: const TextStyle(
            fontSize: 22,
            color: AppColors.brandGold,
            fontWeight: FontWeight.w700,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: const TextStyle(
            color: AppColors.warmWhite,
            fontSize: 9,
            letterSpacing: 1.6,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

class _HeaderDivider extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      width: 1,
      height: 32,
      color: Colors.white.withOpacity(0.15),
    );
  }
}

// ── Section header ───────────────────────────────────────────────────
class _SectionHeader extends StatelessWidget {
  const _SectionHeader({
    required this.title,
    required this.emphasis,
    this.link,
    this.onTap,
  });
  final String title;
  final String emphasis;
  final String? link;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      children: [
        RichText(
          text: TextSpan(
            style: theme.textTheme.titleLarge?.copyWith(
              color: context.textPrimary,
              fontWeight: FontWeight.w700,
            ),
            children: [
              TextSpan(text: '$title '),
              TextSpan(
                text: emphasis,
                style: const TextStyle(
                  fontStyle: FontStyle.italic,
                  color: AppColors.brandGoldDark,
                ),
              ),
            ],
          ),
        ),
        const Spacer(),
        if (link != null && link!.isNotEmpty)
          GestureDetector(
            onTap: onTap,
            child: Text(
              link!,
              style: theme.textTheme.labelSmall?.copyWith(
                color: AppColors.brandGoldDark,
                letterSpacing: 1.4,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
      ],
    );
  }
}

// ── Attendance hero card ─────────────────────────────────────────────
class _AttendanceHeroCard extends StatelessWidget {
  const _AttendanceHeroCard({required this.today});
  final TodayAttendance today;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final checkInTime = today.checkIn?.split('T').last.substring(0, 5);
    final isCheckedIn = today.checkedIn && !today.checkedOut;
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: () => GoRouter.of(context).push(AppRoutes.attendance),
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 12,
                    height: 12,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: isCheckedIn
                          ? AppColors.success
                          : AppColors.brandBrownLight,
                      boxShadow: isCheckedIn
                          ? [
                              BoxShadow(
                                color: AppColors.success.withOpacity(0.5),
                                blurRadius: 8,
                              ),
                            ]
                          : null,
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: RichText(
                      text: TextSpan(
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: context.textPrimary,
                          fontWeight: FontWeight.w600,
                        ),
                        children: [
                          TextSpan(
                            text: today.checkedOut
                                ? 'Day complete'
                                : isCheckedIn
                                    ? 'Checked in '
                                    : 'Not checked in',
                          ),
                          if (isCheckedIn && checkInTime != null)
                            TextSpan(
                              text: 'at $checkInTime',
                              style: const TextStyle(
                                fontStyle: FontStyle.italic,
                                color: AppColors.brandGoldDark,
                              ),
                            ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 14),
                decoration: BoxDecoration(
                  gradient: const LinearGradient(
                    colors: [Color(0xFFF4B71F), Color(0xFFC8941A)],
                  ),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Center(
                  child: Text(
                    isCheckedIn
                        ? 'CHECK OUT  →'
                        : today.checkedOut
                            ? 'VIEW ATTENDANCE  →'
                            : 'CHECK IN  →',
                    style: const TextStyle(
                      color: AppColors.brandBrownDarker,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 1.4,
                      fontSize: 12,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Quick actions grid ───────────────────────────────────────────────
class _QuickActionsGrid extends StatelessWidget {
  const _QuickActionsGrid();

  @override
  Widget build(BuildContext context) {
    final actions = [
      _QuickAction(
        Icons.event_outlined,
        'Apply\nLeave',
        AppRoutes.leaves,
      ),
      _QuickAction(
        Icons.timer_outlined,
        'Time\nSheet',
        AppRoutes.attendance,
      ),
      _QuickAction(
        Icons.description_outlined,
        'Pay\nSlip',
        AppRoutes.payroll,
      ),
      _QuickAction(
        Icons.account_balance_wallet_outlined,
        'Reim-\nburse',
        AppRoutes.payroll,
      ),
    ];
    return Row(
      children: [
        for (var i = 0; i < actions.length; i++) ...[
          Expanded(child: _QuickActionTile(action: actions[i])),
          if (i < actions.length - 1) const SizedBox(width: 8),
        ],
      ],
    );
  }
}

class _QuickAction {
  final IconData icon;
  final String label;
  final String route;
  _QuickAction(this.icon, this.label, this.route);
}

class _QuickActionTile extends StatelessWidget {
  const _QuickActionTile({required this.action});
  final _QuickAction action;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: () => GoRouter.of(context).push(action.route),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14),
        decoration: BoxDecoration(
          color: Theme.of(context).cardColor,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: AppColors.brandGold.withOpacity(0.25),
          ),
        ),
        child: Column(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.brandGold.withOpacity(0.18),
              ),
              child: Icon(action.icon,
                  color: AppColors.brandGoldDark, size: 18),
            ),
            const SizedBox(height: 8),
            Text(
              action.label,
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                height: 1.2,
                color: context.textPrimary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── Recent updates ───────────────────────────────────────────────────
class _RecentUpdates extends StatelessWidget {
  const _RecentUpdates({required this.summary});
  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    final items = <_NotifPreview>[
      _NotifPreview(
        Icons.event_available_outlined,
        AppColors.success,
        'Today’s attendance',
        summary.todayAttendance.checkedIn
            ? 'You’re ${summary.todayAttendance.status?.toUpperCase() ?? "CHECKED IN"}'
            : 'Don’t forget to check in',
      ),
      _NotifPreview(
        Icons.account_balance_wallet_outlined,
        AppColors.brandGoldDark,
        'Next payday',
        '${summary.nextPaydayInDays} days to go',
      ),
      _NotifPreview(
        Icons.beach_access_outlined,
        AppColors.brandBrownLight,
        'Leave balance',
        summary.leaveBalances
            .map((b) => '${b.code} ${b.balance.toStringAsFixed(0)}')
            .join(' · '),
      ),
    ].where((i) => i.subtitle.trim().isNotEmpty).toList();
    return Column(
      children: [
        for (final n in items) ...[
          Card(
            child: Padding(
              padding: const EdgeInsets.symmetric(
                  horizontal: 14, vertical: 10),
              child: Row(
                children: [
                  Container(
                    width: 38,
                    height: 38,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: n.color.withOpacity(0.15),
                    ),
                    child: Icon(n.icon, color: n.color, size: 18),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          n.title,
                          style: TextStyle(
                            color: context.textPrimary,
                            fontWeight: FontWeight.w600,
                            fontSize: 13,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          n.subtitle,
                          style: const TextStyle(
                            color: AppColors.brandBrownLight,
                            fontSize: 11,
                            fontFamily: 'monospace',
                            letterSpacing: 1.0,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 6),
        ],
      ],
    );
  }
}

class _NotifPreview {
  final IconData icon;
  final Color color;
  final String title;
  final String subtitle;
  _NotifPreview(this.icon, this.color, this.title, this.subtitle);
}

// ── Role-specific add-ons ────────────────────────────────────────────
class _ManagerWidgets extends StatelessWidget {
  const _ManagerWidgets({required this.summary});
  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    final l = AppL10n.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _SectionHeader(title: 'Team', emphasis: 'overview'),
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
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _SectionHeader(title: 'HR', emphasis: 'queue'),
        const SizedBox(height: 8),
        _StatTile(
          label: l.pendingApprovals.toUpperCase(),
          value: '${summary.pendingApprovalsCount}',
          onTap: () => GoRouter.of(context).push(AppRoutes.approvalsInbox),
        ),
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
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _SectionHeader(title: 'Company', emphasis: 'snapshot'),
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
      ],
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
