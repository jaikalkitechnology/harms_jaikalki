import 'dart:js_interop';

@JS('jkPwa')
external _JkPwa? get _jkPwa;

extension type _JkPwa(JSObject _) implements JSObject {
  external String state();
  external JSPromise<JSString> install();
  external set onChange(JSFunction? callback);
}

String pwaState() => _jkPwa?.state() ?? 'unsupported';

Future<String> pwaInstall() async {
  final bridge = _jkPwa;
  if (bridge == null) return 'unavailable';
  return (await bridge.install().toDart).toDart;
}

void pwaOnChange(void Function() callback) {
  _jkPwa?.onChange = callback.toJS;
}
