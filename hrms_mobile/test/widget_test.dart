import 'package:flutter_test/flutter_test.dart';

import 'package:hrms_mobile/core/theme/app_colors.dart';

void main() {
  test('Brand colors are stable', () {
    // Sanity check for brand tokens — values are the contract shared
    // with the React admin and the design-system HTML.
    expect(AppColors.brandBrown.value, 0xFF3D2817);
    expect(AppColors.brandGold.value, 0xFFF4B71F);
    expect(AppColors.cream.value, 0xFFFDF8EE);
  });
}
