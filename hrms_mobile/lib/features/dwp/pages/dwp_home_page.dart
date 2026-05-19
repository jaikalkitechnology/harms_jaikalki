import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/injection.dart';
import '../../../core/routing/app_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../employees/cubit/employees_cubit.dart' show LoadStatus;
import '../cubit/dwp_cubit.dart';
import '../data/dwp_api.dart';
import '../data/dwp_models.dart';

class DwpHomePage extends StatelessWidget {
  const DwpHomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => DwpHomeCubit(sl<DwpApi>())..load(),
      child: const _HomeView(),
    );
  }
}

class _HomeView extends StatelessWidget {
  const _HomeView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Daily plan')),
      body: BlocBuilder<DwpHomeCubit, DwpHomeState>(
        builder: (context, state) {
          if (state.status == LoadStatus.loading && state.today.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }
          return RefreshIndicator(
            onRefresh: () => context.read<DwpHomeCubit>().load(),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _StreakCard(streak: state.streakDays),
                const SizedBox(height: 16),
                _TodayActions(state: state),
                const SizedBox(height: 24),
                if (state.history.isNotEmpty) ...[
                  Text('★ HISTORY',
                      style: Theme.of(context).textTheme.labelSmall?.copyWith(
                            color: AppColors.brandGoldDark,
                          )),
                  const SizedBox(height: 8),
                  ...state.history.take(20).map((s) => _HistoryRow(submission: s)),
                ],
              ],
            ),
          );
        },
      ),
    );
  }
}

class _StreakCard extends StatelessWidget {
  const _StreakCard({required this.streak});
  final int streak;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: AppColors.brandGold.withOpacity(0.18),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(Icons.local_fire_department,
                  color: AppColors.brandGoldDark, size: 28),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('STREAK',
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: context.textMuted,
                      )),
                  Text(
                    streak == 0
                        ? 'Start your streak today'
                        : '$streak day${streak == 1 ? '' : 's'}',
                    style: theme.textTheme.titleLarge,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TodayActions extends StatelessWidget {
  const _TodayActions({required this.state});
  final DwpHomeState state;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('★ TODAY',
            style: theme.textTheme.labelSmall?.copyWith(
              color: AppColors.brandGoldDark,
            )),
        const SizedBox(height: 8),
        _ActionTile(
          title: 'Morning plan',
          subtitle: 'List today\'s tasks at the start of the day',
          icon: Icons.wb_sunny_outlined,
          done: state.hasMorning,
          onTap: state.hasMorning
              ? null
              : () => GoRouter.of(context).push(AppRoutes.dwpMorning),
        ),
        const SizedBox(height: 8),
        _ActionTile(
          title: 'EOD summary',
          subtitle: 'Wrap up the day with what you completed',
          icon: Icons.nightlight_outlined,
          done: state.hasEod,
          onTap: state.hasEod
              ? null
              : () => GoRouter.of(context).push(AppRoutes.dwpEod),
        ),
      ],
    );
  }
}

class _ActionTile extends StatelessWidget {
  const _ActionTile({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.done,
    this.onTap,
  });
  final String title;
  final String subtitle;
  final IconData icon;
  final bool done;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Icon(icon,
                  size: 32,
                  color:
                      done ? AppColors.success : AppColors.brandGoldDark),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: theme.textTheme.titleMedium),
                    const SizedBox(height: 2),
                    Text(
                      done ? '✓ Submitted' : subtitle,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: done
                            ? AppColors.success
                            : context.textMuted,
                      ),
                    ),
                  ],
                ),
              ),
              if (!done)
                const Icon(Icons.arrow_forward_ios,
                    size: 14, color: context.textMuted),
            ],
          ),
        ),
      ),
    );
  }
}

class _HistoryRow extends StatelessWidget {
  const _HistoryRow({required this.submission});
  final DwpSubmission submission;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final tasks = submission.fields
        .firstWhere(
          (f) => f.fieldKey == 'tasks',
          orElse: () => const DwpSubmissionField(fieldKey: 'tasks'),
        )
        .value;
    return Card(
      child: ListTile(
        leading: Icon(
          submission.type == 'morning'
              ? Icons.wb_sunny_outlined
              : Icons.nightlight_outlined,
          color: AppColors.brandGoldDark,
        ),
        title: Text('${submission.date} · ${submission.type.toUpperCase()}'),
        subtitle: tasks == null
            ? null
            : Text(
                tasks,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: theme.textTheme.bodySmall,
              ),
        trailing: submission.totalHours != null
            ? Text('${submission.totalHours}h',
                style: theme.textTheme.bodySmall?.copyWith(
                  color: context.textMuted,
                ))
            : null,
      ),
    );
  }
}
