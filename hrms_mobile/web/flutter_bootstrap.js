{{flutter_js}}
{{flutter_build_config}}

// No serviceWorkerSettings: Flutter's own service worker is deprecated
// (a stub that unregisters itself), and the default loader would swap it
// in over the app's sw.js on every visit. sw.js is registered in
// index.html instead.
_flutter.loader.load();
