import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/exam_api.dart';
import '../data/exam_models.dart';

class ExamListPage extends StatefulWidget {
  const ExamListPage({super.key});

  @override
  State<ExamListPage> createState() => _ExamListPageState();
}

class _ExamListPageState extends State<ExamListPage> {
  late Future<({List<ExamSummary> exams, List<CertificateOut> certs})> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<({List<ExamSummary> exams, List<CertificateOut> certs})> _load() async {
    final api = sl<ExamApi>();
    final exams = await api.exams();
    final certs = await api.myCertificates();
    return (exams: exams, certs: certs);
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  Color _typeColor(String t) {
    switch (t) {
      case 'certification':
        return AppColors.brandGoldDark;
      case 'mandatory':
        return AppColors.error;
      case 'practice':
        return AppColors.info;
      default:
        return AppColors.warning;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Exams & Certificates')),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<
            ({List<ExamSummary> exams, List<CertificateOut> certs})>(
          future: _future,
          builder: (context, snap) {
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final exams = snap.data!.exams;
            final certs = snap.data!.certs;
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                if (certs.isNotEmpty) ...[
                  Text('★ MY CERTIFICATES (${certs.length})',
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: AppColors.brandGoldDark,
                      )),
                  const SizedBox(height: 8),
                  ...certs.map(
                    (c) => Card(
                      color: AppColors.brandGoldPale,
                      margin: const EdgeInsets.only(bottom: 8),
                      child: ListTile(
                        leading: Icon(Icons.workspace_premium,
                            color: AppColors.brandGoldDark, size: 32),
                        title: Text(c.title,
                            style: theme.textTheme.titleSmall),
                        subtitle: Text(
                          '${c.certificateNumber}\nIssued ${c.issuedDate}'
                          '${c.expiryDate != null ? " · expires ${c.expiryDate}" : ""}',
                          style: theme.textTheme.bodySmall,
                        ),
                        trailing: c.scorePercentage != null
                            ? Text('${c.scorePercentage!.toStringAsFixed(0)}%',
                                style: theme.textTheme.titleMedium?.copyWith(
                                  color: AppColors.brandGoldDark,
                                  fontWeight: FontWeight.bold,
                                ))
                            : null,
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                ],
                Text('★ AVAILABLE EXAMS (${exams.length})',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: AppColors.brandGoldDark,
                    )),
                const SizedBox(height: 8),
                if (exams.isEmpty)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: Center(child: Text('No exams scheduled.')),
                    ),
                  ),
                ...exams.map(
                  (e) => Card(
                    margin: const EdgeInsets.only(bottom: 12),
                    child: InkWell(
                      borderRadius: BorderRadius.circular(12),
                      onTap: () => context.push('/exams/${e.id}/take'),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Expanded(
                                  child: Text(e.title,
                                      style: theme.textTheme.titleMedium),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 8, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: _typeColor(e.examType)
                                        .withOpacity(0.15),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Text(
                                    e.examType.toUpperCase(),
                                    style: TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.bold,
                                      color: _typeColor(e.examType),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            Text(e.code,
                                style: theme.textTheme.bodySmall?.copyWith(
                                  fontFamily: 'JetBrainsMono',
                                  color: AppColors.textMuted,
                                )),
                            if (e.description != null) ...[
                              const SizedBox(height: 6),
                              Text(e.description!,
                                  style: theme.textTheme.bodySmall),
                            ],
                            const SizedBox(height: 8),
                            Wrap(
                              spacing: 12,
                              children: [
                                _Pill(
                                  icon: Icons.timer_outlined,
                                  label: '${e.timeLimitMinutes} min',
                                ),
                                _Pill(
                                  icon: Icons.help_outline,
                                  label: '${e.totalQuestions} Qs',
                                ),
                                _Pill(
                                  icon: Icons.verified_outlined,
                                  label: 'Pass ${e.passingPercentage}%',
                                ),
                                _Pill(
                                  icon: Icons.replay_outlined,
                                  label: '${e.attemptsAllowed} attempts',
                                ),
                              ],
                            ),
                          ],
                        ),
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

class _Pill extends StatelessWidget {
  const _Pill({required this.icon, required this.label});
  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: AppColors.textMuted),
        const SizedBox(width: 4),
        Text(label, style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }
}
