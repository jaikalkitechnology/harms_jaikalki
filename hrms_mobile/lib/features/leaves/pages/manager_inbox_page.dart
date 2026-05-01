import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../../employees/cubit/employees_cubit.dart' show LoadStatus;
import '../cubit/leaves_cubit.dart';
import '../data/leave_api.dart';
import '../data/leave_models.dart';

class ManagerInboxPage extends StatelessWidget {
  const ManagerInboxPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => PendingApprovalsCubit(sl<LeaveApi>())..load(),
      child: const _InboxView(),
    );
  }
}

class _InboxView extends StatelessWidget {
  const _InboxView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Pending approvals')),
      body: BlocBuilder<PendingApprovalsCubit, PendingApprovalsState>(
        builder: (context, state) {
          if (state.status == LoadStatus.loading && state.items.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state.items.isEmpty) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text('All caught up'),
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: () => context.read<PendingApprovalsCubit>().load(),
            child: ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: state.items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (_, i) => _ApprovalCard(request: state.items[i]),
            ),
          );
        },
      ),
    );
  }
}

class _ApprovalCard extends StatelessWidget {
  const _ApprovalCard({required this.request});
  final LeaveRequest request;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final cubit = context.read<PendingApprovalsCubit>();
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${request.leaveType?.name ?? 'Leave'} · ${request.days} day'
              '${request.days != 1 ? 's' : ''}',
              style: theme.textTheme.titleMedium,
            ),
            const SizedBox(height: 4),
            Text(
              'Employee #${request.employeeId} · ${request.fromDate} → ${request.toDate}',
              style: theme.textTheme.bodySmall?.copyWith(
                color: AppColors.brandBrownLight,
              ),
            ),
            if (request.reason != null) ...[
              const SizedBox(height: 6),
              Text(request.reason!, style: theme.textTheme.bodyMedium),
            ],
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: FilledButton.icon(
                    onPressed: () => cubit.approve(request.id),
                    icon: const Icon(Icons.check, size: 18),
                    label: const Text('Approve'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: () => cubit.reject(request.id),
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
