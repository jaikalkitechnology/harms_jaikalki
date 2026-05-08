import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/sales_api.dart';
import '../data/sales_models.dart';

const _stages = [
  'new',
  'contacted',
  'qualified',
  'proposal',
  'negotiation',
  'won',
  'lost',
];

class LeadDetailPage extends StatefulWidget {
  const LeadDetailPage({super.key, required this.leadId});
  final int leadId;

  @override
  State<LeadDetailPage> createState() => _LeadDetailPageState();
}

class _LeadDetailPageState extends State<LeadDetailPage> {
  Lead? _lead;
  List<LeadActivity> _activities = const [];
  bool _busy = false;
  final _commentCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _commentCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _busy = true);
    try {
      final api = sl<SalesApi>();
      final list = await api.myLeads();
      final lead = list.firstWhere(
        (e) => e.id == widget.leadId,
        orElse: () => list.isEmpty
            ? throw StateError('Lead not found')
            : list.first,
      );
      final acts = await api.leadActivities(widget.leadId);
      if (!mounted) return;
      setState(() {
        _lead = lead;
        _activities = acts;
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not load lead: $e')),
      );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _changeStage(String newStage) async {
    if (_lead == null) return;
    if (_lead!.stage == newStage && newStage != 'won') return;
    String? reason;
    if (newStage == 'lost') {
      reason = await _askReason();
      if (reason == null || reason.trim().isEmpty) return;
    }
    if (newStage == 'won' && _lead!.wonApprovalStatus != 'pending') {
      final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Submit for admin approval?'),
          content: const Text(
            'Marking this lead as Won will send it to admin for approval. '
            'It will count toward your target only after approval.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Submit'),
            ),
          ],
        ),
      );
      if (ok != true) return;
    }
    setState(() => _busy = true);
    try {
      final updated = await sl<SalesApi>().updateStage(
        _lead!.id,
        newStage,
        lostReason: reason,
      );
      if (!mounted) return;
      setState(() => _lead = updated);
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not change stage: $e')),
      );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<String?> _askReason() async {
    final ctrl = TextEditingController();
    return showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Why was it lost?'),
        content: TextField(
          controller: ctrl,
          decoration: const InputDecoration(
            hintText: 'Pricing, competitor, no need…',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, ctrl.text),
            child: const Text('Mark lost'),
          ),
        ],
      ),
    );
  }

  Future<void> _submitComment() async {
    final text = _commentCtrl.text.trim();
    if (text.isEmpty) return;
    setState(() => _busy = true);
    try {
      await sl<SalesApi>().addLeadComment(widget.leadId, text);
      _commentCtrl.clear();
      await _load();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not post comment: $e')),
      );
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _call() async {
    final phone = _lead?.contactPhone;
    if (phone == null || phone.isEmpty) return;
    final uri = Uri.parse('tel:$phone');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final lead = _lead;
    return Scaffold(
      appBar: AppBar(
        title: Text(lead?.contactName ?? 'Lead'),
      ),
      body: lead == null
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _load,
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _Header(lead: lead, onCall: _call),
                  if (_WonStatusBanner.shouldShow(lead)) ...[
                    const SizedBox(height: 12),
                    _WonStatusBanner(lead: lead),
                  ],
                  const SizedBox(height: 16),
                  _StageStepper(
                    current: lead.stage,
                    onChanged: _busy ? null : _changeStage,
                  ),
                  const SizedBox(height: 16),
                  Text('Pipeline activity', style: theme.textTheme.titleSmall),
                  const SizedBox(height: 8),
                  if (_activities.isEmpty)
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Text(
                          'No comments or stage changes yet.',
                          style: TextStyle(
                            color: AppColors.brandBrownLight,
                          ),
                        ),
                      ),
                    )
                  else
                    ..._activities.map(_activityTile),
                  const SizedBox(height: 12),
                  _CommentBox(
                    controller: _commentCtrl,
                    onSubmit: _busy ? null : _submitComment,
                  ),
                ],
              ),
            ),
    );
  }

  Widget _activityTile(LeadActivity a) {
    final theme = Theme.of(context);
    IconData icon;
    Color color;
    String title;
    String? subtitle = a.body;
    switch (a.activityType) {
      case 'stage_change':
        icon = Icons.timeline;
        color = AppColors.info;
        title = 'Stage: ${a.fromStage ?? "—"} → ${a.toStage ?? "—"}';
        break;
      case 'assignment':
        icon = Icons.person_add_alt;
        color = AppColors.brandGoldDark;
        title = a.body ?? 'Assignment changed';
        subtitle = null;
        break;
      case 'system':
        icon = Icons.info_outline;
        color = AppColors.brandBrownLight;
        title = a.body ?? 'System note';
        subtitle = null;
        break;
      default:
        icon = Icons.chat_bubble_outline;
        color = AppColors.brandGoldDark;
        title = a.actorLabel ?? 'Comment';
    }
    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: color.withOpacity(0.15),
          child: Icon(icon, color: color, size: 18),
        ),
        title: Text(title),
        subtitle: subtitle != null
            ? Padding(
                padding: const EdgeInsets.only(top: 4),
                child: Text(
                  subtitle,
                  style: theme.textTheme.bodySmall,
                ),
              )
            : null,
        trailing: Text(
          a.createdAt.split('T').first,
          style: theme.textTheme.bodySmall?.copyWith(
            color: AppColors.brandBrownLight,
          ),
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.lead, required this.onCall});
  final Lead lead;
  final VoidCallback onCall;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              lead.contactName ?? 'Lead #${lead.id}',
              style: theme.textTheme.titleLarge,
            ),
            if (lead.contactEmail != null) ...[
              const SizedBox(height: 4),
              Text(lead.contactEmail!, style: theme.textTheme.bodySmall),
            ],
            const SizedBox(height: 12),
            Row(
              children: [
                Icon(Icons.currency_rupee,
                    size: 16, color: AppColors.brandGoldDark),
                Text(
                  lead.expectedValue.toStringAsFixed(0),
                  style: theme.textTheme.titleMedium,
                ),
                const SizedBox(width: 16),
                Icon(Icons.source,
                    size: 16, color: AppColors.brandBrownLight),
                const SizedBox(width: 4),
                Text(lead.source.replaceAll('_', ' ')),
              ],
            ),
            if (lead.contactPhone != null) ...[
              const SizedBox(height: 12),
              FilledButton.tonalIcon(
                onPressed: onCall,
                icon: const Icon(Icons.call),
                label: Text(lead.contactPhone!),
              ),
            ],
            if (lead.notes != null && lead.notes!.isNotEmpty) ...[
              const SizedBox(height: 12),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.brandGoldDark.withOpacity(0.06),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(lead.notes!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _WonStatusBanner extends StatelessWidget {
  const _WonStatusBanner({required this.lead});
  final Lead lead;

  static bool shouldShow(Lead lead) =>
      lead.stage == 'won' || lead.wonApprovalStatus == 'rejected';

  @override
  Widget build(BuildContext context) {
    final status = lead.wonApprovalStatus;
    Color color;
    IconData icon;
    String title;
    String? subtitle;

    if (status == 'pending') {
      color = AppColors.warning;
      icon = Icons.hourglass_top;
      title = 'Pending from admin';
      subtitle = 'Submitted for approval. It will count toward your target only after approval.';
    } else if (status == 'rejected') {
      color = AppColors.error;
      icon = Icons.cancel;
      title = 'Rejected by admin';
      subtitle = lead.wonRejectionReason ??
          'Admin sent this back to negotiation.';
    } else {
      // approved or null/legacy: only show if stage=won.
      if (lead.stage != 'won') return const SizedBox.shrink();
      color = AppColors.success;
      icon = Icons.check_circle;
      title = 'Won';
      subtitle = 'Approved — counted toward your target.';
    }

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.10),
        border: Border.all(color: color.withOpacity(0.4)),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    color: color,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                if (subtitle != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: TextStyle(
                      color: AppColors.brandBrownLight,
                      fontSize: 12,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _StageStepper extends StatelessWidget {
  const _StageStepper({
    required this.current,
    required this.onChanged,
  });
  final String current;
  final ValueChanged<String>? onChanged;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final idx = _stages.indexOf(current);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Pipeline progress', style: theme.textTheme.titleSmall),
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: _stages.map((s) {
                final i = _stages.indexOf(s);
                final reached = i <= idx && idx >= 0;
                final isCurrent = s == current;
                return ChoiceChip(
                  label: Text(s.replaceAll('_', ' ')),
                  selected: reached,
                  onSelected: onChanged == null
                      ? null
                      : (_) => onChanged!(s),
                  selectedColor:
                      AppColors.brandGoldDark.withOpacity(0.18),
                  labelStyle: TextStyle(
                    color: isCurrent
                        ? AppColors.brandGoldDark
                        : (reached
                            ? context.textPrimary
                            : AppColors.brandBrownLight),
                    fontWeight: isCurrent ? FontWeight.w600 : FontWeight.w400,
                  ),
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }
}

class _CommentBox extends StatelessWidget {
  const _CommentBox({required this.controller, required this.onSubmit});
  final TextEditingController controller;
  final VoidCallback? onSubmit;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            TextField(
              controller: controller,
              maxLines: 3,
              decoration: const InputDecoration(
                hintText: 'Add a comment for the team…',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),
            FilledButton.icon(
              onPressed: onSubmit,
              icon: const Icon(Icons.send),
              label: const Text('Post comment'),
            ),
          ],
        ),
      ),
    );
  }
}
