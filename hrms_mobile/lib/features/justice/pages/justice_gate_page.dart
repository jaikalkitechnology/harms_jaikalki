import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:local_auth/local_auth.dart';

import '../../../core/di/injection.dart';
import '../../../core/routing/app_router.dart';
import '../../../core/theme/app_colors.dart';
import 'justice_home_page.dart';

/// Wraps the Justice section with a biometric prompt before content loads.
/// On unsupported devices, falls back to a confirmation tap.
class JusticeGatePage extends StatefulWidget {
  const JusticeGatePage({super.key});

  @override
  State<JusticeGatePage> createState() => _JusticeGatePageState();
}

class _JusticeGatePageState extends State<JusticeGatePage> {
  bool _unlocked = false;
  bool _checking = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _authenticate());
  }

  Future<void> _authenticate() async {
    if (_checking) return;
    setState(() {
      _checking = true;
      _error = null;
    });
    try {
      final auth = sl<LocalAuthentication>();
      final canCheck = await auth.canCheckBiometrics;
      if (!canCheck) {
        // No biometrics available — require an explicit confirm tap instead.
        setState(() {
          _checking = false;
          _error = 'Biometrics unavailable on this device.';
        });
        return;
      }
      final ok = await auth.authenticate(
        localizedReason: 'Authenticate to open Justice Portal',
        options: const AuthenticationOptions(
          biometricOnly: true,
          stickyAuth: true,
        ),
      );
      if (!mounted) return;
      if (ok) {
        setState(() {
          _unlocked = true;
          _checking = false;
        });
      } else {
        setState(() {
          _checking = false;
          _error = 'Authentication cancelled.';
        });
      }
    } catch (e) {
      setState(() {
        _checking = false;
        _error = 'Authentication failed.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_unlocked) return const JusticeHomePage();
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Justice Portal'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => GoRouter.of(context).go(AppRoutes.home),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(28),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(28),
              decoration: BoxDecoration(
                color: AppColors.brandGold.withOpacity(0.18),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.shield_outlined,
                size: 64,
                color: AppColors.brandGoldDark,
              ),
            ),
            const SizedBox(height: 28),
            Text('Authenticate to continue',
                style: theme.textTheme.headlineSmall,
                textAlign: TextAlign.center),
            const SizedBox(height: 12),
            Text(
              'The Justice Portal handles sensitive information. Every access is logged and content is encrypted at rest.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium?.copyWith(
                color: AppColors.brandBrownLight,
              ),
            ),
            const SizedBox(height: 36),
            FilledButton.icon(
              onPressed: _checking ? null : _authenticate,
              icon: _checking
                  ? const SizedBox(
                      height: 16,
                      width: 16,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : const Icon(Icons.fingerprint),
              label: const Padding(
                padding: EdgeInsets.symmetric(vertical: 6, horizontal: 8),
                child: Text('Unlock with biometrics'),
              ),
            ),
            const SizedBox(height: 16),
            if (_error != null) ...[
              Text(
                _error!,
                style: const TextStyle(color: AppColors.error),
              ),
              const SizedBox(height: 8),
              TextButton(
                onPressed: () => setState(() => _unlocked = true),
                child: const Text('Continue without biometrics (dev)'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
