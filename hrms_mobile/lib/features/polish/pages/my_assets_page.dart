import 'package:flutter/material.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/polish_api.dart';
import '../data/polish_models.dart';

class MyAssetsPage extends StatefulWidget {
  const MyAssetsPage({super.key});

  @override
  State<MyAssetsPage> createState() => _MyAssetsPageState();
}

class _MyAssetsPageState extends State<MyAssetsPage> {
  late Future<List<Asset>> _future;

  @override
  void initState() {
    super.initState();
    _future = sl<PolishApi>().myAssets();
  }

  IconData _iconFor(String c) {
    switch (c) {
      case 'laptop':
        return Icons.laptop_mac;
      case 'mobile':
        return Icons.phone_iphone;
      case 'headset':
        return Icons.headset_mic;
      case 'monitor':
        return Icons.tv;
      case 'vehicle':
        return Icons.two_wheeler;
      default:
        return Icons.devices_other;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('My Assets')),
      body: FutureBuilder<List<Asset>>(
        future: _future,
        builder: (context, snap) {
          if (!snap.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final assets = snap.data!;
          if (assets.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.inventory_2_outlined,
                        size: 64, color: AppColors.brandGoldDark),
                    const SizedBox(height: 12),
                    Text(
                      'No assets assigned to you.',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: AppColors.textMuted,
                      ),
                    ),
                  ],
                ),
              ),
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: assets.length,
            itemBuilder: (context, i) {
              final a = assets[i];
              return Card(
                margin: const EdgeInsets.only(bottom: 12),
                child: ListTile(
                  leading: CircleAvatar(
                    backgroundColor: AppColors.brandGoldPale,
                    child: Icon(_iconFor(a.category),
                        color: AppColors.brandGoldDark),
                  ),
                  title: Text(a.name),
                  subtitle: Text(
                    '${a.assetTag} · ${a.category} · ${a.condition}',
                    style: theme.textTheme.bodySmall,
                  ),
                  trailing: Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: AppColors.success.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Text(
                      'ASSIGNED',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        color: AppColors.success,
                      ),
                    ),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
