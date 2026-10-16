import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import 'package:share_plus/share_plus.dart';

import '../../../core/di/injection.dart';
import '../../../core/files/file_saver.dart';
import '../../../core/routing/app_router.dart';
import '../../../core/theme/app_colors.dart';
import '../data/documents_api.dart';

String _fmtDay(String? iso) {
  final d = iso == null ? null : DateTime.tryParse(iso);
  return d == null ? '' : DateFormat('d MMM yyyy').format(d);
}

/// More → Documents: the employee's letters (offer, appointment,
/// confirmation …) and the company policies HR has published.
class DocumentsPage extends StatelessWidget {
  const DocumentsPage({super.key, this.initialTab = 0});

  /// 0 = My letters, 1 = Policies.
  final int initialTab;

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      initialIndex: initialTab,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Documents'),
          actions: [
            IconButton(
              tooltip: 'My certificates',
              icon: const Icon(Icons.workspace_premium_outlined),
              onPressed: () => context.push(AppRoutes.myCertificates),
            ),
          ],
          bottom: const TabBar(
            tabs: [
              Tab(text: 'My letters'),
              Tab(text: 'Policies'),
            ],
          ),
        ),
        body: const TabBarView(
          children: [_LettersTab(), _PoliciesTab()],
        ),
      ),
    );
  }
}

/// Download + open (or share) a document, with a busy flag per item.
mixin _FileActions<T extends StatefulWidget> on State<T> {
  final Set<int> busy = {};

  void toast(String msg, {bool error = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: error ? AppColors.error : AppColors.success,
      ),
    );
  }

  Future<void> download(
    int id,
    Future<List<int>> Function() fetch, {
    required String filename,
    required String mimeType,
  }) async {
    setState(() => busy.add(id));
    try {
      final bytes = await fetch();
      final problem = await saveAndOpenBytes(bytes, filename: filename, mimeType: mimeType);
      toast(problem ?? 'Downloaded $filename', error: problem != null);
    } catch (_) {
      toast('Could not download. Check your connection and try again.', error: true);
    } finally {
      if (mounted) setState(() => busy.remove(id));
    }
  }

  Future<void> share(
    int id,
    Future<List<int>> Function() fetch, {
    required String filename,
    required String mimeType,
    required String title,
  }) async {
    setState(() => busy.add(id));
    try {
      final bytes = await fetch();
      await Share.shareXFiles(
        [XFile.fromData(Uint8List.fromList(bytes), name: filename, mimeType: mimeType)],
        subject: title,
      );
    } catch (_) {
      toast('Could not share this file.', error: true);
    } finally {
      if (mounted) setState(() => busy.remove(id));
    }
  }
}

// ── My letters ───────────────────────────────────────────────────────
class _LettersTab extends StatefulWidget {
  const _LettersTab();

  @override
  State<_LettersTab> createState() => _LettersTabState();
}

class _LettersTabState extends State<_LettersTab> with _FileActions {
  late Future<List<EmployeeLetter>> _future = sl<DocumentsApi>().myLetters();

  Future<void> _refresh() async {
    setState(() => _future = sl<DocumentsApi>().myLetters());
    await _future;
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _refresh,
      child: FutureBuilder<List<EmployeeLetter>>(
        future: _future,
        builder: (context, snap) {
          if (snap.hasError) {
            return const _Message(
              icon: Icons.cloud_off_outlined,
              text: 'Could not load your letters. Pull down to try again.',
            );
          }
          if (!snap.hasData) return const Center(child: CircularProgressIndicator());
          final letters = snap.data!;
          if (letters.isEmpty) {
            return const _Message(
              icon: Icons.mail_outline,
              text: 'No letters yet.\nYour offer, appointment and confirmation '
                  'letters appear here once HR issues them.',
            );
          }
          final api = sl<DocumentsApi>();
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: letters.length,
            itemBuilder: (_, i) {
              final l = letters[i];
              return _DocCard(
                icon: Icons.description_outlined,
                title: l.title,
                tag: l.typeLabel.toLowerCase() == l.title.toLowerCase()
                    ? null
                    : l.typeLabel,
                meta: [l.letterNumber, _fmtDay(l.issuedOn)]
                    .whereType<String>()
                    .where((s) => s.isNotEmpty)
                    .join(' · '),
                busy: busy.contains(l.id),
                onDownload: () => download(l.id, () => api.letterFile(l.id),
                    filename: l.fileName, mimeType: l.mimeType),
                onShare: () => share(l.id, () => api.letterFile(l.id),
                    filename: l.fileName, mimeType: l.mimeType, title: l.title),
              );
            },
          );
        },
      ),
    );
  }
}

// ── Policies ─────────────────────────────────────────────────────────
class _PoliciesTab extends StatefulWidget {
  const _PoliciesTab();

  @override
  State<_PoliciesTab> createState() => _PoliciesTabState();
}

class _PoliciesTabState extends State<_PoliciesTab> with _FileActions {
  late Future<List<CompanyPolicy>> _future = sl<DocumentsApi>().policies();

  Future<void> _refresh() async {
    setState(() => _future = sl<DocumentsApi>().policies());
    await _future;
  }

  Future<void> _accept(CompanyPolicy p) async {
    final api = sl<DocumentsApi>();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(p.title),
        content: const Text(
          'Please open and read the policy before accepting it.\n\n'
          'By tapping “I accept” you confirm that you have read and '
          'understood it and will follow it.',
        ),
        actions: [
          TextButton(
            onPressed: () {
              download(p.id, () => api.policyFile(p.id),
                  filename: p.fileName, mimeType: p.mimeType);
            },
            child: const Text('Open policy'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('I accept'),
          ),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    setState(() => busy.add(p.id));
    try {
      await api.acknowledgePolicy(p.id);
      toast('Thank you — you have accepted ${p.title}.');
      await _refresh();
    } catch (_) {
      toast('Could not record your acceptance. Please try again.', error: true);
    } finally {
      if (mounted) setState(() => busy.remove(p.id));
    }
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _refresh,
      child: FutureBuilder<List<CompanyPolicy>>(
        future: _future,
        builder: (context, snap) {
          if (snap.hasError) {
            return const _Message(
              icon: Icons.cloud_off_outlined,
              text: 'Could not load the policies. Pull down to try again.',
            );
          }
          if (!snap.hasData) return const Center(child: CircularProgressIndicator());
          final policies = snap.data!;
          if (policies.isEmpty) {
            return const _Message(
              icon: Icons.policy_outlined,
              text: 'No company policies have been published yet.',
            );
          }
          final api = sl<DocumentsApi>();
          final toAccept = policies.where((p) => p.needsMyAcceptance).length;
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: policies.length + (toAccept > 0 ? 1 : 0),
            itemBuilder: (_, index) {
              if (toAccept > 0 && index == 0) return _AcceptBanner(count: toAccept);
              final p = policies[index - (toAccept > 0 ? 1 : 0)];
              final effective = _fmtDay(p.effectiveDate);
              return _DocCard(
                icon: Icons.policy_outlined,
                title: p.title,
                tag: p.categoryLabel,
                meta: [
                  if (p.version != null && p.version!.isNotEmpty) p.version!,
                  if (effective.isNotEmpty) 'Effective $effective',
                ].join(' · '),
                description: p.description,
                busy: busy.contains(p.id),
                onDownload: () => download(p.id, () => api.policyFile(p.id),
                    filename: p.fileName, mimeType: p.mimeType),
                onShare: () => share(p.id, () => api.policyFile(p.id),
                    filename: p.fileName, mimeType: p.mimeType, title: p.title),
                footer: !p.requiresAcknowledgement
                    ? null
                    : p.myAcknowledgedAt != null
                        ? Row(
                            children: [
                              const Icon(Icons.verified_outlined,
                                  size: 16, color: AppColors.successText),
                              const SizedBox(width: 6),
                              Text(
                                'Accepted on ${_fmtDay(p.myAcknowledgedAt)}',
                                style: const TextStyle(
                                    color: AppColors.successText, fontSize: 12),
                              ),
                            ],
                          )
                        : FilledButton.tonalIcon(
                            onPressed: busy.contains(p.id) ? null : () => _accept(p),
                            icon: const Icon(Icons.task_alt, size: 18),
                            label: const Text('Read & accept'),
                          ),
              );
            },
          );
        },
      ),
    );
  }
}

// ── Shared widgets ───────────────────────────────────────────────────
class _DocCard extends StatelessWidget {
  const _DocCard({
    required this.icon,
    required this.title,
    required this.meta,
    required this.busy,
    required this.onDownload,
    required this.onShare,
    this.tag,
    this.description,
    this.footer,
  });

  final IconData icon;
  final String title;
  final String? tag;
  final String meta;
  final String? description;
  final Widget? footer;
  final bool busy;
  final VoidCallback onDownload;
  final VoidCallback onShare;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: busy ? null : onDownload,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(14, 14, 6, 14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CircleAvatar(
                radius: 22,
                backgroundColor: AppColors.brandGold.withOpacity(0.15),
                child: Icon(icon, color: AppColors.brandGold),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: TextStyle(
                        color: context.textPrimary,
                        fontWeight: FontWeight.w600,
                        fontSize: 15,
                      ),
                    ),
                    if (tag != null) ...[
                      const SizedBox(height: 4),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: AppColors.brandGold.withOpacity(0.15),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Text(
                          tag!,
                          style: const TextStyle(
                            color: AppColors.brandGold,
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                    if (meta.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(meta, style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
                    ],
                    if (description != null && description!.trim().isNotEmpty) ...[
                      const SizedBox(height: 6),
                      Text(
                        description!.trim(),
                        maxLines: 3,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(color: AppColors.textMuted, fontSize: 13, height: 1.35),
                      ),
                    ],
                    if (footer != null) ...[
                      const SizedBox(height: 10),
                      footer!,
                    ],
                  ],
                ),
              ),
              if (busy)
                const Padding(
                  padding: EdgeInsets.all(12),
                  child: SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
                )
              else ...[
                IconButton(
                  tooltip: 'Download',
                  icon: const Icon(Icons.download_outlined),
                  color: AppColors.brandGold,
                  onPressed: onDownload,
                ),
                IconButton(
                  tooltip: 'Share',
                  icon: const Icon(Icons.share_outlined),
                  color: AppColors.textMuted,
                  onPressed: onShare,
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _AcceptBanner extends StatelessWidget {
  const _AcceptBanner({required this.count});
  final int count;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.warning.withOpacity(0.12),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.warning.withOpacity(0.4)),
      ),
      child: Row(
        children: [
          const Icon(Icons.pending_actions_outlined, color: AppColors.warning),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              count == 1
                  ? '1 policy needs your acceptance. Read it, then tap “Read & accept”.'
                  : '$count policies need your acceptance. Read each one, then tap “Read & accept”.',
              style: TextStyle(color: context.textPrimary, height: 1.4),
            ),
          ),
        ],
      ),
    );
  }
}

class _Message extends StatelessWidget {
  const _Message({required this.icon, required this.text});
  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    // A ListView so pull-to-refresh still works on an empty page.
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        const SizedBox(height: 80),
        Icon(icon, size: 64, color: AppColors.brandGoldDark),
        const SizedBox(height: 12),
        Text(
          text,
          textAlign: TextAlign.center,
          style: const TextStyle(color: AppColors.textMuted, height: 1.4),
        ),
      ],
    );
  }
}
