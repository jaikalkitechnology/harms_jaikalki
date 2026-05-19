import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SettingsState extends Equatable {
  // App is dark-mode + English only — these are fixed, not user-set.
  const SettingsState({
    this.themeMode = ThemeMode.dark,
    this.locale = const Locale('en'),
    this.biometricEnabled = false,
    this.onboardingCompleted = false,
    this.notificationsEnabled = true,
  });

  final ThemeMode themeMode;
  final Locale locale;
  final bool biometricEnabled;
  final bool onboardingCompleted;
  final bool notificationsEnabled;

  SettingsState copyWith({
    ThemeMode? themeMode,
    Locale? locale,
    bool? biometricEnabled,
    bool? onboardingCompleted,
    bool? notificationsEnabled,
  }) =>
      SettingsState(
        themeMode: themeMode ?? this.themeMode,
        locale: locale ?? this.locale,
        biometricEnabled: biometricEnabled ?? this.biometricEnabled,
        onboardingCompleted: onboardingCompleted ?? this.onboardingCompleted,
        notificationsEnabled:
            notificationsEnabled ?? this.notificationsEnabled,
      );

  @override
  List<Object?> get props => [
        themeMode,
        locale,
        biometricEnabled,
        onboardingCompleted,
        notificationsEnabled,
      ];
}

class SettingsCubit extends Cubit<SettingsState> {
  SettingsCubit(this._prefs) : super(const SettingsState());

  final SharedPreferences _prefs;

  static const _kTheme = 'jaikalki.theme';
  static const _kLocale = 'jaikalki.locale';
  static const _kBio = 'jaikalki.biometric';
  static const _kOnboarding = 'jaikalki.onboarding_done';
  static const _kNotifications = 'jaikalki.notifications';

  void hydrate() {
    final bio = _prefs.getBool(_kBio) ?? false;
    final onboarded = _prefs.getBool(_kOnboarding) ?? false;
    final notifs = _prefs.getBool(_kNotifications) ?? true;

    // Theme + language are intentionally fixed: dark mode, English.
    emit(SettingsState(
      themeMode: ThemeMode.dark,
      locale: const Locale('en'),
      biometricEnabled: bio,
      onboardingCompleted: onboarded,
      notificationsEnabled: notifs,
    ));
  }

  Future<void> setThemeMode(ThemeMode mode) async {
    await _prefs.setString(_kTheme, _fromThemeMode(mode));
    emit(state.copyWith(themeMode: mode));
  }

  Future<void> setLocale(Locale locale) async {
    await _prefs.setString(_kLocale, locale.languageCode);
    emit(state.copyWith(locale: locale));
  }

  Future<void> setBiometric(bool enabled) async {
    await _prefs.setBool(_kBio, enabled);
    emit(state.copyWith(biometricEnabled: enabled));
  }

  Future<void> markOnboardingComplete() async {
    await _prefs.setBool(_kOnboarding, true);
    emit(state.copyWith(onboardingCompleted: true));
  }

  Future<void> setNotifications(bool enabled) async {
    await _prefs.setBool(_kNotifications, enabled);
    emit(state.copyWith(notificationsEnabled: enabled));
  }

  String _fromThemeMode(ThemeMode m) => switch (m) {
        ThemeMode.light => 'light',
        ThemeMode.dark => 'dark',
        ThemeMode.system => 'system',
      };
}
