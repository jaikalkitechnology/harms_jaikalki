import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/sales_api.dart';
import '../data/sales_models.dart';

class SalesPipelinePage extends StatefulWidget {
  const SalesPipelinePage({super.key});

  @override
  State<SalesPipelinePage> createState() => _SalesPipelinePageState();
}

class _SalesPipelinePageState extends State<SalesPipelinePage> {
  late Future<List<PipelineColumn>> _future;

  static const _stageOrder = <String>[
    'new',
    'contacted',
    'qualified',
    'proposal',
    'negotiation',
    'won',
  ];

  static const _stageColors = <String, Color>{
    'new': AppColors.info,
    'contacted': AppColors.brandGoldDark,
    'qualified': AppColors.brandGold,
    'proposal': AppColors.warning,
    'negotiation': AppColors.warning,
    'won': AppColors.success,
    'lost': AppColors.error,
  };

  @override
  void initState() {
    super.initState();
    _future = sl<SalesApi>().myPipeline();
  }

  Future<void> _refresh() async {
    setState(() {
      _future = sl<SalesApi>().myPipeline();
    });
    await _future;
  }

  String? _nextStage(String s) {
    final idx = _stageOrder.indexOf(s);
    if (idx < 0 || idx >= _stageOrder.length - 1) return null;
    return _stageOrder[idx + 1];
  }

  String? _prevStage(String s) {
    final idx = _stageOrder.indexOf(s);
    if (idx <= 0) return null;
    return _stageOrder[idx - 1];
  }

  Future<void> _move(Lead lead, String target) async {
    // Prompt before submitting a "won" request so the rep knows it
    // needs admin approval.
    if (target == 'won' && lead.wonApprovalStatus != 'pending') {
      final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Submit for admin approval?'),
          content: const Text(
            'Marking this lead as Won will send it to admin for approval. '
            'It will only count toward your target after approval.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Submit for approval'),
            ),
          ],
        ),
      );
      if (ok != true) return;
    }
    try {
      await sl<SalesApi>().updateStage(lead.id, target);
      if (mounted) {
        final msg = target == 'won'
            ? 'Submitted for admin approval'
            : 'Moved to $target';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(msg),
            backgroundColor: AppColors.success,
          ),
        );
      }
      await _refresh();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Could not update stage'),
            backgroundColor: AppColors.error,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Sales Pipeline'),
        actions: [
          IconButton(
            tooltip: 'My leads',
            icon: const Icon(Icons.list_alt),
            onPressed: () => context.push('/sales/leads'),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _refresh,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<PipelineColumn>>(
          future: _future,
          builder: (context, snap) {
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final cols = snap.data!.where((c) => c.count > 0).toList();
            if (cols.isEmpty) {
              return ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  const SizedBox(height: 80),
                  Icon(Icons.trending_up,
                      size: 64, color: AppColors.brandGoldDark),
                  const SizedBox(height: 16),
                  Center(
                    child: Text(
                      'No active leads in your pipeline.',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: AppColors.brandBrownLight,
                      ),
                    ),
                  ),
                ],
              );
            }
            return ListView(
              padding: const EdgeInsets.all(16),
              children: cols.map((col) {
                final color =
                    _stageColors[col.stage] ?? AppColors.brandGoldDark;
                return Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: color.withOpacity(0.15),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              col.stage.toUpperCase(),
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: color,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Text(
                            '${col.count} · ₹${col.totalValue.toStringAsFixed(0)}',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: AppColors.brandBrownLight,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                      ...col.leads.map(
                        (ld) => _LeadCard(
                          lead: ld,
                          prev: _prevStage(ld.stage),
                          next: _nextStage(ld.stage),
                          onMove: (tgt) => _move(ld, tgt),
                        ),
                      ),
                    ],
                  ),
                );
              }).toList(),
            );
          },
        ),
      ),
    );
  }
}

class _LeadCard extends StatelessWidget {
  const _LeadCard({
    required this.lead,
    required this.prev,
    required this.next,
    required this.onMove,
  });

  final Lead lead;
  final String? prev;
  final String? next;
  final void Function(String stage) onMove;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final wonBadge = _WonBadge.forLead(lead);

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Text(
                    lead.contactName ?? 'Lead #${lead.id}',
                    style: theme.textTheme.titleSmall,
                  ),
                ),
                if (wonBadge != null) wonBadge,
              ],
            ),
            if (lead.contactPhone != null)
              Text(
                lead.contactPhone!,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: AppColors.brandBrownLight,
                ),
              ),
            const SizedBox(height: 4),
            Text(
              '₹${lead.expectedValue.toStringAsFixed(0)} · score ${lead.score}',
              style: theme.textTheme.bodySmall,
            ),
            if (lead.nextAction != null) ...[
              const SizedBox(height: 4),
              Text(
                '→ ${lead.nextAction}',
                style: theme.textTheme.bodySmall?.copyWith(
                  fontStyle: FontStyle.italic,
                  color: AppColors.brandBrownLight,
                ),
              ),
            ],
            if (lead.wonApprovalStatus == 'rejected' &&
                lead.wonRejectionReason != null) ...[
              const SizedBox(height: 6),
              Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 8, vertical: 6),
                decoration: BoxDecoration(
                  color: AppColors.errorLight,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  'Admin rejected: ${lead.wonRejectionReason}',
                  style: theme.textTheme.bodySmall
                      ?.copyWith(color: AppColors.error),
                ),
              ),
            ],
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                if (prev != null)
                  TextButton.icon(
                    icon: const Icon(Icons.arrow_back, size: 14),
                    label: Text('Back to $prev'),
                    onPressed: () => onMove(prev!),
                  )
                else
                  const SizedBox.shrink(),
                if (next != null && lead.wonApprovalStatus != 'pending')
                  TextButton.icon(
                    icon: const Icon(Icons.arrow_forward, size: 14),
                    label: Text(next == 'won'
                        ? 'Submit for Won'
                        : 'Advance to $next'),
                    onPressed: () => onMove(next!),
                  )
                else
                  const SizedBox.shrink(),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _WonBadge extends StatelessWidget {
  const _WonBadge({
    required this.label,
    required this.color,
    required this.icon,
  });

  final String label;
  final Color color;
  final IconData icon;

  static Widget? forLead(Lead lead) {
    if (lead.stage != 'won') return null;
    final status = lead.wonApprovalStatus;
    if (status == 'pending') {
      return const _WonBadge(
        label: 'Pending from admin',
        color: AppColors.warning,
        icon: Icons.hourglass_top,
      );
    }
    if (status == 'rejected') {
      return const _WonBadge(
        label: 'Rejected by admin',
        color: AppColors.error,
        icon: Icons.cancel,
      );
    }
    // approved or legacy null → solid green Won.
    return const _WonBadge(
      label: 'Won',
      color: AppColors.success,
      icon: Icons.check_circle,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.4)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 14),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              color: color,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
