import 'package:flutter/material.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/incentives_api.dart';

/// Managers: approve, change or reject their direct reports' incentives
/// before HR approves them for payroll.
class IncentiveReviewPage extends StatefulWidget {
  const IncentiveReviewPage({super.key});

  @override
  State<IncentiveReviewPage> createState() => _IncentiveReviewPageState();
}

class _IncentiveReviewPageState extends State<IncentiveReviewPage> {
  late Future<List<IncentiveLine>> _future = sl<IncentivesApi>().reviewQueue();
  final Set<int> _busy = {};

  Future<void> _refresh() async {
    setState(() => _future = sl<IncentivesApi>().reviewQueue());
    await _future;
  }

  String _inr(double v) => '₹${v.toStringAsFixed(0)}';

  Future<void> _act(IncentiveLine l, String action) async {
    double? amount;
    String? note;
    if (action != 'approve') {
      final amountCtl = TextEditingController(text: (l.amount ?? l.calculated).toStringAsFixed(0));
      final noteCtl = TextEditingController();
      final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: Text(action == 'adjust' ? 'Change ${l.employeeName}\'s amount' : 'Reject ${l.employeeName}\'s incentive'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (action == 'adjust')
                TextField(
                  controller: amountCtl,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(labelText: 'Amount to pay (₹)'),
                ),
              TextField(
                controller: noteCtl,
                maxLength: 500,
                decoration: const InputDecoration(labelText: 'Reason'),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
            FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Save')),
          ],
        ),
      );
      if (ok != true) return;
      note = noteCtl.text.trim();
      if (note.isEmpty) {
        _toast('Please give a reason.', error: true);
        return;
      }
      if (action == 'adjust') amount = double.tryParse(amountCtl.text.trim());
    }
    setState(() => _busy.add(l.id));
    try {
      await sl<IncentivesApi>().review(l.id, action, amount: amount, note: note);
      _toast(action == 'approve' ? 'Approved' : action == 'adjust' ? 'Amount changed' : 'Rejected');
      await _refresh();
    } catch (_) {
      _toast('Could not save.', error: true);
    } finally {
      if (mounted) setState(() => _busy.remove(l.id));
    }
  }

  void _toast(String msg, {bool error = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: error ? AppColors.error : AppColors.success,
    ));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Review incentives')),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<IncentiveLine>>(
          future: _future,
          builder: (context, snap) {
            if (snap.hasError) {
              return ListView(children: const [
                SizedBox(height: 100),
                Center(child: Text('Could not load. Pull down to try again.', style: TextStyle(color: AppColors.textMuted))),
              ]);
            }
            if (!snap.hasData) return const Center(child: CircularProgressIndicator());
            final lines = snap.data!;
            if (lines.isEmpty) {
              return ListView(children: const [
                SizedBox(height: 100),
                Icon(Icons.verified_outlined, size: 56, color: AppColors.brandGoldDark),
                SizedBox(height: 10),
                Center(child: Text('Nothing to review.', style: TextStyle(color: AppColors.textMuted))),
              ]);
            }
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                const Text(
                  'Approve the calculated amount, change it (with a reason) or reject it. '
                  'HR approves the final list for payroll.',
                  style: TextStyle(color: AppColors.textMuted, fontSize: 12.5),
                ),
                const SizedBox(height: 12),
                for (final l in lines) _card(l),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _card(IncentiveLine l) {
    final statusColor = switch (l.reviewStatus) {
      'approved' => AppColors.successText,
      'adjusted' => AppColors.infoText,
      'rejected' => AppColors.errorText,
      _ => AppColors.textMuted,
    };
    final statusLabel = switch (l.reviewStatus) {
      'approved' => 'Approved',
      'adjusted' => 'Changed',
      'rejected' => 'Rejected',
      _ => 'To review',
    };
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(l.employeeName,
                      style: TextStyle(color: context.textPrimary, fontWeight: FontWeight.w700, fontSize: 15)),
                ),
                Text(statusLabel, style: TextStyle(color: statusColor, fontWeight: FontWeight.w600, fontSize: 12.5)),
              ],
            ),
            Text('${l.schemeName} · ${l.periodLabel}',
                style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
            const SizedBox(height: 8),
            Text(
              '${l.pct.toStringAsFixed(0)}% of target'
              '${l.attendance != null ? ' · attendance ${l.attendance!.toStringAsFixed(0)}%' : ''}',
              style: TextStyle(color: context.textPrimary, fontSize: 13),
            ),
            if (!l.eligible)
              for (final r in l.reasons)
                Text('• $r', style: const TextStyle(color: AppColors.errorText, fontSize: 12.5)),
            const SizedBox(height: 6),
            Text(
              'Calculated ${_inr(l.calculated)} · to pay ${_inr(l.amount ?? 0)}',
              style: TextStyle(color: context.textPrimary, fontWeight: FontWeight.w600),
            ),
            if (l.reviewNote != null)
              Text('“${l.reviewNote}”', style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
            const SizedBox(height: 8),
            if (_busy.contains(l.id))
              const LinearProgressIndicator()
            else
              Wrap(
                spacing: 8,
                children: [
                  if (l.reviewStatus != 'approved')
                    FilledButton.tonal(onPressed: () => _act(l, 'approve'), child: const Text('Approve')),
                  OutlinedButton(onPressed: () => _act(l, 'adjust'), child: const Text('Change')),
                  if (l.reviewStatus != 'rejected')
                    TextButton(
                      onPressed: () => _act(l, 'reject'),
                      child: const Text('Reject', style: TextStyle(color: AppColors.errorText)),
                    ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}
