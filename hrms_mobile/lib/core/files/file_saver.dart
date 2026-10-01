/// Save downloaded bytes and show them to the user, on every platform.
///
/// Mobile / desktop: written to a temp file and opened with the system
/// viewer. Web: handed to the browser as a normal file download (the
/// browser has no file system for `dart:io` or path_provider).
///
/// Returns null on success, or a message to show when it couldn't open.
library;

export 'file_saver_io.dart'
    if (dart.library.js_interop) 'file_saver_web.dart';
