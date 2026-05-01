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
  late Future<TargetSummary?> _future;

  @override
  void initState() {
    super.initState();
    _future = sl<SalesApi>().myTarget();
  }

  Future<void> _refresh() async {
    setState(() {
      _future = sl<SalesApi>().myTarget();
    });
    await _future;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('My Targets')),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<TargetSummary?>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState != ConnectionState.done) {
              return const Center(child: CircularProgressIndicator());
            }
            final summary = snap.data;
            if (summary == null) {
              return ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  const SizedBox(height: 80),
                  Icon(Icons.flag_outlined,
                      size: 64, color: AppColors.brandGoldDark),
                  const SizedBox(height: 16),
                  Center(
                    child: Text(
                      'No active sales target.\nAsk your manager to set one.',
                      textAlign: TextAlign.center,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: AppColors.brandBrownLight,
                      ),
                    ),
                  ),
                ],
              );
            }

            final pct = summary.achievementPct;
            final achColor = pct >= 100
                ? AppColors.success
                : pct >= 70
                    ? AppColors.brandGoldDark
                    : AppColors.info;

            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Card(
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
                                Text('Target',
                                    style: theme.textTheme.bodySmall),
                                Text(
                                  '₹${summary.target.targetAmount.toStringAsFixed(0)}',
                                  style: theme.textTheme.titleLarge,
                                ),
                              ],
                            ),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text('Achieved',
                                    style: theme.textTheme.bodySmall),
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
                        Text(
                          '${pct.toStringAsFixed(1)}% achieved',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: AppColors.brandBrownLight,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Card(
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
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}
