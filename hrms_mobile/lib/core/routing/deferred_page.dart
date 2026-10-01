import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

/// Shows a page from a `deferred as` import, loading its code first.
///
/// On the web each deferred import is a separate download fetched the
/// first time the page opens, which keeps rarely used modules out of the
/// start-up bundle. On Android / iOS `loadLibrary()` completes at once.
class DeferredPage extends StatefulWidget {
  const DeferredPage(this.loadLibrary, this.builder, {super.key});

  final Future<void> Function() loadLibrary;
  final WidgetBuilder builder;

  @override
  State<DeferredPage> createState() => _DeferredPageState();
}

class _DeferredPageState extends State<DeferredPage> {
  late Future<void> _loading = widget.loadLibrary();

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<void>(
      future: _loading,
      builder: (context, snap) {
        if (snap.connectionState == ConnectionState.done && !snap.hasError) {
          return widget.builder(context);
        }
        return Scaffold(
          appBar: AppBar(),
          body: Center(
            child: snap.hasError
                ? Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Text(
                        'Could not load this section.',
                        style: TextStyle(color: AppColors.textMuted),
                      ),
                      const SizedBox(height: 12),
                      FilledButton(
                        onPressed: () =>
                            setState(() => _loading = widget.loadLibrary()),
                        child: const Text('Try again'),
                      ),
                    ],
                  )
                : const CircularProgressIndicator(),
          ),
        );
      },
    );
  }
}
