/// Talks to the install-to-home-screen bridge in web/index.html
/// (`window.jkPwa`). Native builds get the stub: the app is already
/// installed there, so nothing is offered.
library;

export 'pwa_bridge_stub.dart'
    if (dart.library.js_interop) 'pwa_bridge_web.dart';
