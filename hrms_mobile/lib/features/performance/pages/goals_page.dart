import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/performance_api.dart';
import '../data/performance_models.dart';

class MyGoalsPage extends StatefulWidget {
  const MyGoalsPage({super.key});

  @override
  State<MyGoalsPage> createState() => _MyGoalsPageState();
}

class _MyGoalsPageState extends State<MyGoalsPage> {
  late Future<List<Goal>> _future;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _future = sl<PerformanceApi>().myGoals();
  }

  Future<void> _refresh() async {
    setState(() => _future = sl<PerformanceApi>().myGoals());
    await _future;
  }

  Color _statusColor(String s) {
    switch (s) {
      case 'achieved':
        return AppColors.success;
      case 'at_risk':
        return AppColors.warning;
      case 'missed':
      case 'cancelled':
        return AppColors.error;
      default:
        return AppColors.info;
    }
  }

  Future<void> _adjustProgress(Goal g, int delta) async {
    final next = (g.progressPct + delta).clamp(0, 100);
    if (next == g.progressPct) return;
    setState(() => _busy = true);
    try {
      await sl<PerformanceApi>().updateGoal(
        goalId: g.id,
        progressPct: next,
      );
      await _refresh();
    } on DioException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              e.response?.data is Map
                  ? (e.response!.data['detail']?.toString() ?? 'Failed')
                  : 'Failed',
            ),
            backgroundColor: AppColors.error,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('My Goals')),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<Goal>>(
          future: _future,
          builder: (context, snap) {
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final goals = snap.data!;
            if (goals.isEmpty) {
              return ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  const SizedBox(height: 80),
                  Icon(Icons.flag_outlined,
                      size: 64, color: AppColors.brandGoldDark),
                  const SizedBox(height: 12),
                  Center(
                    child: Text('No goals yet for this cycle.',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: AppColors.brandBrownLight,
                        )),
                  ),
                ],
              );
            }
            final overall = goals.isEmpty
                ? 0
                : (goals
                            .map((g) =>
                                g.weightPct * g.progressPct ~/ 100)
                            .fold(0, (a, b) => a + b) ~/
                        1)
                    .clamp(0, 100);
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Card(
                  color: AppColors.brandGoldPale,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Overall progress',
                            style: theme.textTheme.labelMedium),
                        const SizedBox(height: 8),
                        ClipRRect(
                          borderRadius: BorderRadius.circular(6),
                          child: LinearProgressIndicator(
                            value: overall / 100,
                            minHeight: 12,
                            backgroundColor: Colors.white,
                            valueColor: const AlwaysStoppedAnimation(
                                AppColors.brandGoldDark),
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text('$overall% weighted average',
                            style: theme.textTheme.bodySmall),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                ...goals.map(
                  (g) => Card(
                    margin: const EdgeInsets.only(bottom: 12),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(g.title,
                                    style: theme.textTheme.titleMedium),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 8, vertical: 2),
                                decoration: BoxDecoration(
                                  color:
                                      _statusColor(g.status).withOpacity(0.15),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  g.status.replaceAll('_', ' ').toUpperCase(),
                                  style: TextStyle(
                                    fontSize: 10,
                                    fontWeight: FontWeight.bold,
                                    color: _statusColor(g.status),
                                  ),
                                ),
                              ),
                            ],
                          ),
                          if (g.description != null) ...[
                            const SizedBox(height: 4),
                            Text(g.description!,
                                style: theme.textTheme.bodySmall),
                          ],
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: AppColors.brandBrown50,
                                  borderRadius: BorderRadius.circular(4),
                                ),
                                child: Text(
                                  g.category,
                                  style: const TextStyle(fontSize: 10),
                                ),
                              ),
                              const SizedBox(width: 8),
                              Text('Weight ${g.weightPct}%',
                                  style: theme.textTheme.bodySmall),
                              if (g.dueDate != null) ...[
                                const SizedBox(width: 8),
                                Text('Due ${g.dueDate}',
                                    style: theme.textTheme.bodySmall),
                              ],
                            ],
                          ),
                          const SizedBox(height: 12),
                          ClipRRect(
                            borderRadius: BorderRadius.circular(6),
                            child: LinearProgressIndicator(
                              value: g.progressPct / 100,
                              minHeight: 8,
                              backgroundColor: AppColors.brandBrown50,
                              valueColor: AlwaysStoppedAnimation(
                                _statusColor(g.status),
                              ),
                            ),
                          ),
                          const SizedBox(height: 4),
                          Row(
                            children: [
                              Text('${g.progressPct}%',
                                  style: theme.textTheme.bodySmall?.copyWith(
                                      fontWeight: FontWeight.bold)),
                              const Spacer(),
                              IconButton(
                                icon: const Icon(Icons.remove_circle_outline),
                                tooltip: '-10%',
                                onPressed: _busy
                                    ? null
                                    : () => _adjustProgress(g, -10),
                              ),
                              IconButton(
                                icon: const Icon(Icons.add_circle_outline),
                                tooltip: '+10%',
                                onPressed: _busy
                                    ? null
                                    : () => _adjustProgress(g, 10),
                              ),
                            ],
                          ),
                        ],
                      ),
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
