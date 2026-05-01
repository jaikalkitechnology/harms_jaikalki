import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/performance_api.dart';
import '../data/performance_models.dart';

class FeedbackInboxPage extends StatefulWidget {
  const FeedbackInboxPage({super.key});

  @override
  State<FeedbackInboxPage> createState() => _FeedbackInboxPageState();
}

class _FeedbackInboxPageState extends State<FeedbackInboxPage> {
  late Future<List<FeedbackRequest>> _future;

  @override
  void initState() {
    super.initState();
    _future = sl<PerformanceApi>().pendingFeedback();
  }

  Future<void> _refresh() async {
    setState(() => _future = sl<PerformanceApi>().pendingFeedback());
    await _future;
  }

  Future<void> _open(FeedbackRequest req) async {
    final result = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      builder: (_) => _FeedbackForm(req: req),
    );
    if (result == null) return;
    try {
      await sl<PerformanceApi>().submitFeedback(
        requestId: req.id,
        rating: result['rating'] as double,
        strengths: result['strengths'] as String?,
        improvementAreas: result['improvement'] as String?,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Feedback submitted — thank you'),
          backgroundColor: AppColors.success,
        ),
      );
      await _refresh();
    } on DioException catch (e) {
      if (!mounted) return;
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
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('360 Feedback Inbox')),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<FeedbackRequest>>(
          future: _future,
          builder: (context, snap) {
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final pending = snap.data!;
            if (pending.isEmpty) {
              return ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  const SizedBox(height: 80),
                  Icon(Icons.mark_email_read_outlined,
                      size: 64, color: AppColors.brandGoldDark),
                  const SizedBox(height: 16),
                  Center(
                    child: Text(
                      'No pending feedback requests.',
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
              itemCount: pending.length,
              itemBuilder: (context, i) {
                final req = pending[i];
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: AppColors.brandGoldPale,
                      child: Icon(
                        req.isAnonymous
                            ? Icons.visibility_off_outlined
                            : Icons.person,
                        color: AppColors.brandGoldDark,
                      ),
                    ),
                    title: Text('Feedback for employee #${req.subjectEmployeeId}'),
                    subtitle: Text(
                      '${req.relation.replaceAll("_", " ")} · '
                      '${req.isAnonymous ? "anonymous" : "identified"}',
                      style: theme.textTheme.bodySmall,
                    ),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () => _open(req),
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

class _FeedbackForm extends StatefulWidget {
  const _FeedbackForm({required this.req});
  final FeedbackRequest req;

  @override
  State<_FeedbackForm> createState() => _FeedbackFormState();
}

class _FeedbackFormState extends State<_FeedbackForm> {
  double _rating = 3;
  String _strengths = '';
  String _improvement = '';

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return DraggableScrollableSheet(
      expand: false,
      initialChildSize: 0.7,
      maxChildSize: 0.95,
      builder: (_, scroll) => Padding(
        padding: EdgeInsets.only(
          left: 20,
          right: 20,
          top: 20,
          bottom: MediaQuery.of(context).viewInsets.bottom + 20,
        ),
        child: SingleChildScrollView(
          controller: scroll,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Provide feedback', style: theme.textTheme.titleLarge),
              if (widget.req.isAnonymous)
                Padding(
                  padding: const EdgeInsets.only(top: 4),
                  child: Text(
                    'Your feedback will be shown anonymously in the aggregate.',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: AppColors.brandBrownLight,
                    ),
                  ),
                ),
              const SizedBox(height: 16),
              Text('Overall rating: ${_rating.toStringAsFixed(1)}',
                  style: theme.textTheme.titleMedium),
              Slider(
                value: _rating,
                min: 1,
                max: 5,
                divisions: 8,
                onChanged: (v) => setState(() => _rating = v),
              ),
              const SizedBox(height: 8),
              TextField(
                decoration: const InputDecoration(
                  labelText: 'Strengths',
                  border: OutlineInputBorder(),
                ),
                maxLines: 3,
                onChanged: (v) => _strengths = v,
              ),
              const SizedBox(height: 12),
              TextField(
                decoration: const InputDecoration(
                  labelText: 'Areas for improvement',
                  border: OutlineInputBorder(),
                ),
                maxLines: 3,
                onChanged: (v) => _improvement = v,
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () => Navigator.pop(context, {
                    'rating': _rating,
                    'strengths':
                        _strengths.trim().isEmpty ? null : _strengths.trim(),
                    'improvement':
                        _improvement.trim().isEmpty ? null : _improvement.trim(),
                  }),
                  child: const Text('Submit feedback'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
