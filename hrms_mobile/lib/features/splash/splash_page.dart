import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';

class SplashPage extends StatelessWidget {
  const SplashPage({super.key});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Scaffold(
      backgroundColor: isDark ? AppColors.brandBrownDarker : AppColors.cream,
      body: Center(
        child: Image.asset(
          isDark
              ? 'assets/branding/jaikalki-splash-dark.webp'
              : 'assets/branding/jaikalki-splash-light.png',
          fit: BoxFit.contain,
        ),
      ),
    );
  }
}
