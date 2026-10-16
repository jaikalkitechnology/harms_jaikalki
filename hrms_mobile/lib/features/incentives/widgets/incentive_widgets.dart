import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';
import '../../team/widgets/team_widgets.dart';
import '../data/incentives_api.dart';

String _inr(double v) => '₹${v.toStringAsFixed(0).replaceAllMapped(
      RegExp(r'(\d)(?=(\d\d)+\d$)'),
      (m) => '${m[1]},',
    )}';

/// "You're at 82% — ₹18,000 more to reach 100% (₹5,000)".
class IncentiveCard extends StatelessWidget {
  const IncentiveCard({super.key, required this.p});
  final IncentiveProjection p;

  @override
  Widget build(BuildContext context) {
    final next = p.nextSlab;
    final needed = next == null ? null : double.tryParse('${next['still_needed']}');
    final neededText = needed == null
        ? ''
        : p.isMoney
            ? '${_inr(needed)} more'
            : '${needed.toStringAsFixed(0)} more ${p.unit}';
    return Card(
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.emoji_events_outlined, color: AppColors.brandGold),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(p.schemeName,
                      style: TextStyle(color: context.textPrimary, fontWeight: FontWeight.w700, fontSize: 16)),
                ),
              ],
            ),
            if ((p.description ?? '').isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(p.description!, style: const TextStyle(color: AppColors.textMuted, fontSize: 12.5)),
              ),
            const SizedBox(height: 12),
            Row(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Earning now', style: TextStyle(color: AppColors.textMuted, fontSize: 12)),
                      Text(_inr(p.earningNow),
                          style: TextStyle(
                            color: p.earningNow > 0 ? AppColors.successText : context.textPrimary,
                            fontSize: 24,
                            fontWeight: FontWeight.w800,
                          )),
                    ],
                  ),
                ),
                Text('${p.pct.toStringAsFixed(0)}% of target',
                    style: const TextStyle(color: AppColors.textMuted, fontSize: 12.5)),
              ],
            ),
            const SizedBox(height: 10),
            TargetProgress(pct: p.pct),
            const SizedBox(height: 10),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                for (final s in p.slabs)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: (p.pct >= (double.tryParse('${s['min_pct']}') ?? 0)
                              ? AppColors.successText
                              : AppColors.brandGold)
                          .withOpacity(0.14),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      '${(double.tryParse('${s['min_pct']}') ?? 0).toStringAsFixed(0)}% → '
                      '${_inr(double.tryParse('${s['amount']}') ?? 0)}',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: p.pct >= (double.tryParse('${s['min_pct']}') ?? 0)
                            ? AppColors.successText
                            : AppColors.brandGold,
                      ),
                    ),
                  ),
              ],
            ),
            if (next != null) ...[
              const SizedBox(height: 10),
              Text(
                '$neededText to reach ${(double.tryParse('${next['min_pct']}') ?? 0).toStringAsFixed(0)}% '
                '— that pays ${_inr(double.tryParse('${next['amount']}') ?? 0)}.',
                style: TextStyle(color: context.textPrimary, fontSize: 13.5),
              ),
            ] else if (p.slabs.isNotEmpty)
              const Padding(
                padding: EdgeInsets.only(top: 10),
                child: Text('Top slab reached — well done!',
                    style: TextStyle(color: AppColors.successText, fontWeight: FontWeight.w600)),
              ),
            for (final w in p.warnings)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.info_outline, size: 16, color: AppColors.warning),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text('$w — needed to qualify.',
                          style: const TextStyle(color: AppColors.warning, fontSize: 12.5)),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class IncentiveHistory extends StatelessWidget {
  const IncentiveHistory({super.key, required this.lines});
  final List<IncentiveLine> lines;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.zero,
      child: Column(
        children: [
          for (final l in lines)
            ListTile(
              title: Text('${l.schemeName} · ${l.periodLabel}',
                  style: TextStyle(color: context.textPrimary, fontSize: 14)),
              subtitle: Text(_status(l), style: TextStyle(color: _statusColor(l), fontSize: 12)),
              trailing: Text(
                l.amount == null ? '—' : _inr(l.amount!),
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      color: context.textPrimary,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0,
                    ),
              ),
            ),
        ],
      ),
    );
  }

  static String _status(IncentiveLine l) {
    if (l.runStatus != 'approved') return 'Being reviewed';
    if ((l.amount ?? 0) <= 0) {
      final why = l.reviewNote ?? (l.reasons.isNotEmpty ? l.reasons.first : null);
      return why == null ? 'Not paid' : 'Not paid — $why';
    }
    if (l.paid) return 'Paid with ${l.payoutLabel} salary';
    return 'Approved — paid with ${l.payoutLabel} salary';
  }

  static Color _statusColor(IncentiveLine l) {
    if (l.runStatus != 'approved') return AppColors.textMuted;
    return (l.amount ?? 0) > 0 ? AppColors.successText : AppColors.textMuted;
  }
}
