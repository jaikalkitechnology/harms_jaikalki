import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/injection.dart';
import '../../../core/routing/app_router.dart';
import '../../../core/theme/app_colors.dart';
import '../data/justice_api.dart';
import '../data/justice_models.dart';

class JusticeHomePage extends StatefulWidget {
  const JusticeHomePage({super.key});

  @override
  State<JusticeHomePage> createState() => _JusticeHomePageState();
}

class _JusticeHomePageState extends State<JusticeHomePage> {
  late Future<List<ComplaintListItem>> _future;

  @override
  void initState() {
    super.initState();
    _future = sl<JusticeApi>().myComplaints();
  }

  Future<void> _refresh() async {
    setState(() => _future = sl<JusticeApi>().myComplaints());
    await _future;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Justice Portal'),
        actions: [
          IconButton(
            icon: const Icon(Icons.help_outline),
            onPressed: () => context.push(AppRoutes.justiceResources),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () =>
            context.push(AppRoutes.justiceSubmit).then((_) => _refresh()),
        backgroundColor: AppColors.brandGoldDark,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.shield_outlined),
        label: const Text('New complaint'),
      ),
      body: FutureBuilder<List<ComplaintListItem>>(
        future: _future,
        builder: (context, snap) {
          if (!snap.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final items = snap.data!;
          return RefreshIndicator(
            onRefresh: _refresh,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
              children: [
                Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppColors.brandGoldDark.withOpacity(0.08),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: AppColors.brandGoldDark.withOpacity(0.25),
                    ),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.lock_outline,
                          color: AppColors.brandGoldDark),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          'Your complaints are end-to-end encrypted. Only authorised members can decrypt them, and every access is logged.',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: context.textPrimary,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                Text('★ MY COMPLAINTS',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: AppColors.brandGoldDark,
                    )),
                const SizedBox(height: 8),
                if (items.isEmpty)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 24),
                    child: Center(
                      child: Text('You haven\'t submitted any complaints yet.'),
                    ),
                  )
                else
                  ...items.map((c) => _ComplaintRow(complaint: c)),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _ComplaintRow extends StatelessWidget {
  const _ComplaintRow({required this.complaint});
  final ComplaintListItem complaint;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: ListTile(
        title: Text(complaint.subject,
            maxLines: 1, overflow: TextOverflow.ellipsis),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(complaint.ticketNumber,
                style: theme.textTheme.bodySmall?.copyWith(
                  fontFamily: 'monospace',
                  color: AppColors.brandBrownLight,
                )),
            Text(
              complaint.complaintType.replaceAll('_', ' '),
              style: theme.textTheme.bodySmall?.copyWith(
                color: AppColors.brandBrownLight,
              ),
            ),
          ],
        ),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: AppColors.brandGold.withOpacity(0.18),
            borderRadius: BorderRadius.circular(6),
          ),
          child: Text(
            complaint.status.replaceAll('_', ' ').toUpperCase(),
            style: const TextStyle(
              fontSize: 9,
              fontFamily: 'monospace',
              letterSpacing: 1.2,
              fontWeight: FontWeight.w700,
              color: AppColors.brandGoldDark,
            ),
          ),
        ),
      ),
    );
  }
}
