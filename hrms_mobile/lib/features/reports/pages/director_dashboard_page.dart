import 'package:flutter/material.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/reports_api.dart';
import '../data/reports_models.dart';

class DirectorDashboardPage extends StatefulWidget {
  const DirectorDashboardPage({super.key});

  @override
  State<DirectorDashboardPage> createState() => _DirectorDashboardPageState();
}

class _DirectorDashboardPageState extends State<DirectorDashboardPage> {
  late Future<DirectorDashboard> _future;

  @override
  void initState() {
    super.initState();
    _future = sl<ReportsApi>().directorDashboard();
  }

  Future<void> _refresh() async {
    setState(() => _future = sl<ReportsApi>().directorDashboard());
    await _future;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _refresh,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<DirectorDashboard>(
          future: _future,
          builder: (context, snap) {
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final d = snap.data!;
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _kpiRow(d, theme),
                const SizedBox(height: 16),
                _Section(title: '★ HEADCOUNT TREND'),
                const SizedBox(height: 8),
                _HeadcountSparkline(points: d.headcount.points),
                const SizedBox(height: 16),
                _Section(title: '★ DEPARTMENTS'),
                const SizedBox(height: 8),
                _DeptBars(rows: d.departmentBreakdown),
                const SizedBox(height: 16),
                _Section(title: '★ COMPLIANCE'),
                const SizedBox(height: 8),
                _ComplianceCard(c: d.compliance),
                const SizedBox(height: 16),
                _Section(title: '★ OPS SUMMARY'),
                const SizedBox(height: 8),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      children: [
                        if (d.sales != null) ...[
                          _SummaryRow(
                            label: 'Sales leads (90d)',
                            value: '${d.sales!.leadsCount}',
                          ),
                          _SummaryRow(
                            label: 'Win rate',
                            value:
                                '${d.sales!.winRatePct.toStringAsFixed(1)}%',
                          ),
                          _SummaryRow(
                            label: 'Orders booked',
                            value:
                                '₹${d.sales!.ordersTotal.toStringAsFixed(0)}',
                          ),
                          const Divider(),
                        ],
                        _SummaryRow(
                          label: 'Verifications',
                          value:
                              '${d.verification.completed}/${d.verification.total}',
                        ),
                        _SummaryRow(
                          label: 'Avg TAT',
                          value: '${d.verification.avgHours} h',
                        ),
                        _SummaryRow(
                          label: 'Breach',
                          value: '${d.verification.breachPct}%',
                          color: d.verification.breachPct > 10
                              ? AppColors.error
                              : AppColors.success,
                        ),
                        const Divider(),
                        _SummaryRow(
                          label: 'Training sessions',
                          value:
                              '${d.training.sessionsCompleted}/${d.training.sessionsTotal} done',
                        ),
                        _SummaryRow(
                          label: 'Upcoming',
                          value: '${d.training.upcomingSessions}',
                        ),
                        _SummaryRow(
                          label: 'Trained attendees',
                          value: '${d.training.totalAttendees}',
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

  Widget _kpiRow(DirectorDashboard d, ThemeData theme) {
    return GridView.count(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisCount: 2,
      childAspectRatio: 1.6,
      crossAxisSpacing: 8,
      mainAxisSpacing: 8,
      children: [
        _KpiCard(
          label: 'Headcount',
          value: '${d.headcount.currentHeadcount}',
        ),
        _KpiCard(
          label: '12m attrition',
          value: '${d.attrition.attritionPct}%',
          color: d.attrition.attritionPct > 15
              ? AppColors.error
              : AppColors.success,
        ),
        _KpiCard(
          label: 'Compliance',
          value: '${d.compliance.coveragePct.toStringAsFixed(0)}%',
          color: d.compliance.coveragePct >= 90
              ? AppColors.success
              : AppColors.warning,
        ),
        _KpiCard(
          label: 'Verif. breach',
          value: '${d.verification.breachPct.toStringAsFixed(0)}%',
          color: d.verification.breachPct > 10
              ? AppColors.error
              : AppColors.success,
        ),
      ],
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({required this.title});
  final String title;

  @override
  Widget build(BuildContext context) {
    return Text(
      title,
      style: Theme.of(context).textTheme.labelSmall?.copyWith(
            color: AppColors.brandGoldDark,
          ),
    );
  }
}

class _KpiCard extends StatelessWidget {
  const _KpiCard({required this.label, required this.value, this.color});
  final String label;
  final String value;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label.toUpperCase(),
              style: theme.textTheme.labelSmall?.copyWith(
                color: AppColors.textMuted,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              value,
              style: theme.textTheme.headlineSmall?.copyWith(
                color: color ?? context.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _HeadcountSparkline extends StatelessWidget {
  const _HeadcountSparkline({required this.points});
  final List<HeadcountPoint> points;

  @override
  Widget build(BuildContext context) {
    if (points.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Center(child: Text('No data')),
        ),
      );
    }
    final maxValue = points
        .map((p) => p.headcount)
        .fold<int>(0, (a, b) => a > b ? a : b)
        .clamp(1, 1 << 31);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            SizedBox(
              height: 90,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: points
                    .map(
                      (p) => Expanded(
                        child: Padding(
                          padding:
                              const EdgeInsets.symmetric(horizontal: 1.5),
                          child: Container(
                            height: (p.headcount / maxValue) * 80 + 4,
                            decoration: BoxDecoration(
                              color: AppColors.brandGoldDark,
                              borderRadius: BorderRadius.circular(2),
                            ),
                          ),
                        ),
                      ),
                    )
                    .toList(),
              ),
            ),
            const SizedBox(height: 4),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  points.first.period,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                Text(
                  points.last.period,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _DeptBars extends StatelessWidget {
  const _DeptBars({required this.rows});
  final List<DepartmentBreakdown> rows;

  @override
  Widget build(BuildContext context) {
    if (rows.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Center(child: Text('No data')),
        ),
      );
    }
    final maxValue = rows
        .map((r) => r.headcount)
        .fold<int>(0, (a, b) => a > b ? a : b)
        .clamp(1, 1 << 31);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: rows.map((r) {
            final width = (r.headcount / maxValue);
            return Padding(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(r.department,
                          style: Theme.of(context).textTheme.bodySmall),
                      Text('${r.headcount}',
                          style: Theme.of(context).textTheme.bodySmall),
                    ],
                  ),
                  const SizedBox(height: 4),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(4),
                    child: LinearProgressIndicator(
                      value: width,
                      minHeight: 8,
                      backgroundColor: AppColors.brandBrown50,
                      valueColor: const AlwaysStoppedAnimation(
                          AppColors.brandGoldDark),
                    ),
                  ),
                ],
              ),
            );
          }).toList(),
        ),
      ),
    );
  }
}

class _ComplianceCard extends StatelessWidget {
  const _ComplianceCard({required this.c});
  final ComplianceStats c;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: AppColors.brandGoldPale,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${c.coveragePct.toStringAsFixed(1)}% fully compliant',
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: AppColors.brandGoldDark,
                  ),
            ),
            const SizedBox(height: 6),
            Text(
              '${c.mandatoryCourses} mandatory course(s) · '
              '${c.employeesTotal} active employees',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 12),
            _StackedBar(
              full: c.fullyCompliant,
              partial: c.partiallyCompliant,
              none: c.nonCompliant,
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 12,
              children: [
                _LegendDot(color: AppColors.success, label: 'Full ${c.fullyCompliant}'),
                _LegendDot(
                    color: AppColors.brandGoldDark,
                    label: 'Partial ${c.partiallyCompliant}'),
                _LegendDot(
                    color: AppColors.error, label: 'None ${c.nonCompliant}'),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _StackedBar extends StatelessWidget {
  const _StackedBar({
    required this.full,
    required this.partial,
    required this.none,
  });
  final int full;
  final int partial;
  final int none;

  @override
  Widget build(BuildContext context) {
    final total = (full + partial + none).clamp(1, 1 << 31);
    return ClipRRect(
      borderRadius: BorderRadius.circular(6),
      child: SizedBox(
        height: 14,
        child: Row(
          children: [
            if (full > 0)
              Expanded(
                flex: full,
                child: Container(color: AppColors.success),
              ),
            if (partial > 0)
              Expanded(
                flex: partial,
                child: Container(color: AppColors.brandGoldDark),
              ),
            if (none > 0)
              Expanded(
                flex: none,
                child: Container(color: AppColors.error),
              ),
            // total guard so the row never becomes empty when no data
            if (total == 0)
              Expanded(
                flex: 1,
                child: Container(color: AppColors.brandBrown50),
              ),
          ],
        ),
      ),
    );
  }
}

class _LegendDot extends StatelessWidget {
  const _LegendDot({required this.color, required this.label});
  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        Text(label, style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }
}

class _SummaryRow extends StatelessWidget {
  const _SummaryRow({required this.label, required this.value, this.color});
  final String label;
  final String value;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Expanded(
            child: Text(label,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: AppColors.textMuted,
                    )),
          ),
          Text(
            value,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
          ),
        ],
      ),
    );
  }
}
