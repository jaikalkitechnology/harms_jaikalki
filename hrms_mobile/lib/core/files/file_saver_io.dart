import 'dart:io';

import 'package:open_filex/open_filex.dart';
import 'package:path_provider/path_provider.dart';

Future<String?> saveAndOpenBytes(
  List<int> bytes, {
  required String filename,
  String mimeType = 'application/pdf',
}) async {
  final dir = await getTemporaryDirectory();
  final file = File('${dir.path}/$filename');
  await file.writeAsBytes(bytes, flush: true);
  final res = await OpenFilex.open(file.path, type: mimeType);
  return res.type == ResultType.done ? null : res.message;
}
