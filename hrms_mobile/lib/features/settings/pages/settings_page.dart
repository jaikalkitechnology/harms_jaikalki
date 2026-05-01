import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/theme/app_colors.dart';
import '../../../l10n/app_l10n.dart';
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
              _SectionHeader(label: l.theme.toUpperCase()),
              RadioListTile<ThemeMode>(
                value: ThemeMode.system,
                groupValue: state.themeMode,
                title: Text(l.themeSystem),
                onChanged: (m) => cubit.setThemeMode(m!),
              ),
              RadioListTile<ThemeMode>(
                value: ThemeMode.light,
                groupValue: state.themeMode,
                title: Text(l.themeLight),
                onChanged: (m) => cubit.setThemeMode(m!),
              ),
              RadioListTile<ThemeMode>(
                value: ThemeMode.dark,
                groupValue: state.themeMode,
                title: Text(l.themeDark),
                onChanged: (m) => cubit.setThemeMode(m!),
              ),
              const Divider(),
              _SectionHeader(label: l.language.toUpperCase()),
              RadioListTile<String>(
                value: 'en',
                groupValue: state.locale.languageCode,
                title: const Text('English'),
                onChanged: (v) => cubit.setLocale(Locale(v!)),
              ),
              RadioListTile<String>(
                value: 'hi',
                groupValue: state.locale.languageCode,
                title: const Text('हिन्दी'),
                onChanged: (v) => cubit.setLocale(Locale(v!)),
              ),
              const Divider(),
              _SectionHeader(label: 'SECURITY'),
              SwitchListTile(
                title: Text(l.biometric),
                subtitle: const Text('Face ID / fingerprint'),
                value: state.biometricEnabled,
                onChanged: cubit.setBiometric,
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
          fontFamily: 'monospace',
          letterSpacing: 2,
          color: AppColors.brandGoldDark,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
