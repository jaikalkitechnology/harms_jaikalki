import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/theme/app_colors.dart';
import '../../../l10n/app_l10n.dart';
import '../../auth/presentation/bloc/auth_bloc.dart';
import '../cubit/settings_cubit.dart';

class SettingsPage extends StatelessWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context) {
    final l = AppL10n.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l.settings)),
      body: BlocBuilder<SettingsCubit, SettingsState>(
        builder: (context, state) {
          final cubit = context.read<SettingsCubit>();
          return ListView(
            padding: const EdgeInsets.symmetric(vertical: 8),
            children: [
              _SectionHeader(label: 'SECURITY'),
              BlocBuilder<AuthBloc, AuthState>(
                builder: (context, auth) {
                  return SwitchListTile(
                    title: Text(l.biometric),
                    subtitle: Text(
                      auth.biometricAvailable
                          ? 'Face ID / fingerprint sign-in'
                          : 'Not available on this device',
                    ),
                    value: auth.biometricEnabled,
                    onChanged: auth.biometricAvailable
                        ? (v) {
                            cubit.setBiometric(v);
                            context
                                .read<AuthBloc>()
                                .add(AuthBiometricToggleRequested(v));
                          }
                        : null,
                  );
                },
              ),
              SwitchListTile(
                title: Text(l.notifications),
                value: state.notificationsEnabled,
                onChanged: cubit.setNotifications,
              ),
              const Divider(),
              _SectionHeader(label: 'ABOUT'),
              ListTile(
                leading: const Icon(Icons.info_outline),
                title: Text(l.aboutApp),
                subtitle: const Text('Jaikalki HRMS · v0.1'),
              ),
              ListTile(
                leading: const Icon(Icons.shield_outlined),
                title: Text(l.privacyPolicy),
                onTap: () {},
              ),
            ],
          );
        },
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.label});
  final String label;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 18, 16, 8),
      child: Text(
        label,
        style: const TextStyle(
          fontSize: 11,
          fontFamily: 'JetBrainsMono',
          letterSpacing: 2,
          color: AppColors.brandGoldDark,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
