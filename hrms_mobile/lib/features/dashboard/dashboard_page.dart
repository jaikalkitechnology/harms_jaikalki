import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../core/routing/app_router.dart';
import '../../core/theme/app_colors.dart';
import '../auth/presentation/bloc/auth_bloc.dart';

class DashboardPage extends StatelessWidget {
  const DashboardPage({super.key, this.roleLabel});

  final String? roleLabel;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return BlocBuilder<AuthBloc, AuthState>(
      builder: (context, state) {
        final user = state.user;
        return Scaffold(
          appBar: AppBar(
            title: Image.asset(
              'assets/branding/jaikalki-logo-horizontal-light.png',
              height: 28,
            ),
            centerTitle: false,
            actions: [
              IconButton(
                icon: const Icon(Icons.logout),
                tooltip: 'Sign out',
                onPressed: () =>
                    context.read<AuthBloc>().add(const AuthLogoutRequested()),
              ),
            ],
          ),
          body: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Text(
                '★ ${(roleLabel ?? user?.role ?? 'EMPLOYEE').toUpperCase()}',
                style: theme.textTheme.labelSmall?.copyWith(
                  color: AppColors.brandGoldDark,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                'Welcome${user != null ? ', ${user.fullName.split(' ').first}' : ''}',
                style: theme.textTheme.headlineMedium,
              ),
              if (user != null) ...[
                const SizedBox(height: 4),
                Text(
                  '${user.email} · level ${user.roleLevel}',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: AppColors.brandBrownLight,
                  ),
                ),
              ],
              const SizedBox(height: 24),
              const _StatCard(
                label: 'Attendance',
                value: '—',
                hint: 'Phase 3',
              ),
              const SizedBox(height: 12),
              const _StatCard(
                label: 'Leave Balance',
                value: '—',
                hint: 'Phase 3',
              ),
              const SizedBox(height: 12),
              const _StatCard(
                label: 'Pending Approvals',
                value: '—',
                hint: 'Phase 4',
              ),
              const SizedBox(height: 12),
              const _StatCard(
                label: 'Latest Payslip',
                value: '—',
                hint: 'Phase 7',
              ),
              const SizedBox(height: 16),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  OutlinedButton.icon(
                    onPressed: () => context.push(AppRoutes.attendance),
                    icon: const Icon(Icons.fingerprint, size: 18),
                    label: const Text('Attendance'),
                  ),
                  OutlinedButton.icon(
                    onPressed: () => context.push(AppRoutes.leaves),
                    icon: const Icon(Icons.calendar_today_outlined, size: 18),
                    label: const Text('Leaves'),
                  ),
                  OutlinedButton.icon(
                    onPressed: () => context.push(AppRoutes.employees),
                    icon: const Icon(Icons.groups_outlined, size: 18),
                    label: const Text('Employees'),
                  ),
                  if (user != null &&
                      (user.role == 'manager' ||
                          user.role == 'hr' ||
                          user.role == 'director' ||
                          user.role == 'admin' ||
                          user.role == 'super_admin'))
                    FilledButton.icon(
                      onPressed: () => context.push(AppRoutes.approvalsInbox),
                      icon: const Icon(Icons.inbox_outlined, size: 18),
                      label: const Text('Approvals'),
                    ),
                  if (user != null && user.role == 'intern')
                    FilledButton.icon(
                      onPressed: () => context.push(AppRoutes.internExpenses),
                      icon: const Icon(Icons.flight_takeoff, size: 18),
                      label: const Text('Expenses'),
                    ),
                ],
              ),
              const SizedBox(height: 24),
              if (user != null && user.permissions.isNotEmpty)
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'PERMISSIONS',
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: AppColors.brandBrownLight,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 6,
                          runSpacing: 6,
                          children: user.permissions
                              .map(
                                (p) => Chip(
                                  label: Text(
                                    p,
                                    style: const TextStyle(fontSize: 11),
                                  ),
                                  backgroundColor: AppColors.brandBrown50,
                                  side: BorderSide.none,
                                ),
                              )
                              .toList(),
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        );
      },
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
                  Text(
                    label.toUpperCase(),
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: AppColors.brandBrownLight,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(value, style: theme.textTheme.headlineMedium),
                  const SizedBox(height: 2),
                  Text(
                    hint,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: AppColors.brandBrownLight,
                    ),
                  ),
                ],
              ),
            ),
            const Icon(
              Icons.arrow_forward_ios,
              size: 14,
              color: AppColors.brandBrownLight,
            ),
          ],
        ),
      ),
    );
  }
}
