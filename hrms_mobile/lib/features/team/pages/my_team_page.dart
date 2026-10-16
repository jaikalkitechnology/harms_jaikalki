import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/injection.dart';
import '../../../core/routing/app_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../incentives/data/incentives_api.dart';
import '../data/team_api.dart';
import '../widgets/team_widgets.dart';

/// My team: today's attendance, daily plans and targets for everyone
/// below you. People who lead a team show their team's figures; tap to
/// open that team and go a level down.
class MyTeamPage extends StatefulWidget {
  const MyTeamPage({super.key, this.rootId, this.rootName});

  /// Open someone else's team (one of yours); null = your own.
  final int? rootId;
  final String? rootName;

  @override
  State<MyTeamPage> createState() => _MyTeamPageState();
}

class _MyTeamPageState extends State<MyTeamPage> {
  bool _everyone = false;
  bool _attentionOnly = false;
  late Future<TeamOverview> _future = _load();

  Future<TeamOverview> _load() =>
      sl<TeamApi>().overview(everyone: _everyone, rootId: widget.rootId);

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  void _openTeam(TeamMemberRow m) => context.push(
        '${AppRoutes.myTeam}?root=${m.employeeId}&name=${Uri.encodeComponent(m.name)}',
      );

  void _openMember(TeamMemberRow m) =>
      context.push('${AppRoutes.teamMember}/${m.employeeId}');

  @override
  Widget build(BuildContext context) {
    final title = widget.rootId == null
        ? 'My team'
        : "${widget.rootName ?? 'Their'}'s team";
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<TeamOverview>(
          future: _future,
          builder: (context, snap) {
            if (snap.hasError) {
              return ListView(
                padding: const EdgeInsets.all(24),
                children: const [
                  SizedBox(height: 80),
                  Text(
                    'Could not load your team. Pull down to try again.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: AppColors.textMuted),
                  ),
                ],
              );
            }
            if (!snap.hasData) return const Center(child: CircularProgressIndicator());
            final d = snap.data!;
            final attention = d.members.where((m) => m.needsAttention).toList();
            final rows = _attentionOnly ? attention : d.members;
            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
              children: [
                SegmentedButton<bool>(
                  segments: const [
                    ButtonSegment(value: false, label: Text('Direct reports')),
                    ButtonSegment(value: true, label: Text('Everyone below')),
                  ],
                  selected: {_everyone},
                  showSelectedIcon: false,
                  onSelectionChanged: (v) {
                    setState(() {
                      _everyone = v.first;
                      _future = _load();
                    });
                  },
                ),
                const SizedBox(height: 14),
                _Summary(s: d.summary),
                if (widget.rootId == null) const _IncentiveReviewBanner(),
                const SizedBox(height: 16),
                Row(
                  children: [
                    ChoiceChip(
                      label: Text('Everyone (${d.members.length})'),
                      selected: !_attentionOnly,
                      onSelected: (_) => setState(() => _attentionOnly = false),
                    ),
                    const SizedBox(width: 8),
                    ChoiceChip(
                      label: Text('Needs attention (${attention.length})'),
                      selected: _attentionOnly,
                      onSelected: (_) => setState(() => _attentionOnly = true),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                if (rows.isEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 48),
                    child: Text(
                      d.members.isEmpty
                          ? 'Nobody reports to you yet.'
                          : 'Everyone is on track today.',
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: AppColors.textMuted),
                    ),
                  )
                else
                  for (final m in rows)
                    _MemberCard(
                      m: m,
                      showManager: _everyone,
                      onTap: () => _openMember(m),
                      onOpenTeam: m.team == null ? null : () => _openTeam(m),
                    ),
              ],
            );
          },
        ),
      ),
    );
  }
}

/// "3 incentives waiting for your review" — only when there are some.
class _IncentiveReviewBanner extends StatefulWidget {
  const _IncentiveReviewBanner();

  @override
  State<_IncentiveReviewBanner> createState() => _IncentiveReviewBannerState();
}

class _IncentiveReviewBannerState extends State<_IncentiveReviewBanner> {
  late final Future<int> _count = sl<IncentivesApi>().pendingReviews().catchError((_) => 0);

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<int>(
      future: _count,
      builder: (context, snap) {
        final n = snap.data ?? 0;
        if (n == 0) return const SizedBox.shrink();
        return Padding(
          padding: const EdgeInsets.only(top: 12),
          child: Material(
            color: AppColors.brandGold.withOpacity(0.14),
            borderRadius: BorderRadius.circular(12),
            child: ListTile(
              leading: const Icon(Icons.emoji_events_outlined, color: AppColors.brandGold),
              title: Text('$n incentive${n == 1 ? '' : 's'} waiting for your review',
                  style: TextStyle(color: context.textPrimary, fontWeight: FontWeight.w600)),
              trailing: const Icon(Icons.chevron_right, color: AppColors.brandGold),
              onTap: () => context.push(AppRoutes.incentiveReview),
            ),
          ),
        );
      },
    );
  }
}

class _Summary extends StatelessWidget {
  const _Summary({required this.s});
  final TeamRollup s;

  @override
  Widget build(BuildContext context) {
    final tiles = [
      ('Present', '${s.presentTotal}',
          '${s.attendancePct == null ? '' : '${s.attendancePct!.toStringAsFixed(0)}%'}'
          '${s.late > 0 ? ' · ${s.late} late' : ''}', AppColors.successText),
      ('On leave', '${s.onLeave}', '${s.off} off today', null),
      ('Absent / not in', '${s.absent + s.notIn}', '${s.absent} absent', s.absent > 0 ? AppColors.errorText : null),
      ('Daily plans', '${s.dwpMorning}/${s.size}', '${s.dwpEod} end-of-day', null),
      ('Tasks', '${s.tasksOpen}', '${s.tasksOverdue} overdue', s.tasksOverdue > 0 ? AppColors.errorText : null),
      ('Target', s.targetPct == null ? '—' : '${s.targetPct!.toStringAsFixed(0)}%',
          s.withTarget == 0 ? 'no targets' : '${rupees(s.achievedAmount)} of ${rupees(s.targetAmount)}', null),
    ];
    return GridView.count(
      crossAxisCount: 3,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 8,
      crossAxisSpacing: 8,
      childAspectRatio: 1.05,
      children: [
        for (final t in tiles)
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: context.surfaceCard,
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.brandGold.withOpacity(0.15)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(t.$1.toUpperCase(),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: AppColors.textMuted, fontSize: 10, letterSpacing: 0.6)),
                Text(t.$2,
                    style: TextStyle(
                      color: t.$4 ?? context.textPrimary,
                      fontSize: 22,
                      fontWeight: FontWeight.w700,
                    )),
                Text(t.$3,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(color: AppColors.textFaint, fontSize: 10.5)),
              ],
            ),
          ),
      ],
    );
  }
}

class _MemberCard extends StatelessWidget {
  const _MemberCard({
    required this.m,
    required this.showManager,
    required this.onTap,
    required this.onOpenTeam,
  });
  final TeamMemberRow m;
  final bool showManager;
  final VoidCallback onTap;
  final VoidCallback? onOpenTeam;

  @override
  Widget build(BuildContext context) {
    final subtitle = [
      m.designation ?? m.code,
      if (showManager && m.level > 1 && m.managerName != null) 'under ${m.managerName}',
    ].join(' · ');
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  PersonAvatar(name: m.name, photoUrl: m.photoUrl),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(m.name,
                            style: TextStyle(
                              color: context.textPrimary,
                              fontWeight: FontWeight.w600,
                              fontSize: 15,
                            )),
                        Text(subtitle,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
                        const SizedBox(height: 6),
                        PlanMarks(morning: m.dwpMorning, eod: m.dwpEod),
                        if (m.tasksOpen > 0)
                          Padding(
                            padding: const EdgeInsets.only(top: 4),
                            child: Text(
                              '${m.tasksOpen} open task${m.tasksOpen == 1 ? '' : 's'}'
                              '${m.tasksOverdue > 0 ? ' · ${m.tasksOverdue} overdue' : ''}',
                              style: TextStyle(
                                fontSize: 12,
                                color: m.tasksOverdue > 0 ? AppColors.errorText : AppColors.textMuted,
                              ),
                            ),
                          ),
                      ],
                    ),
                  ),
                  StatusPill(m.today),
                ],
              ),
              if (m.target != null) ...[
                const SizedBox(height: 10),
                TargetProgress(
                  pct: m.target!.pct,
                  caption: 'Target · ${targetCaption(m.target!)}',
                ),
              ],
              if (onOpenTeam != null) ...[
                const SizedBox(height: 10),
                Material(
                  color: AppColors.brandGold.withOpacity(0.10),
                  borderRadius: BorderRadius.circular(10),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(10),
                    onTap: onOpenTeam,
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                      child: Row(
                        children: [
                          const Icon(Icons.groups_outlined, size: 18, color: AppColors.brandGold),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              rollupLine(m.team!),
                              style: TextStyle(color: context.textPrimary, fontSize: 12.5),
                            ),
                          ),
                          const Icon(Icons.chevron_right, color: AppColors.brandGold),
                        ],
                      ),
                    ),
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
