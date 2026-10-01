import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../core/di/injection.dart';
import '../../core/routing/app_router.dart';
import '../../core/theme/app_colors.dart';
import '../../l10n/app_l10n.dart';
import '../auth/domain/repositories/auth_repository.dart';
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
                                    emp.category?.name ?? emp.category?.code),
                                _row(Icons.location_on_outlined,
                                    'WORK LOCATION', emp.workLocation),
                                _row(Icons.work_outline, 'WORK MODE',
                                    _label(emp.workMode)),
                                _row(Icons.assignment_ind_outlined,
                                    'EMPLOYMENT TYPE',
                                    _label(emp.employmentType)),
                                _row(Icons.event_outlined, 'JOINED ON',
                                    _date(emp.dateOfJoining)),
                                if (emp.confirmationDate != null)
                                  _row(Icons.verified_outlined,
                                      'CONFIRMED ON', _date(emp.confirmationDate)),
                                if (emp.isOnProbation &&
                                    emp.probationEndDate != null)
                                  _row(Icons.hourglass_top_outlined,
                                      'PROBATION ENDS',
                                      _date(emp.probationEndDate)),
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
                                    _date(emp.dateOfBirth)),
                                _row(Icons.person_outline, 'GENDER',
                                    _label(emp.gender)),
                                _row(Icons.favorite_outline,
                                    'MARITAL STATUS',
                                    _label(emp.maritalStatus)),
                                _row(Icons.bloodtype_outlined,
                                    'BLOOD GROUP', emp.bloodGroup),
                              ],
                            ),
                            const SizedBox(height: 16),
                            const _StatutoryNomineeSection(),
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
                            icon: const Icon(Icons.lock_outline,
                                color: AppColors.brandGoldDark),
                            label: const Text(
                              'CHANGE PASSWORD',
                              style:
                                  TextStyle(color: AppColors.brandGoldDark),
                            ),
                            style: OutlinedButton.styleFrom(
                              side: const BorderSide(
                                  color: AppColors.brandGoldDark),
                              padding: const EdgeInsets.symmetric(
                                  vertical: 14),
                              minimumSize: const Size.fromHeight(0),
                            ),
                            onPressed: () =>
                                _showChangePassword(context),
                          ),
                          const SizedBox(height: 10),
                          OutlinedButton.icon(
                            icon: const Icon(Icons.logout,
                                color: AppColors.errorText),
                            label: Text(
                              l.logout,
                              style:
                                  const TextStyle(color: AppColors.errorText),
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

  Future<void> _showChangePassword(BuildContext context) async {
    final oldCtrl = TextEditingController();
    final newCtrl = TextEditingController();
    final confirmCtrl = TextEditingController();
    final messenger = ScaffoldMessenger.of(context);
    await showDialog<void>(
      context: context,
      builder: (ctx) {
        bool busy = false;
        String? error;
        bool obscure = true;
        return StatefulBuilder(
          builder: (ctx, setLocal) => AlertDialog(
            title: const Text('Change password'),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  TextField(
                    controller: oldCtrl,
                    obscureText: obscure,
                    decoration: const InputDecoration(
                      labelText: 'Current password',
                    ),
                  ),
                  const SizedBox(height: 10),
                  TextField(
                    controller: newCtrl,
                    obscureText: obscure,
                    decoration: const InputDecoration(
                      labelText: 'New password (min 8 chars)',
                    ),
                  ),
                  const SizedBox(height: 10),
                  TextField(
                    controller: confirmCtrl,
                    obscureText: obscure,
                    decoration: InputDecoration(
                      labelText: 'Confirm new password',
                      suffixIcon: IconButton(
                        icon: Icon(obscure
                            ? Icons.visibility_outlined
                            : Icons.visibility_off_outlined),
                        onPressed: () =>
                            setLocal(() => obscure = !obscure),
                      ),
                    ),
                  ),
                  if (error != null) ...[
                    const SizedBox(height: 10),
                    Text(error!,
                        style:
                            const TextStyle(color: AppColors.errorText)),
                  ],
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: busy ? null : () => Navigator.of(ctx).pop(),
                child: const Text('Cancel'),
              ),
              FilledButton(
                onPressed: busy
                    ? null
                    : () async {
                        final oldP = oldCtrl.text;
                        final newP = newCtrl.text;
                        if (newP.length < 8) {
                          setLocal(() => error =
                              'New password must be at least 8 characters');
                          return;
                        }
                        if (newP != confirmCtrl.text) {
                          setLocal(() =>
                              error = 'Passwords do not match');
                          return;
                        }
                        setLocal(() {
                          busy = true;
                          error = null;
                        });
                        try {
                          await sl<AuthRepository>().changePassword(
                            oldPassword: oldP,
                            newPassword: newP,
                          );
                          if (ctx.mounted) Navigator.of(ctx).pop();
                          messenger.showSnackBar(
                            const SnackBar(
                              content: Text(
                                'Password changed. You may need to '
                                'sign in again on other devices.',
                              ),
                              backgroundColor: AppColors.success,
                            ),
                          );
                        } on DioException catch (e) {
                          final msg = e.response?.data is Map
                              ? (e.response!.data['detail']
                                      ?.toString() ??
                                  'Could not change password')
                              : 'Could not change password';
                          setLocal(() {
                            busy = false;
                            error = msg;
                          });
                        } catch (_) {
                          setLocal(() {
                            busy = false;
                            error = 'Could not change password';
                          });
                        }
                      },
                child: busy
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Save'),
              ),
            ],
          ),
        );
      },
    );
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

/// "full_time" → "Full time".
String? _label(String? raw) {
  if (raw == null || raw.isEmpty) return raw;
  final s = raw.replaceAll('_', ' ').toLowerCase();
  return s[0].toUpperCase() + s.substring(1);
}

/// "2025-04-01" → "1 Apr 2025".
String? _date(String? iso) {
  final d = iso == null ? null : DateTime.tryParse(iso);
  return d == null ? iso : DateFormat('d MMM yyyy').format(d);
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
                    color: AppColors.textMuted,
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

// ── Statutory & nominee (self-service: view + add, nominee locks) ─────
class _StatutoryNomineeSection extends StatefulWidget {
  const _StatutoryNomineeSection();

  @override
  State<_StatutoryNomineeSection> createState() =>
      _StatutoryNomineeSectionState();
}

class _StatutoryNomineeSectionState
    extends State<_StatutoryNomineeSection> {
  late Future<MyStatutory> _future;

  @override
  void initState() {
    super.initState();
    _future = sl<EmployeeApi>().myStatutory();
  }

  void _reload() {
    setState(() => _future = sl<EmployeeApi>().myStatutory());
  }

  String _typeLabel(String t) {
    switch (t) {
      case 'pf':
        return 'PF';
      case 'gratuity':
        return 'Gratuity';
      case 'insurance':
        return 'Insurance';
      default:
        return 'General';
    }
  }

  Future<void> _addStatutory(MyStatutory s) async {
    final fields = <String, TextEditingController>{
      if ((s.pfNumber ?? '').isEmpty)
        'pf_number': TextEditingController(),
      if ((s.uanNumber ?? '').isEmpty)
        'uan_number': TextEditingController(),
      if ((s.esicNumber ?? '').isEmpty)
        'esic_number': TextEditingController(),
      if ((s.insuranceCompany ?? '').isEmpty)
        'insurance_company': TextEditingController(),
      if ((s.insurancePolicyNo ?? '').isEmpty)
        'insurance_policy_no': TextEditingController(),
    };
    if (fields.isEmpty) return;
    const labels = {
      'pf_number': 'PF number',
      'uan_number': 'UAN number',
      'esic_number': 'ESIC number',
      'insurance_company': 'Mediclaim insurer',
      'insurance_policy_no': 'Mediclaim policy no.',
    };
    final messenger = ScaffoldMessenger.of(context);
    await showDialog<void>(
      context: context,
      builder: (ctx) {
        bool busy = false;
        String? error;
        return StatefulBuilder(
          builder: (ctx, setLocal) => AlertDialog(
            title: const Text('Add statutory details'),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'You can fill in blank fields once. Corrections '
                    'afterwards go through HR.',
                    style: TextStyle(fontSize: 12),
                  ),
                  const SizedBox(height: 8),
                  for (final e in fields.entries) ...[
                    TextField(
                      controller: e.value,
                      decoration:
                          InputDecoration(labelText: labels[e.key]),
                    ),
                    const SizedBox(height: 8),
                  ],
                  if (error != null)
                    Text(error!,
                        style:
                            const TextStyle(color: AppColors.errorText)),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed:
                    busy ? null : () => Navigator.of(ctx).pop(),
                child: const Text('Cancel'),
              ),
              FilledButton(
                onPressed: busy
                    ? null
                    : () async {
                        final payload = <String, dynamic>{};
                        for (final e in fields.entries) {
                          final v = e.value.text.trim();
                          if (v.isNotEmpty) payload[e.key] = v;
                        }
                        if (payload.isEmpty) {
                          Navigator.of(ctx).pop();
                          return;
                        }
                        setLocal(() {
                          busy = true;
                          error = null;
                        });
                        try {
                          await sl<EmployeeApi>()
                              .addStatutory(payload);
                          if (ctx.mounted) Navigator.of(ctx).pop();
                          messenger.showSnackBar(
                            const SnackBar(
                              content: Text('Saved'),
                              backgroundColor: AppColors.success,
                            ),
                          );
                          _reload();
                        } on DioException catch (e) {
                          final msg = e.response?.data is Map
                              ? (e.response!.data['detail']
                                      ?.toString() ??
                                  'Could not save')
                              : 'Could not save';
                          setLocal(() {
                            busy = false;
                            error = msg;
                          });
                        } catch (_) {
                          setLocal(() {
                            busy = false;
                            error = 'Could not save';
                          });
                        }
                      },
                child: busy
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child:
                            CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Save'),
              ),
            ],
          ),
        );
      },
    );
  }

  Future<void> _addNominee() async {
    final name = TextEditingController();
    final relation = TextEditingController();
    final phone = TextEditingController();
    final share = TextEditingController(text: '100');
    final guardian = TextEditingController();
    String type = 'general';
    bool minor = false;
    final messenger = ScaffoldMessenger.of(context);
    await showDialog<void>(
      context: context,
      builder: (ctx) {
        bool busy = false;
        String? error;
        return StatefulBuilder(
          builder: (ctx, setLocal) => AlertDialog(
            title: const Text('Add nominee'),
            content: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'Nominee can be added once. After this it is '
                    'locked — contact HR to change.',
                    style: TextStyle(fontSize: 12),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: name,
                    decoration:
                        const InputDecoration(labelText: 'Full name'),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: relation,
                    decoration: const InputDecoration(
                        labelText: 'Relation (e.g. Spouse)'),
                  ),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<String>(
                    value: type,
                    decoration:
                        const InputDecoration(labelText: 'Applies to'),
                    items: const [
                      DropdownMenuItem(
                          value: 'general', child: Text('General')),
                      DropdownMenuItem(value: 'pf', child: Text('PF')),
                      DropdownMenuItem(
                          value: 'gratuity', child: Text('Gratuity')),
                      DropdownMenuItem(
                          value: 'insurance',
                          child: Text('Insurance')),
                    ],
                    onChanged: (v) =>
                        setLocal(() => type = v ?? 'general'),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: share,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(
                        labelText: 'Share %'),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: phone,
                    keyboardType: TextInputType.phone,
                    decoration: const InputDecoration(
                        labelText: 'Phone (optional)'),
                  ),
                  const SizedBox(height: 8),
                  CheckboxListTile(
                    contentPadding: EdgeInsets.zero,
                    value: minor,
                    title: const Text('Nominee is a minor'),
                    onChanged: (v) =>
                        setLocal(() => minor = v ?? false),
                  ),
                  if (minor)
                    TextField(
                      controller: guardian,
                      decoration: const InputDecoration(
                          labelText: 'Guardian name'),
                    ),
                  if (error != null) ...[
                    const SizedBox(height: 8),
                    Text(error!,
                        style:
                            const TextStyle(color: AppColors.errorText)),
                  ],
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed:
                    busy ? null : () => Navigator.of(ctx).pop(),
                child: const Text('Cancel'),
              ),
              FilledButton(
                onPressed: busy
                    ? null
                    : () async {
                        if (name.text.trim().length < 2 ||
                            relation.text.trim().length < 2) {
                          setLocal(() => error =
                              'Name and relation are required');
                          return;
                        }
                        setLocal(() {
                          busy = true;
                          error = null;
                        });
                        try {
                          await sl<EmployeeApi>().addNominee({
                            'name': name.text.trim(),
                            'relation': relation.text.trim(),
                            'nominee_type': type,
                            'share_pct':
                                num.tryParse(share.text.trim()) ??
                                    100,
                            if (phone.text.trim().isNotEmpty)
                              'phone': phone.text.trim(),
                            'is_minor': minor,
                            if (minor &&
                                guardian.text.trim().isNotEmpty)
                              'guardian_name': guardian.text.trim(),
                          });
                          if (ctx.mounted) Navigator.of(ctx).pop();
                          messenger.showSnackBar(
                            const SnackBar(
                              content: Text('Nominee added'),
                              backgroundColor: AppColors.success,
                            ),
                          );
                          _reload();
                        } on DioException catch (e) {
                          final msg = e.response?.data is Map
                              ? (e.response!.data['detail']
                                      ?.toString() ??
                                  'Could not add nominee')
                              : 'Could not add nominee';
                          setLocal(() {
                            busy = false;
                            error = msg;
                          });
                        } catch (_) {
                          setLocal(() {
                            busy = false;
                            error = 'Could not add nominee';
                          });
                        }
                      },
                child: busy
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child:
                            CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Save'),
              ),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return FutureBuilder<MyStatutory>(
      future: _future,
      builder: (context, snap) {
        if (snap.connectionState != ConnectionState.done) {
          return const SizedBox.shrink();
        }
        if (snap.hasError || !snap.hasData) {
          return const SizedBox.shrink();
        }
        final s = snap.data!;
        final stat = <(String, String?)>[
          ('PF NUMBER', s.pfNumber),
          ('UAN NUMBER', s.uanNumber),
          ('ESIC NUMBER', s.esicNumber),
          ('MEDICLAIM INSURER', s.insuranceCompany),
          ('MEDICLAIM POLICY NO.', s.insurancePolicyNo),
        ];
        final hasBlank = stat.any((r) => (r.$2 ?? '').isEmpty);
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(
                  vertical: 8, horizontal: 4),
              child: Text(
                '★ STATUTORY & NOMINEE',
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
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    for (final r in stat) ...[
                      Padding(
                        padding:
                            const EdgeInsets.symmetric(vertical: 6),
                        child: Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment:
                                    CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    r.$1,
                                    style: const TextStyle(
                                      fontSize: 9,
                                      letterSpacing: 1.4,
                                      fontWeight: FontWeight.w600,
                                      color:
                                          AppColors.textMuted,
                                    ),
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    (r.$2 ?? '').isEmpty
                                        ? 'Not added'
                                        : r.$2!,
                                    style: TextStyle(
                                      fontSize: 14,
                                      fontWeight: FontWeight.w600,
                                      color: (r.$2 ?? '').isEmpty
                                          ? context.textMuted
                                          : context.textPrimary,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                      Divider(
                        height: 1,
                        color: AppColors.brandBrown100
                            .withOpacity(0.4),
                      ),
                    ],
                    const SizedBox(height: 8),
                    if (hasBlank)
                      Align(
                        alignment: Alignment.centerLeft,
                        child: TextButton.icon(
                          icon: const Icon(Icons.add, size: 18),
                          label: const Text('Add statutory details'),
                          onPressed: () => _addStatutory(s),
                        ),
                      ),
                    const SizedBox(height: 4),
                    Text(
                      'NOMINEES',
                      style: const TextStyle(
                        fontSize: 9,
                        letterSpacing: 1.4,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textMuted,
                      ),
                    ),
                    const SizedBox(height: 6),
                    if (s.nominees.isEmpty)
                      Text(
                        'No nominee on record.',
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: context.textMuted,
                        ),
                      )
                    else
                      ...s.nominees.map(
                        (n) => Padding(
                          padding: const EdgeInsets.symmetric(
                              vertical: 4),
                          child: Row(
                            children: [
                              const Icon(Icons.person_outline,
                                  size: 18,
                                  color: AppColors.brandGoldDark),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  '${n.name} · ${n.relation} · '
                                  '${_typeLabel(n.nomineeType)} · '
                                  '${n.sharePct}%',
                                  style: TextStyle(
                                    fontSize: 13,
                                    color: context.textPrimary,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    const SizedBox(height: 6),
                    if (s.nomineesLocked)
                      Row(
                        children: [
                          const Icon(Icons.lock_outline,
                              size: 14,
                              color: AppColors.textMuted),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              'Nominee details are locked. '
                              'Contact HR to change.',
                              style: theme.textTheme.bodySmall
                                  ?.copyWith(
                                color: context.textMuted,
                              ),
                            ),
                          ),
                        ],
                      )
                    else
                      Align(
                        alignment: Alignment.centerLeft,
                        child: TextButton.icon(
                          icon: const Icon(Icons.add, size: 18),
                          label: const Text('Add nominee'),
                          onPressed: _addNominee,
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}
