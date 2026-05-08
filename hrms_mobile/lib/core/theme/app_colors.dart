import 'package:flutter/material.dart';

/// Jaikalki brand color tokens — mirror of `tailwind.config.ts`
/// in the React admin so the two clients stay visually consistent.
class AppColors {
  AppColors._();

  // ── Brand: Brown ──────────────────────────────────────
  static const Color brandBrown = Color(0xFF3D2817);
  static const Color brandBrownDark = Color(0xFF2D1810);
  static const Color brandBrownDarker = Color(0xFF1A0F08);
  static const Color brandBrownLight = Color(0xFF5C3D24);
  static const Color brandBrown50 = Color(0xFFF5EFE8);
  static const Color brandBrown100 = Color(0xFFE8DACA);

  // ── Brand: Gold ───────────────────────────────────────
  static const Color brandGold = Color(0xFFF4B71F);
  static const Color brandGoldBright = Color(0xFFFFC72C);
  static const Color brandGoldLight = Color(0xFFFFD66B);
  static const Color brandGoldLighter = Color(0xFFFCD34D);
  static const Color brandGoldDark = Color(0xFFC8941A);
  static const Color brandGoldPale = Color(0xFFFEF3C7);

  // ── Surfaces ─────────────────────────────────────────
  static const Color warmWhite = Color(0xFFFAFAF7);
  static const Color cream = Color(0xFFFDF8EE);
  static const Color cream50 = Color(0xFFFBF6E9);
  static const Color warmOffWhite = Color(0xFFFAF0E6);

  // ── Semantic ────────────────────────────────────────
  static const Color success = Color(0xFF5E8B3A);
  static const Color successLight = Color(0xFFDCEEC9);
  static const Color warning = Color(0xFFE89F1A);
  static const Color warningLight = Color(0xFFFEF3C7);
  static const Color error = Color(0xFFC53030);
  static const Color errorLight = Color(0xFFFED7D7);
  static const Color info = Color(0xFF2C7A7B);
  static const Color infoLight = Color(0xFFC9E8E9);

  // ── Role colors ─────────────────────────────────────
  static const Color roleSuperAdmin = Color(0xFF6B46C1);
  static const Color roleAdmin = Color(0xFFB91C1C);
  static const Color roleDirector = brandGold;
  static const Color roleHr = Color(0xFF0F766E);
  static const Color roleManager = Color(0xFF1E40AF);
  static const Color roleEmployee = brandBrown;
  static const Color roleField = Color(0xFFC2410C);
  static const Color roleTrainer = Color(0xFF15803D);
  static const Color roleIntern = Color(0xFFFCD34D);
}


/// Theme-aware accessors so widgets can keep using brand-flavoured
/// colours without rendering dark-on-dark in dark mode. Prefer these
/// inside Text / Icon widgets:
///
///     Text('Hello', style: TextStyle(color: ctx.textPrimary));
///     Text('Subtitle', style: TextStyle(color: ctx.textMuted));
extension AppColorsContext on BuildContext {
  /// Brand-brown in light mode, near-white in dark mode.
  Color get textPrimary {
    final brightness = Theme.of(this).brightness;
    return brightness == Brightness.dark
        ? AppColors.warmWhite
        : AppColors.brandBrownDarker;
  }

  /// Slightly muted body text — readable in both modes.
  Color get textMuted {
    final brightness = Theme.of(this).brightness;
    return brightness == Brightness.dark
        ? AppColors.brandBrown100
        : AppColors.brandBrownLight;
  }

  /// A surface card colour that contrasts with the scaffold.
  Color get surfaceCard {
    return Theme.of(this).cardColor;
  }
}
