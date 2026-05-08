import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../core/routing/app_router.dart';
import '../../core/theme/app_colors.dart';
import '../../l10n/app_l10n.dart';

class MoreMenuPage extends StatelessWidget {
  const MoreMenuPage({super.key});

  @override
  Widget build(BuildContext context) {
    final l = AppL10n.of(context);

    final sections = <_MoreSection>[
      _MoreSection('Work', [
        _MoreItem(l.attendance, Icons.fingerprint_outlined, AppRoutes.attendance),
        _MoreItem(l.leaves, Icons.beach_access_outlined, AppRoutes.leaves),
        _MoreItem('Daily plan', Icons.checklist_outlined, AppRoutes.dwp),
        _MoreItem(l.approvals, Icons.inbox_outlined, AppRoutes.approvalsInbox),
        _MoreItem('Field plan', Icons.map_outlined, AppRoutes.fieldHome),
        _MoreItem('Live team map', Icons.location_on_outlined, AppRoutes.fieldLiveMap),
      ]),
      _MoreSection('Sales', [
        _MoreItem('Pipeline', Icons.trending_up_outlined, AppRoutes.salesPipeline),
        _MoreItem('My target', Icons.flag_outlined, AppRoutes.salesTargets),
      ]),
      _MoreSection('Operations', [
        _MoreItem('Verifications', Icons.fact_check_outlined, AppRoutes.verificationQueue),
        _MoreItem('Visitors', Icons.qr_code_2_outlined, AppRoutes.visitors),
        _MoreItem('Book a room', Icons.meeting_room_outlined, AppRoutes.bookRoom),
        _MoreItem('My assets', Icons.devices_outlined, AppRoutes.myAssets),
      ]),
      _MoreSection('Learning', [
        _MoreItem('Courses', Icons.school_outlined, AppRoutes.lmsHome),
        _MoreItem('Badges', Icons.emoji_events_outlined, AppRoutes.lmsBadges),
        _MoreItem('Exams', Icons.quiz_outlined, AppRoutes.exams),
        _MoreItem('Certificates', Icons.workspace_premium_outlined, AppRoutes.myCertificates),
        _MoreItem('Trainers', Icons.mic_external_on_outlined, AppRoutes.trainers),
        _MoreItem('Sessions', Icons.calendar_today_outlined, AppRoutes.trainerSessions),
      ]),
      _MoreSection('Performance', [
        _MoreItem('My goals', Icons.flag_outlined, AppRoutes.myGoals),
        _MoreItem('360 feedback', Icons.rate_review_outlined, AppRoutes.feedbackInbox),
        _MoreItem('Director dashboard', Icons.dashboard_outlined, AppRoutes.directorDashboard),
      ]),
      _MoreSection('People', [
        _MoreItem(l.employees, Icons.groups_outlined, AppRoutes.employees),
        _MoreItem('Internal jobs', Icons.work_outline, AppRoutes.browseJobs),
        _MoreItem('Resignation', Icons.exit_to_app_outlined, AppRoutes.resignation),
        _MoreItem('Justice Portal', Icons.shield_outlined, AppRoutes.justice),
      ]),
      _MoreSection('Money', [
        _MoreItem('Payroll', Icons.account_balance_wallet_outlined, AppRoutes.payroll),
        _MoreItem('Intern expenses', Icons.flight_takeoff_outlined, AppRoutes.internExpenses),
      ]),
      _MoreSection('Account', [
        _MoreItem('Notifications', Icons.notifications_outlined, AppRoutes.notifications),
        _MoreItem('Enable 2FA', Icons.security_outlined, AppRoutes.mfaSetup),
        _MoreItem(l.settings, Icons.settings_outlined, AppRoutes.settings),
      ]),
    ];

    return Scaffold(
      appBar: AppBar(title: Text(l.more)),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 24),
        children: [
          for (final s in sections) _SectionBlock(section: s),
        ],
      ),
    );
  }
}

class _MoreItem {
  final String label;
  final IconData icon;
  final String route;
  _MoreItem(this.label, this.icon, this.route);
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
            // Adaptive column count: 4 on tablets, 3 on phones, 2 on
            // really narrow screens — keeps tiles big enough to fit the
            // icon + 2-line label without overflowing.
            final width = constraints.maxWidth;
            final cols = width >= 720 ? 4 : (width >= 360 ? 3 : 2);
            return GridView.count(
              crossAxisCount: cols,
              physics: const NeverScrollableScrollPhysics(),
              shrinkWrap: true,
              mainAxisSpacing: 10,
              crossAxisSpacing: 10,
              childAspectRatio: 0.95,
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
