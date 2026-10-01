import 'package:flutter/material.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:share_plus/share_plus.dart';

import '../../../core/theme/app_colors.dart';
import '../../polish/data/polish_models.dart';

class VisitorPassPage extends StatelessWidget {
  const VisitorPassPage({super.key, required this.visitor});

  final Visitor visitor;

  Color _statusColor() {
    switch (visitor.status) {
      case 'checked_in':
        return AppColors.success;
      case 'checked_out':
        return AppColors.textMuted;
      case 'cancelled':
      case 'no_show':
        return AppColors.error;
      default:
        return AppColors.info;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final statusColor = _statusColor();
    return Scaffold(
      appBar: AppBar(
        title: const Text('Visitor Pass'),
        actions: [
          IconButton(
            icon: const Icon(Icons.ios_share),
            tooltip: 'Share QR token',
            onPressed: () => Share.share(
              'Jaikalki Visitor Pass\nName: ${visitor.fullName}\n'
              'QR: ${visitor.qrToken}\nExpected: ${visitor.expectedAt}',
              subject: 'Visitor pass for ${visitor.fullName}',
            ),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF3D2817), Color(0xFF5C3D24)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(
              children: [
                Text(
                  'JAIKALKI VISITOR PASS',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: AppColors.brandGold,
                    letterSpacing: 1.6,
                  ),
                ),
                const SizedBox(height: 16),
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: QrImageView(
                    data: visitor.qrToken,
                    version: QrVersions.auto,
                    size: 220,
                    backgroundColor: Colors.white,
                  ),
                ),
                const SizedBox(height: 18),
                Text(
                  visitor.fullName,
                  style: theme.textTheme.titleLarge?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                if (visitor.company != null) ...[
                  const SizedBox(height: 4),
                  Text(
                    visitor.company!,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: Colors.white.withOpacity(0.8),
                    ),
                  ),
                ],
                const SizedBox(height: 12),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: statusColor.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: statusColor.withOpacity(0.4)),
                  ),
                  child: Text(
                    visitor.status.replaceAll('_', ' ').toUpperCase(),
                    style: TextStyle(
                      color: statusColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 11,
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          _info('Purpose', visitor.purpose),
          _info('Expected at', visitor.expectedAt),
          if (visitor.checkedInAt != null) _info('Checked in', visitor.checkedInAt!),
          if (visitor.checkedOutAt != null)
            _info('Checked out', visitor.checkedOutAt!),
          if (visitor.badgeNumber != null) _info('Badge', visitor.badgeNumber!),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.brandGoldPale,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              'Show this QR at the reception. Security can scan it to check '
              'you in or out using the Jaikalki staff app or admin panel.',
              style: theme.textTheme.bodySmall?.copyWith(
                color: AppColors.brandBrownDarker,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _info(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          SizedBox(
            width: 100,
            child: Text(
              label,
              style: const TextStyle(
                fontSize: 12,
                color: AppColors.textMuted,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}
