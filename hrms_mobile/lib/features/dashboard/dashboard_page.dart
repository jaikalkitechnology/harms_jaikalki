import 'package:flutter/material.dart';

import '../../core/constants/app_constants.dart';
import '../../core/theme/app_colors.dart';

class DashboardPage extends StatelessWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Image.asset(
          'assets/branding/jaikalki-logo-horizontal-light.png',
          height: 28,
        ),
        centerTitle: false,
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text('★ TODAY',
              style: theme.textTheme.labelSmall?.copyWith(
                color: AppColors.brandGoldDark,
              )),
          const SizedBox(height: 4),
          Text('Welcome to ${AppConstants.appName}',
              style: theme.textTheme.headlineMedium),
          const SizedBox(height: 24),
          _StatCard(label: 'Attendance', value: '—', hint: 'Phase 3'),
          const SizedBox(height: 12),
          _StatCard(label: 'Leave Balance', value: '—', hint: 'Phase 3'),
          const SizedBox(height: 12),
          _StatCard(label: 'Pending Approvals', value: '—', hint: 'Phase 4'),
          const SizedBox(height: 12),
          _StatCard(label: 'Latest Payslip', value: '—', hint: 'Phase 7'),
          const SizedBox(height: 32),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Phase 0 · Foundation',
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: AppColors.brandGoldDark,
                      )),
                  const SizedBox(height: 6),
                  Text('Scaffold ready', style: theme.textTheme.titleLarge),
                  const SizedBox(height: 8),
                  Text(
                    'Theme tokens, routing, DI, dio + secure storage are wired up. '
                    'Auth ships in Phase 1, employee profile in Phase 2.',
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: AppColors.brandBrownLight,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({
    required this.label,
    required this.value,
    required this.hint,
  });

  final String label;
  final String value;
  final String hint;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label.toUpperCase(),
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: AppColors.brandBrownLight,
                      )),
                  const SizedBox(height: 6),
                  Text(value, style: theme.textTheme.headlineMedium),
                  const SizedBox(height: 2),
                  Text(hint,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: AppColors.brandBrownLight,
                      )),
                ],
              ),
            ),
            const Icon(Icons.arrow_forward_ios,
                size: 14, color: AppColors.brandBrownLight),
          ],
        ),
      ),
    );
  }
}
