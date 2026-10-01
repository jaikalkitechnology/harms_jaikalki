import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/field_api.dart';
import '../data/field_models.dart';

class FieldHomePage extends StatefulWidget {
  const FieldHomePage({super.key});

  @override
  State<FieldHomePage> createState() => _FieldHomePageState();
}

class _FieldHomePageState extends State<FieldHomePage> {
  late Future<List<FieldJob>> _future;

  @override
  void initState() {
    super.initState();
    _future = sl<FieldApi>().myJobsToday();
  }

  Future<void> _refresh() async {
    setState(() {
      _future = sl<FieldApi>().myJobsToday();
    });
    await _future;
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'completed':
        return AppColors.success;
      case 'in_progress':
        return AppColors.info;
      case 'cancelled':
      case 'skipped':
        return AppColors.error;
      default:
        return AppColors.brandGoldDark;
    }
  }

  Color _priorityColor(String p) {
    switch (p) {
      case 'urgent':
        return AppColors.error;
      case 'high':
        return AppColors.warning;
      case 'low':
        return AppColors.textMuted;
      default:
        return AppColors.info;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text("Today's Field Plan"),
        actions: [
          IconButton(
            icon: const Icon(Icons.map_outlined),
            tooltip: 'Live team map',
            onPressed: () => context.push('/field/live-map'),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<FieldJob>>(
          future: _future,
          builder: (context, snap) {
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final jobs = snap.data!;
            if (jobs.isEmpty) {
              return ListView(
                padding: const EdgeInsets.all(16),
                children: const [
                  SizedBox(height: 80),
                  Icon(Icons.assignment_turned_in,
                      size: 64, color: AppColors.brandGoldDark),
                  SizedBox(height: 16),
                  Center(
                    child: Text(
                      'No jobs scheduled for today.',
                      style: TextStyle(color: AppColors.textMuted),
                    ),
                  ),
                ],
              );
            }
            return ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: jobs.length,
              itemBuilder: (context, i) {
                final j = jobs[i];
                final cust = j.customer;
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: InkWell(
                    onTap: () =>
                        context.push('/field/visit/${j.id}'),
                    borderRadius: BorderRadius.circular(12),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  cust?.name ?? 'Customer #${j.customerId}',
                                  style: theme.textTheme.titleMedium,
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 8,
                                  vertical: 4,
                                ),
                                decoration: BoxDecoration(
                                  color: _priorityColor(j.priority)
                                      .withOpacity(0.15),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  j.priority.toUpperCase(),
                                  style: TextStyle(
                                    fontSize: 10,
                                    fontWeight: FontWeight.bold,
                                    color: _priorityColor(j.priority),
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Row(
                            children: [
                              Icon(Icons.work_outline,
                                  size: 14,
                                  color: AppColors.textMuted),
                              const SizedBox(width: 4),
                              Text(
                                j.jobType.replaceAll('_', ' '),
                                style: theme.textTheme.bodySmall,
                              ),
                              if (j.scheduledTime != null) ...[
                                const SizedBox(width: 12),
                                Icon(Icons.access_time,
                                    size: 14,
                                    color: AppColors.textMuted),
                                const SizedBox(width: 4),
                                Text(j.scheduledTime!,
                                    style: theme.textTheme.bodySmall),
                              ],
                            ],
                          ),
                          if (cust?.address != null) ...[
                            const SizedBox(height: 6),
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Icon(Icons.location_on,
                                    size: 14,
                                    color: AppColors.textMuted),
                                const SizedBox(width: 4),
                                Expanded(
                                  child: Text(
                                    cust!.address!,
                                    style: theme.textTheme.bodySmall?.copyWith(
                                      color: AppColors.textMuted,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ],
                          const SizedBox(height: 12),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 4,
                            ),
                            decoration: BoxDecoration(
                              color:
                                  _statusColor(j.status).withOpacity(0.12),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              j.status.replaceAll('_', ' ').toUpperCase(),
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: _statusColor(j.status),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }
}
