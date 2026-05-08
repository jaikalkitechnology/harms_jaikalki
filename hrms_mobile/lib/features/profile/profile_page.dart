import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../core/routing/app_router.dart';
import '../../core/theme/app_colors.dart';
import '../../l10n/app_l10n.dart';
import '../auth/presentation/bloc/auth_bloc.dart';

class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context) {
    final l = AppL10n.of(context);
    return BlocBuilder<AuthBloc, AuthState>(
      builder: (context, state) {
        final user = state.user;
        return Scaffold(
          appBar: AppBar(
            title: Text(l.profile),
            actions: [
              IconButton(
                icon: const Icon(Icons.settings_outlined),
                onPressed: () =>
                    GoRouter.of(context).push(AppRoutes.settings),
              ),
            ],
          ),
          body: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _ProfileHeader(
                name: user?.fullName ?? user?.email ?? '—',
                role: user?.role,
                email: user?.email,
              ),
              const SizedBox(height: 16),
              if (user != null) ...[
                _InfoCard(
                  title: 'ACCOUNT',
                  rows: [
                    ('Email', user.email),
                    if (user.phone != null) ('Phone', user.phone!),
                    ('Role', user.role ?? '—'),
                    ('Level', '${user.roleLevel}'),
                  ],
                ),
                const SizedBox(height: 12),
                if (user.permissions.isNotEmpty)
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(14),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'PERMISSIONS',
                            style: Theme.of(context)
                                .textTheme
                                .labelSmall
                                ?.copyWith(
                                  color: AppColors.brandBrownLight,
                                ),
                          ),
                          const SizedBox(height: 8),
                          Wrap(
                            spacing: 6,
                            runSpacing: 6,
                            children: user.permissions
                                .map(
                                  (p) => Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 8,
                                      vertical: 3,
                                    ),
                                    decoration: BoxDecoration(
                                      color: AppColors.brandBrown50,
                                      borderRadius: BorderRadius.circular(6),
                                    ),
                                    child: Text(
                                      p,
                                      style: const TextStyle(
                                        fontSize: 10,
                                        fontFamily: 'monospace',
                                      ),
                                    ),
                                  ),
                                )
                                .toList(),
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
              const SizedBox(height: 24),
              OutlinedButton.icon(
                onPressed: () => _confirmLogout(context),
                icon: const Icon(Icons.logout, color: AppColors.error),
                label: Text(
                  l.logout,
                  style: const TextStyle(color: AppColors.error),
                ),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: AppColors.error),
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  Future<void> _confirmLogout(BuildContext context) async {
    final l = AppL10n.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        content: Text(l.logoutConfirm),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: Text(l.cancel),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: Text(l.logout),
          ),
        ],
      ),
    );
    if (ok == true && context.mounted) {
      context.read<AuthBloc>().add(const AuthLogoutRequested());
    }
  }
}

class _ProfileHeader extends StatelessWidget {
  const _ProfileHeader({required this.name, this.role, this.email});
  final String name;
  final String? role;
  final String? email;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Row(
          children: [
            CircleAvatar(
              radius: 32,
              backgroundColor: AppColors.brandGold.withOpacity(0.15),
              child: Text(
                name.isNotEmpty ? name[0].toUpperCase() : '?',
                style: const TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.w700,
                  color: context.textPrimary,
                ),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(name, style: theme.textTheme.titleLarge),
                  const SizedBox(height: 2),
                  if (email != null)
                    Text(
                      email!,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: AppColors.brandBrownLight,
                      ),
                    ),
                  if (role != null) ...[
                    const SizedBox(height: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppColors.brandGold.withOpacity(0.18),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        role!.toUpperCase(),
                        style: const TextStyle(
                          fontSize: 10,
                          fontFamily: 'monospace',
                          letterSpacing: 1.5,
                          fontWeight: FontWeight.w700,
                          color: AppColors.brandGoldDark,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({required this.title, required this.rows});
  final String title;
  final List<(String, String)> rows;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: AppColors.brandBrownLight,
                  ),
            ),
            const SizedBox(height: 8),
            ...rows.map(
              (r) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    SizedBox(width: 96, child: Text(r.$1)),
                    Expanded(
                      child: Text(
                        r.$2,
                        style: const TextStyle(fontWeight: FontWeight.w500),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
