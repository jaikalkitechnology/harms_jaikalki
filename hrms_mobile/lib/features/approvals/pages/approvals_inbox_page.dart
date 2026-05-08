import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../../employees/cubit/employees_cubit.dart' show LoadStatus;
import '../cubit/approvals_inbox_cubit.dart';
import '../data/approval_api.dart';
import '../data/approval_models.dart';

class ApprovalsInboxPage extends StatelessWidget {
  const ApprovalsInboxPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => ApprovalsInboxCubit(sl<ApprovalApi>())..load(),
      child: const _InboxView(),
    );
  }
}

class _InboxView extends StatelessWidget {
  const _InboxView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Approvals')),
      body: BlocConsumer<ApprovalsInboxCubit, ApprovalsInboxState>(
        listener: (context, state) {
          if (state.error != null) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.error!)),
            );
          }
        },
        builder: (context, state) {
          if (state.status == LoadStatus.loading && state.items.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }
          return Column(
            children: [
              _Filters(state: state),
              Expanded(
                child: state.items.isEmpty
                    ? const Center(
                        child: Padding(
                          padding: EdgeInsets.all(24),
                          child: Text('All caught up'),
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: () =>
                            context.read<ApprovalsInboxCubit>().load(),
                        child: ListView.separated(
                          padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                          itemCount: state.items.length,
                          separatorBuilder: (_, __) =>
                              const SizedBox(height: 8),
                          itemBuilder: (_, i) =>
                              _ApprovalCard(approval: state.items[i]),
                        ),
                      ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _Filters extends StatelessWidget {
  const _Filters({required this.state});
  final ApprovalsInboxState state;

  @override
  Widget build(BuildContext context) {
    final cubit = context.read<ApprovalsInboxCubit>();
    final total = state.counts.fold<int>(0, (acc, c) => acc + c.count);
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 12, 12, 4),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            _Pill(
              label: 'All · $total',
              active: state.filter == null,
              onTap: () => cubit.load(clearFilter: true),
            ),
            const SizedBox(width: 6),
            ...state.counts.map(
              (c) => Padding(
                padding: const EdgeInsets.only(right: 6),
                child: _Pill(
                  label:
                      '${approvalTypeLabel[c.requestType] ?? c.requestType} · ${c.count}',
                  active: state.filter == c.requestType,
                  onTap: () => cubit.load(filter: c.requestType),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill({required this.label, required this.active, required this.onTap});
  final String label;
  final bool active;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(99),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: active
              ? AppColors.brandGold.withOpacity(0.18)
              : AppColors.brandBrown50,
          borderRadius: BorderRadius.circular(99),
          border: Border.all(
            color: active
                ? AppColors.brandGoldDark.withOpacity(0.5)
                : AppColors.brandBrown100,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 11,
            fontFamily: 'monospace',
            letterSpacing: 1.5,
            fontWeight: FontWeight.w600,
            color: active
                ? context.textPrimary
                : AppColors.brandBrownLight,
          ),
        ),
      ),
    );
  }
}

class _ApprovalCard extends StatelessWidget {
  const _ApprovalCard({required this.approval});
  final ApprovalItem approval;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final cubit = context.read<ApprovalsInboxCubit>();
    final type = approvalTypeLabel[approval.requestType] ?? approval.requestType;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    approval.title,
                    style: theme.textTheme.titleMedium,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppColors.brandGold.withOpacity(0.18),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    type.toUpperCase(),
                    style: const TextStyle(
                      fontSize: 10,
                      fontFamily: 'monospace',
                      letterSpacing: 1.5,
                      fontWeight: FontWeight.w700,
                      color: AppColors.brandGoldDark,
                    ),
                  ),
                ),
              ],
            ),
            if (approval.summary != null) ...[
              const SizedBox(height: 6),
              Text(approval.summary!,
                  style: theme.textTheme.bodyMedium,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis),
            ],
            const SizedBox(height: 8),
            _DataRows(approval: approval),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: FilledButton.icon(
                    onPressed: () => cubit.approve(approval.id),
                    icon: const Icon(Icons.check, size: 18),
                    label: const Text('Approve'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => cubit.reject(approval.id),
                    icon: const Icon(Icons.close, size: 18),
                    label: const Text('Reject'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _DataRows extends StatelessWidget {
  const _DataRows({required this.approval});
  final ApprovalItem approval;

  @override
  Widget build(BuildContext context) {
    final d = approval.requestData;
    final rows = <(String, String)>[];
    switch (approval.requestType) {
      case 'leave_request':
        rows.add(('Type', '${d['leave_type_code'] ?? '—'}'));
        rows.add(('Dates', '${d['from_date']} → ${d['to_date']}'));
        rows.add((
          'Days',
          '${d['days']}${d['half_day'] == true ? ' (half)' : ''}',
        ));
        break;
      case 'attendance_regularization':
        rows.add(('Date', '${d['date'] ?? '—'}'));
        if (d['requested_check_in'] != null) {
          rows.add(('Check-in', '${d['requested_check_in']}'));
        }
        if (d['requested_check_out'] != null) {
          rows.add(('Check-out', '${d['requested_check_out']}'));
        }
        break;
      case 'intern_expense':
        rows.add(('Amount', '₹${d['amount']}'));
        rows.add(('Date', '${d['expense_date'] ?? '—'}'));
        rows.add(('Type', '${d['expense_type'] ?? '—'}'));
        break;
    }
    return Column(
      children: rows
          .map(
            (r) => Padding(
              padding: const EdgeInsets.symmetric(vertical: 2),
              child: Row(
                children: [
                  SizedBox(
                    width: 90,
                    child: Text(
                      r.$1.toUpperCase(),
                      style: const TextStyle(
                        fontSize: 10,
                        fontFamily: 'monospace',
                        letterSpacing: 1.5,
                        color: AppColors.brandBrownLight,
                      ),
                    ),
                  ),
                  Expanded(
                    child: Text(r.$2,
                        style: const TextStyle(
                          color: context.textPrimary,
                        )),
                  ),
                ],
              ),
            ),
          )
          .toList(),
    );
  }
}
