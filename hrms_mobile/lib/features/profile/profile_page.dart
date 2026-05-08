import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../core/di/injection.dart';
import '../../core/routing/app_router.dart';
import '../../core/theme/app_colors.dart';
import '../../l10n/app_l10n.dart';
import '../auth/presentation/bloc/auth_bloc.dart';
import '../employees/data/employee_api.dart';
import '../employees/data/employee_models.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  late Future<EmployeeDetail?> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<EmployeeDetail?> _load() async {
    try {
      return await sl<EmployeeApi>().me();
    } catch (_) {
      // No employee record linked or call failed — fall back to user
      // info already in memory.
      return null;
    }
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  @override
  Widget build(BuildContext context) {
    final l = AppL10n.of(context);
    return BlocBuilder<AuthBloc, AuthState>(
      builder: (context, state) {
        final user = state.user;
        return Scaffold(
          body: RefreshIndicator(
            onRefresh: _refresh,
            child: FutureBuilder<EmployeeDetail?>(
              future: _future,
              builder: (context, snap) {
                final emp = snap.data;
                final fullName = emp?.fullName ??
                    user?.fullName ??
                    user?.email ??
                    '—';
                final initial = fullName.isNotEmpty
                    ? fullName[0].toUpperCase()
                    : '?';
                return ListView(
                  padding: EdgeInsets.zero,
                  children: [
                    _ProfileHero(
                      fullName: fullName,
                      initial: initial,
                      role: user?.role,
                      employeeCode: emp?.employeeCode,
                      photoUrl: emp?.photoUrl,
                      onLogout: () => _confirmLogout(context),
                      onSettings: () =>
                          GoRouter.of(context).push(AppRoutes.settings),
                    ),
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 18, 16, 24),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          if (emp != null) ...[
                            _Section(
                              title: '★ WORK INFO',
                              rows: [
                                _row(Icons.business_outlined, 'DEPARTMENT',
                                    emp.department?.name),
                                _row(Icons.badge_outlined, 'DESIGNATION',
                                    emp.designation?.name),
                                _row(Icons.category_outlined, 'CATEGORY',
                                    emp.category?.code ?? emp.category?.name),
                                _row(Icons.location_on_outlined,
                                    'WORK LOCATION', emp.workLocation),
                                _row(Icons.work_outline, 'WORK MODE',
                                    emp.workMode?.toUpperCase()),
                                _row(Icons.assignment_ind_outlined,
                                    'EMPLOYMENT TYPE',
                                    emp.employmentType?.toUpperCase()),
                                _row(Icons.event_outlined, 'JOINED ON',
                                    emp.dateOfJoining),
                                if (emp.confirmationDate != null)
                                  _row(Icons.verified_outlined,
                                      'CONFIRMED ON', emp.confirmationDate),
                                if (emp.isOnProbation &&
                                    emp.probationEndDate != null)
                                  _row(Icons.hourglass_top_outlined,
                                      'PROBATION ENDS',
                                      emp.probationEndDate),
                              ],
                            ),
                            const SizedBox(height: 16),
                            _Section(
                              title: '★ CONTACT',
                              rows: [
                                _row(Icons.phone_outlined, 'PHONE',
                                    emp.personalPhone ?? user?.phone),
                                _row(Icons.alternate_email_outlined,
                                    'PERSONAL EMAIL', emp.personalEmail),
                                _row(Icons.mail_outline, 'WORK EMAIL',
                                    user?.email),
                              ],
                            ),
                            const SizedBox(height: 16),
                            _Section(
                              title: '★ PERSONAL',
                              rows: [
                                _row(Icons.cake_outlined, 'DATE OF BIRTH',
                                    emp.dateOfBirth),
                                _row(Icons.person_outline, 'GENDER',
                                    emp.gender?.toUpperCase()),
                                _row(Icons.favorite_outline,
                                    'MARITAL STATUS',
                                    emp.maritalStatus?.toUpperCase()),
                                _row(Icons.bloodtype_outlined,
                                    'BLOOD GROUP', emp.bloodGroup),
                              ],
                            ),
                          ] else if (snap.connectionState ==
                                  ConnectionState.done &&
                              user != null) ...[
                            // Fallback: no employee record linked.
                            _Section(
                              title: '★ ACCOUNT',
                              rows: [
                                _row(Icons.mail_outline, 'EMAIL', user.email),
                                if (user.phone != null)
                                  _row(Icons.phone_outlined, 'PHONE',
                                      user.phone),
                                _row(Icons.shield_outlined, 'ROLE',
                                    user.role?.toUpperCase()),
                              ],
                            ),
                          ] else
                            const Center(
                              child: Padding(
                                padding: EdgeInsets.all(40),
                                child: CircularProgressIndicator(),
                              ),
                            ),
                          const SizedBox(height: 20),
                          Row(
                            children: [
                              Expanded(
                                child: ElevatedButton.icon(
                                  icon: const Icon(Icons.edit_outlined),
                                  label: const Text('EDIT PROFILE'),
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: AppColors.brandGoldDark,
                                    foregroundColor: Colors.white,
                                    padding: const EdgeInsets.symmetric(
                                        vertical: 14),
                                  ),
                                  onPressed: () => _toast(
                                    context,
                                    'Self-edit is currently desk-only — '
                                    'ask HR / Admin from the app for now.',
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 10),
                          OutlinedButton.icon(
                            icon: const Icon(Icons.logout,
                                color: AppColors.error),
                            label: Text(
                              l.logout,
                              style:
                                  const TextStyle(color: AppColors.error),
                            ),
                            style: OutlinedButton.styleFrom(
                              side: const BorderSide(color: AppColors.error),
                              padding: const EdgeInsets.symmetric(
                                  vertical: 14),
                              minimumSize: const Size.fromHeight(0),
                            ),
                            onPressed: () => _confirmLogout(context),
                          ),
                          const SizedBox(height: 60),
                        ],
                      ),
                    ),
                  ],
                );
              },
            ),
          ),
        );
      },
    );
  }

  void _toast(BuildContext context, String msg) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
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

  static (IconData, String, String?) _row(
    IconData icon,
    String label,
    String? value,
  ) =>
      (icon, label, value);
}

// ── Hero card ────────────────────────────────────────────────────────
class _ProfileHero extends StatelessWidget {
  const _ProfileHero({
    required this.fullName,
    required this.initial,
    required this.onLogout,
    required this.onSettings,
    this.role,
    this.employeeCode,
    this.photoUrl,
  });

  final String fullName;
  final String initial;
  final String? role;
  final String? employeeCode;
  final String? photoUrl;
  final VoidCallback onLogout;
  final VoidCallback onSettings;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          colors: [Color(0xFF2D1810), Color(0xFF3D2817)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      padding: EdgeInsets.fromLTRB(
        20,
        MediaQuery.of(context).padding.top + 14,
        20,
        28,
      ),
      child: Column(
        children: [
          Row(
            children: [
              IconButton(
                icon: const Icon(Icons.arrow_back, color: Colors.white),
                onPressed: () => Navigator.of(context).maybePop(),
              ),
              Expanded(
                child: RichText(
                  textAlign: TextAlign.center,
                  text: TextSpan(
                    style: theme.textTheme.titleLarge?.copyWith(
                      color: AppColors.warmWhite,
                      fontWeight: FontWeight.w700,
                    ),
                    children: const [
                      TextSpan(text: 'My '),
                      TextSpan(
                        text: 'Profile',
                        style: TextStyle(
                          fontStyle: FontStyle.italic,
                          color: AppColors.brandGold,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.settings_outlined,
                    color: Colors.white),
                onPressed: onSettings,
              ),
            ],
          ),
          const SizedBox(height: 12),
          // Photo halo
          Stack(
            alignment: Alignment.center,
            children: [
              Container(
                width: 124,
                height: 124,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: RadialGradient(
                    colors: [
                      AppColors.brandGold.withOpacity(0.45),
                      Colors.transparent,
                    ],
                  ),
                ),
              ),
              CircleAvatar(
                radius: 52,
                backgroundColor: AppColors.warmWhite,
                backgroundImage:
                    photoUrl != null ? NetworkImage(photoUrl!) : null,
                child: photoUrl == null
                    ? Text(
                        initial,
                        style: const TextStyle(
                          fontSize: 44,
                          fontWeight: FontWeight.w700,
                          color: AppColors.brandBrownDarker,
                        ),
                      )
                    : null,
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            fullName,
            style: theme.textTheme.headlineSmall?.copyWith(
              color: AppColors.warmWhite,
              fontWeight: FontWeight.w700,
            ),
          ),
          if (role != null) ...[
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(
                  horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                color: AppColors.brandGold.withOpacity(0.2),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: AppColors.brandGold.withOpacity(0.5),
                ),
              ),
              child: Text(
                '★ ${role!.toUpperCase()}',
                style: const TextStyle(
                  color: AppColors.brandGold,
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.4,
                ),
              ),
            ),
          ],
          if (employeeCode != null) ...[
            const SizedBox(height: 8),
            Text(
              'EMPLOYEE ID · $employeeCode',
              style: TextStyle(
                color: AppColors.brandGold.withOpacity(0.85),
                fontSize: 10,
                letterSpacing: 1.6,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

// ── Info section card ────────────────────────────────────────────────
class _Section extends StatelessWidget {
  const _Section({required this.title, required this.rows});
  final String title;
  final List<(IconData, String, String?)> rows;

  @override
  Widget build(BuildContext context) {
    final visible = rows.where((r) {
      final v = r.$3;
      return v != null && v.trim().isNotEmpty && v != '—';
    }).toList();
    if (visible.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 4),
          child: Text(
            title,
            style: const TextStyle(
              fontSize: 11,
              letterSpacing: 1.6,
              fontWeight: FontWeight.w700,
              color: AppColors.brandGoldDark,
            ),
          ),
        ),
        Card(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
            child: Column(
              children: [
                for (var i = 0; i < visible.length; i++) ...[
                  _InfoRow(
                    icon: visible[i].$1,
                    label: visible[i].$2,
                    value: visible[i].$3!,
                  ),
                  if (i < visible.length - 1)
                    Divider(
                      height: 1,
                      color: AppColors.brandBrown100.withOpacity(0.4),
                    ),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
  });
  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Row(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.brandGold.withOpacity(0.18),
            ),
            child: Icon(icon, color: AppColors.brandGoldDark, size: 18),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(
                    fontSize: 9,
                    letterSpacing: 1.4,
                    fontWeight: FontWeight.w600,
                    color: AppColors.brandBrownLight,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: context.textPrimary,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
