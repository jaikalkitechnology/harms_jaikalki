import 'package:flutter/material.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../../launch/data/launch_api.dart';
import '../data/polish_api.dart';
import '../data/polish_models.dart';
import '../widgets/asset_widgets.dart';

/// Exit states in which assets are due back.
const _openExitStates = {
  'manager_review', 'accepted', 'in_notice', 'ndc_pending', 'cleared',
};

class _Data {
  const _Data(this.assets, this.categories, this.returnBy);
  final List<Asset> assets;
  final Map<String, AssetCategory> categories;

  /// Last working day when the employee is leaving.
  final String? returnBy;
}

class MyAssetsPage extends StatefulWidget {
  const MyAssetsPage({super.key});

  @override
  State<MyAssetsPage> createState() => _MyAssetsPageState();
}

class _MyAssetsPageState extends State<MyAssetsPage> {
  late Future<_Data> _future = _load();

  Future<_Data> _load() async {
    final api = sl<PolishApi>();
    final assetsF = api.myAssets();
    final categoriesF = api.assetCategories().catchError((_) => <AssetCategory>[]);
    final exitsF = sl<LaunchApi>().myResignations().catchError((_) => <dynamic>[]);
    final assets = await assetsF;
    final categories = {for (final c in await categoriesF) c.code: c};
    String? returnBy;
    for (final raw in await exitsF) {
      final r = raw as Map<String, dynamic>;
      if (_openExitStates.contains(r['status'])) {
        returnBy = (r['actual_last_working_day'] ?? r['proposed_last_working_day']) as String?;
        break;
      }
    }
    return _Data(assets, categories, returnBy);
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My Assets')),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<_Data>(
          future: _future,
          builder: (context, snap) {
            if (snap.hasError) {
              return ListView(
                padding: const EdgeInsets.all(24),
                children: const [
                  SizedBox(height: 80),
                  Text(
                    'Could not load your assets. Pull down to try again.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: AppColors.textMuted),
                  ),
                ],
              );
            }
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final d = snap.data!;
            if (d.assets.isEmpty) return const _Empty();

            final ids = {for (final a in d.assets) a.id};
            // Accessories sit under their main asset when both are here.
            final main = d.assets
                .where((a) => a.parentAssetId == null || !ids.contains(a.parentAssetId))
                .toList();
            List<Asset> accessoriesOf(Asset a) =>
                d.assets.where((x) => x.parentAssetId == a.id).toList();

            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                if (d.returnBy != null) _ReturnBanner(count: d.assets.length, by: d.returnBy!),
                Padding(
                  padding: const EdgeInsets.only(bottom: 8, left: 4),
                  child: Text(
                    '${d.assets.length} item${d.assets.length == 1 ? '' : 's'} assigned to you',
                    style: const TextStyle(color: AppColors.textMuted, fontSize: 13),
                  ),
                ),
                for (final a in main)
                  _AssetCard(
                    asset: a,
                    accessories: accessoriesOf(a),
                    categories: d.categories,
                  ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _Empty extends StatelessWidget {
  const _Empty();

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: const [
        SizedBox(height: 80),
        Icon(Icons.inventory_2_outlined, size: 64, color: AppColors.brandGoldDark),
        SizedBox(height: 12),
        Text(
          'No company assets are assigned to you.',
          textAlign: TextAlign.center,
          style: TextStyle(color: AppColors.textMuted),
        ),
      ],
    );
  }
}

class _ReturnBanner extends StatelessWidget {
  const _ReturnBanner({required this.count, required this.by});
  final int count;
  final String by;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.warning.withOpacity(0.12),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.warning.withOpacity(0.4)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.assignment_return_outlined, color: AppColors.warning),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              'Please hand back ${count == 1 ? 'this asset' : 'these $count assets'} '
              'to HR / IT by ${fmtDay(by)}. Your exit clearance (asset NOC) and '
              'final settlement wait until everything is returned.',
              style: TextStyle(color: context.textPrimary, height: 1.4),
            ),
          ),
        ],
      ),
    );
  }
}

class _AssetCard extends StatelessWidget {
  const _AssetCard({
    required this.asset,
    required this.accessories,
    required this.categories,
  });

  final Asset asset;
  final List<Asset> accessories;
  final Map<String, AssetCategory> categories;

  String _categoryName(String code) =>
      categories[code]?.name ?? code.replaceAll('_', ' ');

  @override
  Widget build(BuildContext context) {
    final a = asset;
    final subtitle = [_categoryName(a.category), a.makeModel]
        .where((s) => s.isNotEmpty)
        .join(' · ');
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () => _showDetails(context),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  CircleAvatar(
                    radius: 22,
                    backgroundColor: AppColors.brandGold.withOpacity(0.15),
                    child: Icon(assetIcon(a.category), color: AppColors.brandGold),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          a.name,
                          style: TextStyle(
                            color: context.textPrimary,
                            fontWeight: FontWeight.w600,
                            fontSize: 15,
                          ),
                        ),
                        Text(subtitle,
                            style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
                        Text(a.assetTag,
                            style: const TextStyle(
                              color: AppColors.textFaint,
                              fontSize: 11,
                              fontFamily: 'JetBrainsMono',
                            )),
                      ],
                    ),
                  ),
                  ConditionChip(a.condition),
                ],
              ),
              if (accessories.isNotEmpty) ...[
                const SizedBox(height: 10),
                for (final x in accessories)
                  Padding(
                    padding: const EdgeInsets.only(left: 56, top: 4),
                    child: Row(
                      children: [
                        Icon(assetIcon(x.category), size: 16, color: AppColors.textMuted),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            '${x.name} · ${x.assetTag}',
                            style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  void _showDetails(BuildContext context) {
    final a = asset;
    final fields = categories[a.category]?.specFields ?? const [];
    final known = {for (final f in fields) f.$1};
    final config = [
      for (final f in fields)
        if ((a.specs[f.$1] ?? '').isNotEmpty) (f.$2, a.specs[f.$1]!),
      for (final e in a.specs.entries)
        if (!known.contains(e.key)) (e.key, e.value),
    ];
    final details = [
      ('Category', _categoryName(a.category)),
      if (a.makeModel.isNotEmpty) ('Make / model', a.makeModel),
      if (a.serialNumber != null) ('Serial number', a.serialNumber!),
      ('Asset tag', a.assetTag),
      ('With you since', fmtDay(a.assignedAt)),
      if (a.warrantyUntil != null) ('Warranty until', fmtDay(a.warrantyUntil)),
    ];

    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (ctx) => SafeArea(
        child: ConstrainedBox(
          constraints: BoxConstraints(maxHeight: MediaQuery.of(ctx).size.height * 0.8),
          child: ListView(
            shrinkWrap: true,
            padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(a.name, style: Theme.of(ctx).textTheme.titleLarge),
                  ),
                  ConditionChip(a.condition),
                ],
              ),
              const SizedBox(height: 16),
              if (config.isNotEmpty) ...[
                const _SheetHeading('CONFIGURATION'),
                for (final r in config) _KV(r.$1, r.$2),
                const SizedBox(height: 12),
              ],
              const _SheetHeading('DETAILS'),
              for (final r in details) _KV(r.$1, r.$2),
              if (accessories.isNotEmpty) ...[
                const SizedBox(height: 12),
                const _SheetHeading('ACCESSORIES'),
                for (final x in accessories) _KV(x.name, x.assetTag),
              ],
              const SizedBox(height: 16),
              const Text(
                'Something wrong with it? Tell HR / IT so it can be repaired '
                'or replaced.',
                style: TextStyle(color: AppColors.textMuted, fontSize: 12),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SheetHeading extends StatelessWidget {
  const _SheetHeading(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(
        text,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: AppColors.brandGoldDark,
            ),
      ),
    );
  }
}

class _KV extends StatelessWidget {
  const _KV(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(
            child: Text(label, style: const TextStyle(color: AppColors.textMuted)),
          ),
          const SizedBox(width: 12),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.right,
              style: TextStyle(color: context.textPrimary, fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }
}
