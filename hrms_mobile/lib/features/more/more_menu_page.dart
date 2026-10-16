import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../core/di/injection.dart';
import '../../core/modules/enabled_modules_service.dart';
import '../../core/routing/app_router.dart';
import '../../core/theme/app_colors.dart';
import '../../l10n/app_l10n.dart';
import '../auth/presentation/bloc/auth_bloc.dart';

class MoreMenuPage extends StatefulWidget {
  const MoreMenuPage({super.key});

  @override
  State<MoreMenuPage> createState() => _MoreMenuPageState();
}

class _MoreMenuPageState extends State<MoreMenuPage> {
  late final EnabledModulesService _modules;

  @override
  void initState() {
    super.initState();
    _modules = sl<EnabledModulesService>();
    _modules.addListener(_onModulesChanged);
    // Background refresh in case admin updated the mapping recently.
    _modules.refresh();
  }

  @override
  void dispose() {
    _modules.removeListener(_onModulesChanged);
    super.dispose();
  }

  void _onModulesChanged() {
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    final l = AppL10n.of(context);

    final allSections = <_MoreSection>[
      _MoreSection('Work', [
        _MoreItem('leaves', l.leaves, Icons.beach_access_outlined, AppRoutes.leaves),
        _MoreItem('dwp', 'Daily plan', Icons.checklist_outlined, AppRoutes.dwp),
        _MoreItem('approvals', l.approvals, Icons.inbox_outlined, AppRoutes.approvalsInbox),
        _MoreItem('leave_approvals', 'Leave approvals', Icons.fact_check_outlined, AppRoutes.managerInbox),
        _MoreItem('field_plan', 'Field plan', Icons.map_outlined, AppRoutes.fieldHome),
        _MoreItem('live_team_map', 'Live team map', Icons.location_on_outlined, AppRoutes.fieldLiveMap),
      ]),
      _MoreSection('Documents', [
        _MoreItem('documents', 'Letters & policies', Icons.folder_copy_outlined, AppRoutes.documents),
        _MoreItem('certificates', 'Certificates', Icons.workspace_premium_outlined, AppRoutes.myCertificates),
      ]),
      _MoreSection('Sales', [
        _MoreItem('my_leads', 'Leads', Icons.person_add_alt_1_outlined, AppRoutes.myLeads),
        _MoreItem('sales_pipeline', 'Pipeline', Icons.trending_up_outlined, AppRoutes.salesPipeline),
        _MoreItem('sales_targets', 'My target', Icons.flag_outlined, AppRoutes.salesTargets),
      ]),
      _MoreSection('Operations', [
        _MoreItem('verifications', 'Verifications', Icons.fact_check_outlined, AppRoutes.verificationQueue),
        _MoreItem('visitors', 'Visitors', Icons.qr_code_2_outlined, AppRoutes.visitors),
        _MoreItem('book_room', 'Book a room', Icons.meeting_room_outlined, AppRoutes.bookRoom),
        _MoreItem('my_assets', 'My assets', Icons.devices_outlined, AppRoutes.myAssets),
      ]),
      _MoreSection('Learning', [
        _MoreItem('lms', 'Courses', Icons.school_outlined, AppRoutes.lmsHome),
        _MoreItem('badges', 'Badges', Icons.emoji_events_outlined, AppRoutes.lmsBadges),
        _MoreItem('exams', 'Exams', Icons.quiz_outlined, AppRoutes.exams),
        _MoreItem('trainers', 'Trainers', Icons.mic_external_on_outlined, AppRoutes.trainers),
        _MoreItem('sessions', 'Sessions', Icons.calendar_today_outlined, AppRoutes.trainerSessions),
      ]),
      _MoreSection('Performance', [
        _MoreItem('my_goals', 'My goals', Icons.flag_outlined, AppRoutes.myGoals),
        _MoreItem('feedback_360', '360 feedback', Icons.rate_review_outlined, AppRoutes.feedbackInbox),
        _MoreItem('director_dashboard', 'Director dashboard', Icons.dashboard_outlined, AppRoutes.directorDashboard),
      ]),
      _MoreSection('People', [
        _MoreItem('employees', l.employees, Icons.groups_outlined, AppRoutes.employees),
        _MoreItem('internal_jobs', 'Internal jobs', Icons.work_outline, AppRoutes.browseJobs),
        _MoreItem('resignation', 'Resignation', Icons.exit_to_app_outlined, AppRoutes.resignation),
        _MoreItem('team_exits', 'Team exits', Icons.group_remove_outlined, AppRoutes.teamExits),
        _MoreItem('justice', 'Justice Portal', Icons.shield_outlined, AppRoutes.justice),
      ]),
      _MoreSection('Money', [
        _MoreItem('payroll', 'Payroll', Icons.account_balance_wallet_outlined, AppRoutes.payroll),
        _MoreItem('intern_expenses', 'Intern expenses', Icons.flight_takeoff_outlined, AppRoutes.internExpenses),
      ]),
      _MoreSection('Account', [
        _MoreItem('notifications', 'Notifications', Icons.notifications_outlined, AppRoutes.notifications),
        _MoreItem('mfa_setup', 'Enable 2FA', Icons.security_outlined, AppRoutes.mfaSetup),
        _MoreItem('settings', l.settings, Icons.settings_outlined, AppRoutes.settings),
      ]),
    ];

    // Apply the per-department whitelist. `EnabledModulesService.isEnabled`
    // returns true when no whitelist exists yet (offline / first launch),
    // so we never accidentally hide everything.
    // Team exits is a reporting-manager tool (not department-gated).
    final user = context.watch<AuthBloc>().state.user;
    final managesPeople = user != null &&
        (user.hasRole('manager') || user.hasPermission('approval.act'));
    // Documents is for everyone (also before the cached whitelist
    // picks up the new key).
    bool shown(_MoreItem i) => switch (i.key) {
          'team_exits' => managesPeople,
          'documents' => true,
          _ => _modules.isEnabled(i.key),
        };

    final sections = <_MoreSection>[];
    for (final s in allSections) {
      final visible = s.items.where(shown).toList();
      if (visible.isNotEmpty) {
        sections.add(_MoreSection(s.title, visible));
      }
    }

    return Scaffold(
      appBar: AppBar(title: Text(l.more)),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 24),
        children: [
          for (final s in sections) _SectionBlock(section: s),
          if (sections.isEmpty)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 64),
              child: Center(
                child: Text(
                  'No modules enabled for your department yet.\n'
                  'Please contact your admin.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: context.textMuted),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _MoreItem {
  final String key;
  final String label;
  final IconData icon;
  final String route;
  _MoreItem(this.key, this.label, this.icon, this.route);
}

class _MoreSection {
  final String title;
  final List<_MoreItem> items;
  _MoreSection(this.title, this.items);
}

class _SectionBlock extends StatelessWidget {
  const _SectionBlock({required this.section});
  final _MoreSection section;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(8, 16, 8, 8),
          child: Text(
            section.title.toUpperCase(),
            style: TextStyle(
              fontSize: 11,
              letterSpacing: 1.6,
              fontWeight: FontWeight.w700,
              color: AppColors.brandGoldDark,
            ),
          ),
        ),
        LayoutBuilder(
          builder: (context, constraints) {
            final width = constraints.maxWidth;
            final cols = width >= 720 ? 4 : (width >= 360 ? 3 : 2);
            return GridView.count(
              crossAxisCount: cols,
              physics: const NeverScrollableScrollPhysics(),
              shrinkWrap: true,
              mainAxisSpacing: 10,
              crossAxisSpacing: 10,
              childAspectRatio: 0.82,
              children: section.items.map((i) => _MoreTile(item: i)).toList(),
            );
          },
        ),
      ],
    );
  }
}

class _MoreTile extends StatelessWidget {
  const _MoreTile({required this.item});
  final _MoreItem item;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      margin: EdgeInsets.zero,
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: () => GoRouter.of(context).push(item.route),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 10),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.brandGold.withOpacity(0.18),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(item.icon,
                    size: 24, color: AppColors.brandGoldDark),
              ),
              const SizedBox(height: 8),
              Flexible(
                child: Text(
                  item.label,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: context.textPrimary,
                    fontWeight: FontWeight.w500,
                    height: 1.15,
                  ),
                  textAlign: TextAlign.center,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
