import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/verification_api.dart';
import '../data/verification_models.dart';

class VerificationQueuePage extends StatefulWidget {
  const VerificationQueuePage({super.key});

  @override
  State<VerificationQueuePage> createState() => _VerificationQueuePageState();
}

class _VerificationQueuePageState extends State<VerificationQueuePage> {
  late Future<List<VerificationJob>> _future;

  @override
  void initState() {
    super.initState();
    _future = sl<VerificationApi>().myQueue();
  }

  Future<void> _refresh() async {
    setState(() {
      _future = sl<VerificationApi>().myQueue();
    });
    await _future;
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'completed':
      case 'audit_passed':
        return AppColors.success;
      case 'in_progress':
        return AppColors.info;
      case 'audit_pending':
      case 'submitted':
        return AppColors.warning;
      case 'audit_failed':
      case 'cancelled':
        return AppColors.error;
      default:
        return AppColors.brandGoldDark;
    }
  }

  bool _isOverdue(String? deadlineIso) {
    if (deadlineIso == null) return false;
    final dl = DateTime.tryParse(deadlineIso);
    if (dl == null) return false;
    return DateTime.now().isAfter(dl);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Verifications')),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<VerificationJob>>(
          future: _future,
          builder: (context, snap) {
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final jobs = snap.data!;
            if (jobs.isEmpty) {
              return ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  const SizedBox(height: 80),
                  Icon(Icons.fact_check_outlined,
                      size: 64, color: AppColors.brandGoldDark),
                  const SizedBox(height: 16),
                  Center(
                    child: Text(
                      'No verifications assigned to you.',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: AppColors.brandBrownLight,
                      ),
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
                final overdue = _isOverdue(j.deadlineAt);
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: InkWell(
                    onTap: () => context.push('/verification/${j.id}'),
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
                                  j.subjectName,
                                  style: theme.textTheme.titleMedium,
                                ),
                              ),
                              if (j.fraudFlagsCount > 0)
                                Padding(
                                  padding: const EdgeInsets.only(right: 8),
                                  child: Row(
                                    children: [
                                      Icon(Icons.warning_amber,
                                          color: AppColors.error, size: 16),
                                      Text(
                                        '${j.fraudFlagsCount}',
                                        style: TextStyle(
                                          color: AppColors.error,
                                          fontSize: 12,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 8, vertical: 4),
                                decoration: BoxDecoration(
                                  color: _statusColor(j.status)
                                      .withOpacity(0.15),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  j.status.replaceAll('_', ' ').toUpperCase(),
                                  style: TextStyle(
                                    fontSize: 10,
                                    fontWeight: FontWeight.bold,
                                    color: _statusColor(j.status),
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Text(
                            '${j.ticketNumber} · ${j.type}',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: AppColors.brandBrownLight,
                            ),
                          ),
                          if (j.address != null) ...[
                            const SizedBox(height: 6),
                            Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Icon(Icons.location_on,
                                    size: 14,
                                    color: AppColors.brandBrownLight),
                                const SizedBox(width: 4),
                                Expanded(
                                  child: Text(
                                    j.address!,
                                    style: theme.textTheme.bodySmall,
                                  ),
                                ),
                              ],
                            ),
                          ],
                          if (j.deadlineAt != null) ...[
                            const SizedBox(height: 6),
                            Row(
                              children: [
                                Icon(Icons.schedule,
                                    size: 14,
                                    color: overdue
                                        ? AppColors.error
                                        : AppColors.brandBrownLight),
                                const SizedBox(width: 4),
                                Text(
                                  overdue
                                      ? 'OVERDUE · ${j.deadlineAt}'
                                      : 'Due ${j.deadlineAt}',
                                  style: theme.textTheme.bodySmall?.copyWith(
                                    color: overdue
                                        ? AppColors.error
                                        : AppColors.brandBrownLight,
                                    fontWeight: overdue
                                        ? FontWeight.bold
                                        : FontWeight.normal,
                                  ),
                                ),
                              ],
                            ),
                          ],
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
