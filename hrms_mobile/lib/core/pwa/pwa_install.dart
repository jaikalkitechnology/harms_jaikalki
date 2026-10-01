import 'package:flutter/foundation.dart';

import 'pwa_bridge.dart';

/// How the web app can be added to this device's home screen.
enum PwaInstallMode {
  /// Native app, or a browser that can't install web apps.
  unavailable,

  /// Already running as an installed app.
  installed,

  /// The browser's own install dialog is ready (Chrome, Edge, Samsung).
  prompt,

  /// iPhone / iPad: Share → Add to Home Screen.
  ios,

  /// Android browser without a ready dialog: menu → Install / Add to Home.
  android,

  /// Safari on a Mac: File → Add to Dock.
  macSafari,
}

class PwaInstall extends ChangeNotifier {
  PwaInstall._() {
    pwaOnChange(notifyListeners);
  }

  static final PwaInstall instance = PwaInstall._();

  PwaInstallMode get mode => switch (pwaState()) {
        'installed' => PwaInstallMode.installed,
        'prompt' => PwaInstallMode.prompt,
        'ios' => PwaInstallMode.ios,
        'android' => PwaInstallMode.android,
        'mac-safari' => PwaInstallMode.macSafari,
        _ => PwaInstallMode.unavailable,
      };

  /// Something can be offered to the user on this device.
  bool get canOffer =>
      mode != PwaInstallMode.unavailable && mode != PwaInstallMode.installed;

  /// Shows the browser's install dialog; true when the user accepted.
  Future<bool> promptInstall() async => (await pwaInstall()) == 'accepted';
}
