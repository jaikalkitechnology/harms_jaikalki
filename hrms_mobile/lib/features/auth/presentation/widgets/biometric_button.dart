import 'package:flutter/material.dart';

import '../../../../core/theme/app_colors.dart';

class BiometricButton extends StatelessWidget {
  const BiometricButton({super.key, required this.onPressed});

  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: onPressed,
      icon: const Icon(Icons.fingerprint, size: 20),
      label: const Text('Use biometrics'),
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.brandBrown,
        side: const BorderSide(color: AppColors.brandBrown100),
        padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }
}
