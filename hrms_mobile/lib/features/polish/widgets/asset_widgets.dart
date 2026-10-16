import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/theme/app_colors.dart';
import '../../launch/data/exit_models.dart';

IconData assetIcon(String category) {
  final c = category.toLowerCase();
  if (RegExp('charger|battery|adapter').hasMatch(c)) {
    return Icons.battery_charging_full;
  }
  if (c.contains('laptop')) return Icons.laptop_mac;
  if (c.contains('sim')) return Icons.sim_card_outlined;
  if (RegExp('mobile|phone').hasMatch(c)) return Icons.phone_iphone;
  if (RegExp('headset|headphone').hasMatch(c)) return Icons.headset_mic;
  if (RegExp('monitor|screen|display').hasMatch(c)) return Icons.desktop_windows;
  if (c.contains('keyboard')) return Icons.keyboard;
  if (c.contains('mouse')) return Icons.mouse;
  if (RegExp('vehicle|bike|car').hasMatch(c)) return Icons.two_wheeler;
  return Icons.devices_other;
}

String conditionLabel(String? condition) => switch (condition) {
      'working' => 'Working',
      'damaged' => 'Damaged',
      'not_working' => 'Not working',
      'expired' => 'Expired',
      'lost' => 'Lost',
      null => '—',
      _ => condition.replaceAll('_', ' '),
    };

Color conditionColor(String? condition) => switch (condition) {
      'working' => AppColors.successText,
      'damaged' => AppColors.warning,
      'not_working' || 'lost' => AppColors.errorText,
      _ => AppColors.textFaint,
    };

/// "2026-10-31" -> "31 Oct 2026".
String fmtDay(String? iso) {
  final d = iso == null ? null : DateTime.tryParse(iso);
  return d == null ? (iso ?? '—') : DateFormat('d MMM yyyy').format(d);
}

class ConditionChip extends StatelessWidget {
  const ConditionChip(this.condition, {super.key});
  final String condition;

  @override
  Widget build(BuildContext context) {
    final c = conditionColor(condition);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: c.withOpacity(0.15),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        conditionLabel(condition),
        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: c),
      ),
    );
  }
}

/// Asset NOC: what's still to hand back, and what came back, for an exit.
class AssetClearanceCard extends StatelessWidget {
  const AssetClearanceCard({
    super.key,
    required this.clearance,
    this.title = 'Company assets',
  });

  final AssetClearance clearance;
  final String title;

  @override
  Widget build(BuildContext context) {
    final c = clearance;
    final theme = Theme.of(context);
    final tone = c.cleared ? AppColors.successText : AppColors.warning;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  c.cleared ? Icons.verified_outlined : Icons.inventory_2_outlined,
                  color: tone,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    title,
                    style: theme.textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                Text(
                  c.cleared ? 'Asset NOC cleared' : '${c.pending.length} to return',
                  style: TextStyle(color: tone, fontWeight: FontWeight.w600, fontSize: 12),
                ),
              ],
            ),
            if (!c.cleared && c.lastWorkingDay != null) ...[
              const SizedBox(height: 4),
              Text(
                'Hand these back by ${fmtDay(c.lastWorkingDay)} for exit clearance.',
                style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
              ),
            ],
            if (c.cleared && c.returned.isEmpty) ...[
              const SizedBox(height: 4),
              const Text(
                'No company assets to return.',
                style: TextStyle(color: AppColors.textMuted, fontSize: 12),
              ),
            ],
            for (final a in c.pending) ...[
              const SizedBox(height: 10),
              _ItemRow(item: a, trailing: const _Tag('To return', AppColors.warning)),
            ],
            for (final a in c.returned) ...[
              const SizedBox(height: 10),
              _ItemRow(
                item: a,
                trailing: _Tag(
                  'Returned ${fmtDay(a.returnedAt)}',
                  AppColors.successText,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ItemRow extends StatelessWidget {
  const _ItemRow({required this.item, required this.trailing});
  final AssetClearanceItem item;
  final Widget trailing;

  @override
  Widget build(BuildContext context) {
    final sub = [item.categoryName, item.assetTag].join(' · ');
    return Row(
      children: [
        CircleAvatar(
          radius: 16,
          backgroundColor: AppColors.brandGold.withOpacity(0.15),
          child: Icon(assetIcon(item.category), size: 16, color: AppColors.brandGold),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(item.name, style: TextStyle(color: context.textPrimary)),
              Text(sub, style: const TextStyle(color: AppColors.textMuted, fontSize: 11)),
            ],
          ),
        ),
        trailing,
      ],
    );
  }
}

class _Tag extends StatelessWidget {
  const _Tag(this.text, this.color);
  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        text,
        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: color),
      ),
    );
  }
}
