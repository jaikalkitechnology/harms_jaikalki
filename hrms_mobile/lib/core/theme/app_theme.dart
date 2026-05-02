import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'app_colors.dart';

class AppTheme {
  AppTheme._();

  static ThemeData light() {
    final base = ThemeData.light(useMaterial3: true);
    final colorScheme = ColorScheme.fromSeed(
      seedColor: AppColors.brandBrown,
      brightness: Brightness.light,
      primary: AppColors.brandBrown,
      onPrimary: AppColors.warmWhite,
      secondary: AppColors.brandGold,
      onSecondary: AppColors.brandBrownDarker,
      surface: AppColors.warmWhite,
      onSurface: AppColors.brandBrownDarker,
      error: AppColors.error,
    );

    return base.copyWith(
      colorScheme: colorScheme,
      scaffoldBackgroundColor: AppColors.cream,
      textTheme: _textTheme(base.textTheme, AppColors.brandBrownDarker),
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.warmWhite,
        foregroundColor: AppColors.brandBrownDarker,
        elevation: 0,
        scrolledUnderElevation: 1,
        titleTextStyle: GoogleFonts.playfairDisplay(
          fontSize: 22,
          fontWeight: FontWeight.w700,
          color: AppColors.brandBrownDarker,
        ),
      ),
      cardTheme: CardThemeData(
        color: AppColors.warmWhite,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: const BorderSide(color: AppColors.brandBrown100),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: AppColors.brandBrown,
          foregroundColor: AppColors.warmWhite,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: GoogleFonts.poppins(fontWeight: FontWeight.w600),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.warmWhite,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.brandBrown100),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.brandBrown100),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.brandGold, width: 1.5),
        ),
      ),
      dividerColor: AppColors.brandBrown100,
    );
  }

  static ThemeData dark() {
    final base = ThemeData.dark(useMaterial3: true);
    final colorScheme = ColorScheme.fromSeed(
      seedColor: AppColors.brandGold,
      brightness: Brightness.dark,
      primary: AppColors.brandGold,
      onPrimary: AppColors.brandBrownDarker,
      secondary: AppColors.brandGoldLight,
      onSecondary: AppColors.brandBrownDarker,
      surface: AppColors.brandBrownDarker,
      onSurface: AppColors.warmWhite,
      error: AppColors.error,
    );

    return base.copyWith(
      colorScheme: colorScheme,
      scaffoldBackgroundColor: AppColors.brandBrownDarker,
      textTheme: _textTheme(base.textTheme, AppColors.warmWhite),
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.brandBrownDark,
        foregroundColor: AppColors.warmWhite,
        elevation: 0,
        titleTextStyle: GoogleFonts.playfairDisplay(
          fontSize: 22,
          fontWeight: FontWeight.w700,
          color: AppColors.warmWhite,
        ),
      ),
      cardTheme: CardThemeData(
        color: AppColors.brandBrownDark,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: BorderSide(color: AppColors.brandBrownLight.withOpacity(0.3)),
        ),
      ),
    );
  }

  static TextTheme _textTheme(TextTheme base, Color color) {
    final body = GoogleFonts.poppinsTextTheme(base).apply(
      bodyColor: color,
      displayColor: color,
    );
    return body.copyWith(
      displayLarge: GoogleFonts.playfairDisplay(
        fontWeight: FontWeight.w700,
        color: color,
        letterSpacing: -0.5,
      ),
      displayMedium: GoogleFonts.playfairDisplay(
        fontWeight: FontWeight.w700,
        color: color,
      ),
      headlineLarge: GoogleFonts.playfairDisplay(
        fontWeight: FontWeight.w700,
        color: color,
      ),
      headlineMedium: GoogleFonts.playfairDisplay(
        fontWeight: FontWeight.w600,
        color: color,
      ),
      titleLarge: GoogleFonts.playfairDisplay(
        fontWeight: FontWeight.w600,
        color: color,
      ),
      labelSmall: GoogleFonts.jetBrainsMono(
        fontSize: 10,
        letterSpacing: 2.4,
        fontWeight: FontWeight.w600,
        color: color,
      ),
    );
  }
}
