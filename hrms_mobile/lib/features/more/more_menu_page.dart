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
    final items = <_MoreItem>[
      _MoreItem('Field plan', Icons.map_outlined, AppRoutes.fieldHome),
      _MoreItem('Live team map', Icons.location_on_outlined, AppRoutes.fieldLiveMap),
      _MoreItem('Sales pipeline', Icons.trending_up_outlined, AppRoutes.salesPipeline),
      _MoreItem('My sales target', Icons.flag_outlined, AppRoutes.salesTargets),
      _MoreItem('Verifications', Icons.fact_check_outlined, AppRoutes.verificationQueue),
      _MoreItem('Learning', Icons.school_outlined, AppRoutes.lmsHome),
      _MoreItem('My badges', Icons.emoji_events_outlined, AppRoutes.lmsBadges),
      _MoreItem('Exams & certificates', Icons.workspace_premium_outlined, AppRoutes.exams),
      _MoreItem('Trainers', Icons.mic_external_on_outlined, AppRoutes.trainers),
      _MoreItem('Training sessions', Icons.calendar_today_outlined, AppRoutes.trainerSessions),
      _MoreItem('Justice Portal', Icons.shield_outlined, AppRoutes.justice),
      _MoreItem('Payroll', Icons.account_balance_wallet_outlined,
          AppRoutes.payroll),
      _MoreItem('Daily plan', Icons.checklist_outlined, AppRoutes.dwp),
      _MoreItem(l.leaves, Icons.beach_access_outlined, AppRoutes.leaves),
      _MoreItem(l.attendance, Icons.fingerprint_outlined, AppRoutes.attendance),
      _MoreItem(l.employees, Icons.groups_outlined, AppRoutes.employees),
      _MoreItem(l.approvals, Icons.inbox_outlined, AppRoutes.approvalsInbox),
      _MoreItem('Intern expenses', Icons.flight_takeoff_outlined,
          AppRoutes.internExpenses),
      _MoreItem(l.settings, Icons.settings_outlined, AppRoutes.settings),
    ];

    return Scaffold(
      appBar: AppBar(title: Text(l.more)),
      body: GridView.count(
        padding: const EdgeInsets.all(16),
        crossAxisCount: 3,
        mainAxisSpacing: 12,
        crossAxisSpacing: 12,
        childAspectRatio: 0.9,
        children: items.map((i) => _MoreTile(item: i)).toList(),
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

class _MoreTile extends StatelessWidget {
  const _MoreTile({required this.item});
  final _MoreItem item;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: () => GoRouter.of(context).push(item.route),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.brandGold.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Icon(item.icon,
                    size: 28, color: AppColors.brandGoldDark),
              ),
              const SizedBox(height: 10),
              Text(
                item.label,
                style: theme.textTheme.bodyMedium,
                textAlign: TextAlign.center,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
