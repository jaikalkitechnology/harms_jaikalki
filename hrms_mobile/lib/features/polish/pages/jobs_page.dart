import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/polish_api.dart';
import '../data/polish_models.dart';

class JobsPage extends StatefulWidget {
  const JobsPage({super.key});

  @override
  State<JobsPage> createState() => _JobsPageState();
}

class _JobsPageState extends State<JobsPage> {
  late Future<({List<JobPosting> jobs, List<JobApplication> mine})> _future;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<({List<JobPosting> jobs, List<JobApplication> mine})> _load() async {
    final api = sl<PolishApi>();
    final jobs = await api.publishedJobs();
    final mine = await api.myApplications();
    return (jobs: jobs, mine: mine);
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  void _toast(String msg, {bool error = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: error ? AppColors.error : AppColors.success,
      ),
    );
  }

  Future<void> _apply(JobPosting job) async {
    final note = await showDialog<String>(
      context: context,
      builder: (_) {
        final ctrl = TextEditingController();
        return AlertDialog(
          title: Text('Apply: ${job.title}'),
          content: TextField(
            controller: ctrl,
            maxLines: 4,
            decoration: const InputDecoration(
              labelText: 'Cover note (optional)',
              border: OutlineInputBorder(),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () => Navigator.pop(context, ctrl.text.trim()),
              child: const Text('Apply'),
            ),
          ],
        );
      },
    );
    if (note == null) return;
    setState(() => _busy = true);
    try {
      await sl<PolishApi>().applyToJob(
        postingId: job.id,
        coverNote: note.isEmpty ? null : note,
      );
      _toast('Application submitted');
      await _refresh();
    } on DioException catch (e) {
      final msg = e.response?.data is Map
          ? (e.response!.data['detail']?.toString() ?? 'Apply failed')
          : 'Apply failed';
      _toast(msg, error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Internal Jobs')),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<({List<JobPosting> jobs, List<JobApplication> mine})>(
          future: _future,
          builder: (context, snap) {
            if (snap.connectionState == ConnectionState.waiting) {
              return const Center(child: CircularProgressIndicator());
            }
            if (snap.hasError || !snap.hasData) {
              return ListView(
                children: [
                  const SizedBox(height: 140),
                  Center(
                    child: Text(
                      'Could not load jobs.\nPull down to retry.',
                      textAlign: TextAlign.center,
                      style: theme.textTheme.bodyMedium
                          ?.copyWith(color: context.textMuted),
                    ),
                  ),
                ],
              );
            }
            final jobs = snap.data!.jobs;
            final appliedIds =
                snap.data!.mine.map((a) => a.postingId).toSet();
            if (jobs.isEmpty) {
              return Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Text(
                    'No open positions right now.',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: context.textMuted,
                    ),
                  ),
                ),
              );
            }
            return ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: jobs.length,
              itemBuilder: (context, i) {
                final j = jobs[i];
                final applied = appliedIds.contains(j.id);
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(j.title, style: theme.textTheme.titleMedium),
                        const SizedBox(height: 4),
                        Text(
                          '${j.code} · ${j.employmentType.replaceAll("_", " ")}'
                          '${j.location != null ? " · ${j.location}" : ""}',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: context.textMuted,
                          ),
                        ),
                        if (j.description != null) ...[
                          const SizedBox(height: 8),
                          Text(j.description!,
                              style: theme.textTheme.bodySmall),
                        ],
                        if (j.referralBonus != null) ...[
                          const SizedBox(height: 6),
                          Row(
                            children: [
                              Icon(Icons.card_giftcard,
                                  size: 14, color: AppColors.brandGoldDark),
                              const SizedBox(width: 4),
                              Text(
                                'Referral bonus ₹${j.referralBonus!.toStringAsFixed(0)}',
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: AppColors.brandGoldDark,
                                ),
                              ),
                            ],
                          ),
                        ],
                        const SizedBox(height: 12),
                        Align(
                          alignment: Alignment.centerRight,
                          child: applied
                              ? Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 12, vertical: 6),
                                  decoration: BoxDecoration(
                                    color: AppColors.success.withOpacity(0.15),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: const Text('Applied',
                                      style: TextStyle(
                                          color: AppColors.success,
                                          fontWeight: FontWeight.bold)),
                                )
                              : ElevatedButton(
                                  onPressed: _busy ? null : () => _apply(j),
                                  child: const Text('Apply'),
                                ),
                        ),
                      ],
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
