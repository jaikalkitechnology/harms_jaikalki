import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/justice_api.dart';
import '../data/justice_models.dart';

class JusticeResourcesPage extends StatefulWidget {
  const JusticeResourcesPage({super.key});

  @override
  State<JusticeResourcesPage> createState() => _JusticeResourcesPageState();
}

class _JusticeResourcesPageState extends State<JusticeResourcesPage> {
  late Future<Resources> _future;

  @override
  void initState() {
    super.initState();
    _future = sl<JusticeApi>().resources();
  }

  Future<void> _dial(String number) async {
    final uri = Uri(scheme: 'tel', path: number);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }

  Future<void> _open(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Resources')),
      body: FutureBuilder<Resources>(
        future: _future,
        builder: (context, snap) {
          if (!snap.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final r = snap.data!;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text('★ HELPLINES',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: AppColors.brandGoldDark,
                  )),
              const SizedBox(height: 8),
              ...r.helplines.map(
                (h) => Card(
                  child: ListTile(
                    leading: const Icon(Icons.phone,
                        color: AppColors.brandGoldDark),
                    title: Text(h.name),
                    subtitle: Text(h.number),
                    trailing: const Icon(Icons.call,
                        color: AppColors.success),
                    onTap: () => _dial(h.number),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Text('★ POLICIES',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: AppColors.brandGoldDark,
                  )),
              const SizedBox(height: 8),
              ...r.policies.map(
                (p) => Card(
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(p.title, style: theme.textTheme.titleMedium),
                        const SizedBox(height: 6),
                        Text(p.summary,
                            style: theme.textTheme.bodyMedium?.copyWith(
                              color: AppColors.textMuted,
                            )),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              if (r.externalResources.isNotEmpty) ...[
                Text('★ EXTERNAL',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: AppColors.brandGoldDark,
                    )),
                const SizedBox(height: 8),
                ...r.externalResources.map(
                  (e) => Card(
                    child: ListTile(
                      leading: const Icon(Icons.open_in_new,
                          color: AppColors.brandGoldDark),
                      title: Text(e.name),
                      subtitle: Text(
                        e.url,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                      onTap: () => _open(e.url),
                    ),
                  ),
                ),
              ],
            ],
          );
        },
      ),
    );
  }
}
