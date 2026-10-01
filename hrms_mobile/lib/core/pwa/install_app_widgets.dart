import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../di/injection.dart';
import '../theme/app_colors.dart';
import 'pwa_install.dart';

const _kDismissedAt = 'pwa.install_banner.dismissed_at';
const _snooze = Duration(days: 7);

/// Runs the right install flow for this device: the browser's dialog
/// where there is one, otherwise step-by-step instructions.
Future<void> startInstall(BuildContext context) async {
  final pwa = PwaInstall.instance;
  if (pwa.mode == PwaInstallMode.prompt) {
    final accepted = await pwa.promptInstall();
    if (accepted && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Installed — open Jaikalki HRMS from your home screen'),
        ),
      );
    }
    return;
  }
  await showInstallInstructions(context, pwa.mode);
}

/// "Install Jaikalki HRMS" card for the login and home screens. Shown in
/// the browser only; "Not now" hides it for a week.
class InstallAppBanner extends StatefulWidget {
  const InstallAppBanner({super.key, this.margin = EdgeInsets.zero});

  final EdgeInsetsGeometry margin;

  @override
  State<InstallAppBanner> createState() => _InstallAppBannerState();
}

class _InstallAppBannerState extends State<InstallAppBanner> {
  late bool _snoozed = _isSnoozed();

  bool _isSnoozed() {
    final raw = sl<SharedPreferences>().getString(_kDismissedAt);
    final at = raw == null ? null : DateTime.tryParse(raw);
    return at != null && DateTime.now().difference(at) < _snooze;
  }

  Future<void> _dismiss() async {
    setState(() => _snoozed = true);
    await sl<SharedPreferences>()
        .setString(_kDismissedAt, DateTime.now().toIso8601String());
  }

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: PwaInstall.instance,
      builder: (context, _) {
        final pwa = PwaInstall.instance;
        if (_snoozed || !pwa.canOffer) return const SizedBox.shrink();
        return Container(
          margin: widget.margin,
          padding: const EdgeInsets.fromLTRB(14, 14, 8, 10),
          decoration: BoxDecoration(
            color: AppColors.brandBrownDark,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.brandGoldDark.withOpacity(0.6)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(10),
                    child: Image.asset(
                      'assets/branding/jaikalki-icon-only-256.png',
                      width: 40,
                      height: 40,
                    ),
                  ),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Install Jaikalki HRMS',
                          style: TextStyle(
                            color: AppColors.warmWhite,
                            fontWeight: FontWeight.w600,
                            fontSize: 15,
                          ),
                        ),
                        SizedBox(height: 2),
                        Text(
                          'Add it to your home screen — opens full screen, '
                          'starts faster, no browser bar.',
                          style: TextStyle(
                            color: AppColors.textMuted,
                            fontSize: 12.5,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: _dismiss,
                    style: TextButton.styleFrom(
                      foregroundColor: AppColors.textMuted,
                    ),
                    child: const Text('Not now'),
                  ),
                  const SizedBox(width: 4),
                  FilledButton.icon(
                    onPressed: () => startInstall(context),
                    icon: Icon(
                      pwa.mode == PwaInstallMode.prompt
                          ? Icons.download_rounded
                          : Icons.add_to_home_screen,
                      size: 18,
                    ),
                    label: Text(
                      pwa.mode == PwaInstallMode.prompt ? 'Install' : 'How to install',
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }
}

/// Settings entry — always available in the browser (ignores "Not now").
class InstallAppTile extends StatelessWidget {
  const InstallAppTile({super.key});

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: PwaInstall.instance,
      builder: (context, _) {
        final mode = PwaInstall.instance.mode;
        if (mode == PwaInstallMode.unavailable) return const SizedBox.shrink();
        final installed = mode == PwaInstallMode.installed;
        return ListTile(
          leading: Icon(
            installed ? Icons.check_circle_outline : Icons.add_to_home_screen,
            color: installed ? AppColors.successText : AppColors.brandGold,
          ),
          title: Text(installed ? 'App installed' : 'Install app'),
          subtitle: Text(
            installed
                ? 'Running from your home screen'
                : 'Add Jaikalki HRMS to this device',
          ),
          onTap: installed ? null : () => startInstall(context),
        );
      },
    );
  }
}

/// Step-by-step help for browsers without an install dialog.
Future<void> showInstallInstructions(
  BuildContext context,
  PwaInstallMode mode,
) {
  final (title, steps, note) = switch (mode) {
    PwaInstallMode.ios => (
        'Add to your iPhone / iPad',
        const [
          (Icons.ios_share, 'Tap the Share button — at the bottom in Safari, '
              'top right in Chrome.'),
          (Icons.add_box_outlined, 'Scroll down and tap "Add to Home Screen".'),
          (Icons.check_circle_outline, 'Tap "Add". Open Jaikalki HRMS from '
              'your home screen.'),
        ],
        'Opened this link inside WhatsApp, Gmail or another app? Open it in '
            'Safari first — apps can\'t add to the home screen.',
      ),
    PwaInstallMode.macSafari => (
        'Add to your Mac',
        const [
          (Icons.menu, 'In Safari, open the File menu.'),
          (Icons.add_box_outlined, 'Choose "Add to Dock".'),
          (Icons.check_circle_outline, 'Click "Add". It opens like any app.'),
        ],
        null,
      ),
    _ => (
        'Add to your phone',
        const [
          (Icons.more_vert, 'Tap the browser menu (⋮) at the top right.'),
          (Icons.add_to_home_screen,
              'Tap "Install app" or "Add to Home screen".'),
          (Icons.check_circle_outline, 'Confirm. Open Jaikalki HRMS from '
              'your home screen.'),
        ],
        'Using an in-app browser? Open the link in Chrome first.',
      ),
  };

  return showModalBottomSheet<void>(
    context: context,
    showDragHandle: true,
    backgroundColor: AppColors.brandBrownDark,
    builder: (ctx) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 0, 24, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(ctx).textTheme.titleLarge),
            const SizedBox(height: 16),
            for (var i = 0; i < steps.length; i++)
              Padding(
                padding: const EdgeInsets.only(bottom: 14),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    CircleAvatar(
                      radius: 16,
                      backgroundColor: AppColors.brandGold.withOpacity(0.18),
                      child: Icon(steps[i].$1,
                          size: 18, color: AppColors.brandGold),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Padding(
                        padding: const EdgeInsets.only(top: 6),
                        child: Text(
                          '${i + 1}.  ${steps[i].$2}',
                          style: const TextStyle(
                            color: AppColors.warmWhite,
                            height: 1.4,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            if (note != null)
              Text(
                note,
                style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
              ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: () => Navigator.of(ctx).pop(),
                child: const Text('Got it'),
              ),
            ),
          ],
        ),
      ),
    ),
  );
}
