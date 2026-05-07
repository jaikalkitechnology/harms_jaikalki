import 'package:flutter/material.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/sales_api.dart';
import '../data/sales_models.dart';

class SalesTargetsPage extends StatefulWidget {
  const SalesTargetsPage({super.key});

  @override
  State<SalesTargetsPage> createState() => _SalesTargetsPageState();
}

class _SalesTargetsPageState extends State<SalesTargetsPage> {
  late Future<_ProgressReport> _future;
  bool _refreshing = false;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<_ProgressReport> _load() async {
    final api = sl<SalesApi>();
    final summary = await api.myTarget();
    final pipeline = await api.myPipeline();
    return _ProgressReport(summary: summary, pipeline: pipeline);
  }

  Future<void> _pullRefresh() async {
    setState(() => _future = _load());
    await _future;
  }

  Future<void> _recompute(int targetId) async {
    setState(() => _refreshing = true);
    try {
      await sl<SalesApi>().refreshTarget(targetId);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Progress refreshed from pipeline')),
      );
      setState(() => _future = _load());
      await _future;
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Could not refresh progress')),
      );
    } finally {
      if (mounted) setState(() => _refreshing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Progress Report'),
        actions: [
          IconButton(
            tooltip: 'Refresh from pipeline',
            icon: _refreshing
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.refresh),
            onPressed: _refreshing
                ? null
                : () async {
                    final r = await _future;
                    if (r.summary != null) {
                      await _recompute(r.summary!.target.id);
                    } else {
                      await _pullRefresh();
                    }
                  },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _pullRefresh,
        child: FutureBuilder<_ProgressReport>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snap.hasError) {
              return ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  const SizedBox(height: 60),
                  Center(
                    child: Text(
                      'Could not load progress.\nPull to retry.',
                      textAlign: TextAlign.center,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: AppColors.brandBrownLight,
                      ),
                    ),
                  ),
                ],
              );
            }
            final report = snap.data!;
            final summary = report.summary;
            final pipeline = report.pipeline;

            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                if (summary != null) ...[
                  _TargetCard(summary: summary),
                  const SizedBox(height: 16),
                  _CommissionCard(summary: summary),
                  const SizedBox(height: 16),
                ] else
                  _NoTargetCard(),
                _PipelineBreakdown(pipeline: pipeline),
                const SizedBox(height: 24),
                Text(
                  'Tip: tap the refresh icon at the top to pull the latest '
                  'achievement directly from your pipeline (orders + won leads).',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: AppColors.brandBrownLight,
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _ProgressReport {
  _ProgressReport({required this.summary, required this.pipeline});
  final TargetSummary? summary;
  final List<PipelineColumn> pipeline;
}

class _TargetCard extends StatelessWidget {
  const _TargetCard({required this.summary});
  final TargetSummary summary;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final pct = summary.achievementPct;
    final achColor = pct >= 100
        ? AppColors.success
        : pct >= 70
            ? AppColors.brandGoldDark
            : AppColors.info;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              summary.target.periodType.toUpperCase(),
              style: theme.textTheme.labelSmall?.copyWith(
                color: AppColors.brandGoldDark,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              '${summary.target.periodStart} → ${summary.target.periodEnd}',
              style: theme.textTheme.bodySmall?.copyWith(
                color: AppColors.brandBrownLight,
              ),
            ),
            const SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Target', style: theme.textTheme.bodySmall),
                    Text(
                      '₹${summary.target.targetAmount.toStringAsFixed(0)}',
                      style: theme.textTheme.titleLarge,
                    ),
                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text('Achieved', style: theme.textTheme.bodySmall),
                    Text(
                      '₹${summary.target.achievedAmount.toStringAsFixed(0)}',
                      style: theme.textTheme.titleLarge?.copyWith(
                        color: achColor,
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 16),
            ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: LinearProgressIndicator(
                value: (pct / 100).clamp(0.0, 1.0),
                minHeight: 12,
                backgroundColor: AppColors.brandBrown50,
                valueColor: AlwaysStoppedAnimation(achColor),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  '${pct.toStringAsFixed(1)}% achieved',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: AppColors.brandBrownLight,
                  ),
                ),
                Text(
                  pct >= 100
                      ? 'Target met '
                      : '₹${(summary.target.targetAmount - summary.target.achievedAmount).toStringAsFixed(0)} to go',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: pct >= 100 ? AppColors.success : AppColors.brandBrownLight,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _CommissionCard extends StatelessWidget {
  const _CommissionCard({required this.summary});
  final TargetSummary summary;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      color: AppColors.brandGoldPale,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(Icons.attach_money,
                color: AppColors.brandGoldDark, size: 36),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Commission accrued',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: AppColors.brandBrownLight,
                      )),
                  Text(
                    '₹${summary.commissionAmount.toStringAsFixed(2)}',
                    style: theme.textTheme.headlineSmall?.copyWith(
                      color: AppColors.brandGoldDark,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  Text(
                    'at ${summary.target.commissionPct}% of achievement',
                    style: theme.textTheme.bodySmall,
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

class _NoTargetCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            Icon(Icons.flag_outlined,
                size: 48, color: AppColors.brandGoldDark),
            const SizedBox(height: 12),
            Text(
              'No active sales target',
              style: theme.textTheme.titleMedium,
            ),
            const SizedBox(height: 4),
            Text(
              'Ask your manager to set one. Your pipeline progress is shown below.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodySmall?.copyWith(
                color: AppColors.brandBrownLight,
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

class _PipelineBreakdown extends StatelessWidget {
  const _PipelineBreakdown({required this.pipeline});
  final List<PipelineColumn> pipeline;

  static const _stageOrder = [
    'new',
    'contacted',
    'qualified',
    'proposal',
    'negotiation',
    'won',
    'lost',
  ];

  static const _stageLabel = {
    'new': 'New',
    'contacted': 'Contacted',
    'qualified': 'Qualified',
    'proposal': 'Proposal',
    'negotiation': 'Negotiation',
    'won': 'Won',
    'lost': 'Lost',
  };

  Color _stageColor(String stage) {
    switch (stage) {
      case 'won':
        return AppColors.success;
      case 'lost':
        return AppColors.error;
      case 'negotiation':
      case 'proposal':
        return AppColors.brandGoldDark;
      case 'qualified':
        return AppColors.info;
      default:
        return AppColors.brandBrownLight;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final byStage = {for (final c in pipeline) c.stage: c};
    final ordered = _stageOrder
        .where((s) => byStage.containsKey(s))
        .map((s) => byStage[s]!)
        .toList();

    final totalLeads = pipeline.fold<int>(0, (a, c) => a + c.count);
    final totalValue =
        pipeline.fold<double>(0, (a, c) => a + c.totalValue);
    final won = byStage['won'];

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.insights,
                    color: AppColors.brandGoldDark, size: 22),
                const SizedBox(width: 8),
                Text(
                  'My Pipeline',
                  style: theme.textTheme.titleMedium,
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              '$totalLeads lead${totalLeads == 1 ? "" : "s"} · '
              '₹${totalValue.toStringAsFixed(0)} total expected value',
              style: theme.textTheme.bodySmall?.copyWith(
                color: AppColors.brandBrownLight,
              ),
            ),
            const SizedBox(height: 12),
            if (won != null && won.count > 0) ...[
              Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 12, vertical: 10),
                decoration: BoxDecoration(
                  color: AppColors.success.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Icon(Icons.check_circle,
                        color: AppColors.success, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        '${won.count} won lead${won.count == 1 ? "" : "s"} · '
                        '₹${won.totalValue.toStringAsFixed(0)} contributing to your achievement',
                        style: theme.textTheme.bodySmall,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
            ],
            if (ordered.isEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 12),
                child: Text(
                  'No leads in your pipeline yet.',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: AppColors.brandBrownLight,
                  ),
                ),
              )
            else
              ...ordered.map((col) => _PipelineRow(
                    label: _stageLabel[col.stage] ?? col.stage,
                    count: col.count,
                    value: col.totalValue,
                    color: _stageColor(col.stage),
                    maxValue:
                        ordered.fold<double>(0, (a, c) => c.totalValue > a ? c.totalValue : a),
                  )),
          ],
        ),
      ),
    );
  }
}

class _PipelineRow extends StatelessWidget {
  const _PipelineRow({
    required this.label,
    required this.count,
    required this.value,
    required this.color,
    required this.maxValue,
  });

  final String label;
  final int count;
  final double value;
  final Color color;
  final double maxValue;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final ratio = maxValue > 0 ? (value / maxValue).clamp(0.0, 1.0) : 0.0;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: color,
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(label, style: theme.textTheme.bodyMedium),
                  const SizedBox(width: 6),
                  Text(
                    '· $count',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: AppColors.brandBrownLight,
                    ),
                  ),
                ],
              ),
              Text(
                '₹${value.toStringAsFixed(0)}',
                style: theme.textTheme.bodySmall?.copyWith(
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: ratio.toDouble(),
              minHeight: 6,
              backgroundColor: AppColors.brandBrown50,
              valueColor: AlwaysStoppedAnimation(color),
            ),
          ),
        ],
      ),
    );
  }
}
