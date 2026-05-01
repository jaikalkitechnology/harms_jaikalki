import 'package:flutter/material.dart';

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
    const order = [
      'new',
      'contacted',
      'qualified',
      'proposal',
      'negotiation',
      'won',
    ];
    final idx = order.indexOf(s);
    if (idx < 0 || idx >= order.length - 1) return null;
    return order[idx + 1];
  }

  Future<void> _advance(Lead lead) async {
    final next = _nextStage(lead.stage);
    if (next == null) return;
    try {
      await sl<SalesApi>().updateStage(lead.id, next);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Moved to $next'),
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
                        (ld) => Card(
                          margin: const EdgeInsets.only(bottom: 8),
                          child: Padding(
                            padding: const EdgeInsets.all(12),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  ld.contactName ?? 'Lead #${ld.id}',
                                  style: theme.textTheme.titleSmall,
                                ),
                                if (ld.contactPhone != null)
                                  Text(
                                    ld.contactPhone!,
                                    style: theme.textTheme.bodySmall?.copyWith(
                                      color: AppColors.brandBrownLight,
                                    ),
                                  ),
                                const SizedBox(height: 4),
                                Text(
                                  '₹${ld.expectedValue.toStringAsFixed(0)} · score ${ld.score}',
                                  style: theme.textTheme.bodySmall,
                                ),
                                if (ld.nextAction != null) ...[
                                  const SizedBox(height: 4),
                                  Text(
                                    '→ ${ld.nextAction}',
                                    style: theme.textTheme.bodySmall?.copyWith(
                                      fontStyle: FontStyle.italic,
                                      color: AppColors.brandBrownLight,
                                    ),
                                  ),
                                ],
                                if (_nextStage(ld.stage) != null) ...[
                                  const SizedBox(height: 8),
                                  Align(
                                    alignment: Alignment.centerRight,
                                    child: TextButton.icon(
                                      icon: const Icon(Icons.arrow_forward,
                                          size: 14),
                                      label: Text(
                                          'Advance to ${_nextStage(ld.stage)}'),
                                      onPressed: () => _advance(ld),
                                    ),
                                  ),
                                ],
                              ],
                            ),
                          ),
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
