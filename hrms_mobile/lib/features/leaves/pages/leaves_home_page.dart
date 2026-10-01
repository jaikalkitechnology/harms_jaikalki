import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../../employees/cubit/employees_cubit.dart' show LoadStatus;
import '../cubit/leaves_cubit.dart';
import '../data/leave_api.dart';
import '../data/leave_models.dart';

class LeavesHomePage extends StatelessWidget {
  const LeavesHomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => LeavesCubit(sl<LeaveApi>())..load(),
      child: const _LeavesView(),
    );
  }
}

class _LeavesView extends StatelessWidget {
  const _LeavesView();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Leaves')),
      floatingActionButton: BlocBuilder<LeavesCubit, LeavesState>(
        builder: (context, state) => FloatingActionButton.extended(
          onPressed: state.types.isEmpty ? null : () => _openApplySheet(context),
          backgroundColor: AppColors.brandGoldDark,
          foregroundColor: Colors.white,
          icon: const Icon(Icons.add),
          label: const Text('Apply'),
        ),
      ),
      body: BlocConsumer<LeavesCubit, LeavesState>(
        listener: (context, state) {
          if (state.error != null && !state.busy) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text(state.error!)),
            );
          }
        },
        builder: (context, state) {
          if (state.status == LoadStatus.loading && state.balances.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }
          return RefreshIndicator(
            onRefresh: () => context.read<LeavesCubit>().load(),
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
              children: [
                Text('★ BALANCES',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: AppColors.brandGoldDark,
                    )),
                const SizedBox(height: 8),
                if (state.balances.isEmpty)
                  const Text('No leave allocations yet'),
                ...state.balances.map((b) => _BalanceCard(balance: b)),
                const SizedBox(height: 24),
                Text('★ HISTORY',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: AppColors.brandGoldDark,
                    )),
                const SizedBox(height: 8),
                if (state.requests.isEmpty)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 12),
                    child: Text('No leave requests yet'),
                  )
                else
                  ...state.requests.map((r) => _RequestCard(request: r)),
              ],
            ),
          );
        },
      ),
    );
  }
}

void _openApplySheet(BuildContext context) {
  final cubit = context.read<LeavesCubit>();
  showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    builder: (sheetCtx) => Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(sheetCtx).viewInsets.bottom,
      ),
      child: BlocProvider.value(
        value: cubit,
        child: const _ApplyLeaveSheet(),
      ),
    ),
  );
}

class _ApplyLeaveSheet extends StatefulWidget {
  const _ApplyLeaveSheet();
  @override
  State<_ApplyLeaveSheet> createState() => _ApplyLeaveSheetState();
}

class _ApplyLeaveSheetState extends State<_ApplyLeaveSheet> {
  final _formKey = GlobalKey<FormState>();
  final _reasonCtrl = TextEditingController();
  int? _typeId;
  DateTime _from = DateTime.now();
  DateTime _to = DateTime.now();
  bool _halfDay = false;

  @override
  void dispose() {
    _reasonCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickFrom() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _from,
      firstDate: DateTime.now().subtract(const Duration(days: 30)),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null) {
      setState(() {
        _from = picked;
        if (_to.isBefore(_from)) _to = _from;
      });
    }
  }

  Future<void> _pickTo() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _to.isBefore(_from) ? _from : _to,
      firstDate: _from,
      lastDate: _from.add(const Duration(days: 180)),
    );
    if (picked != null) setState(() => _to = picked);
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false) || _typeId == null) {
      return;
    }
    final ok = await context.read<LeavesCubit>().apply(
          leaveTypeId: _typeId!,
          fromDate: DateFormat('yyyy-MM-dd').format(_from),
          toDate: DateFormat('yyyy-MM-dd')
              .format(_halfDay ? _from : _to),
          reason: _reasonCtrl.text.trim().isEmpty ? null : _reasonCtrl.text.trim(),
          halfDay: _halfDay,
        );
    if (!mounted) return;
    if (ok) {
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Leave applied — awaiting approval')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return BlocBuilder<LeavesCubit, LeavesState>(
      builder: (context, state) {
        return Padding(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 28),
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    Text('★ APPLY LEAVE',
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: AppColors.brandGoldDark,
                        )),
                    const Spacer(),
                    IconButton(
                      icon: const Icon(Icons.close, size: 20),
                      onPressed: () => Navigator.of(context).pop(),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Text('New leave request', style: theme.textTheme.headlineSmall),
                const SizedBox(height: 24),
                DropdownButtonFormField<int>(
                  value: _typeId,
                  decoration: const InputDecoration(labelText: 'Leave type'),
                  items: state.types
                      .map((t) => DropdownMenuItem(
                            value: t.id,
                            child: Text('${t.code} · ${t.name}'),
                          ))
                      .toList(),
                  onChanged: (v) => setState(() => _typeId = v),
                  validator: (v) => v == null ? 'Pick a leave type' : null,
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: InkWell(
                        onTap: _pickFrom,
                        child: InputDecorator(
                          decoration: const InputDecoration(labelText: 'From'),
                          child: Text(DateFormat('d MMM yyyy').format(_from)),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: InkWell(
                        onTap: _halfDay ? null : _pickTo,
                        child: InputDecorator(
                          decoration: const InputDecoration(labelText: 'To'),
                          child: Text(
                            _halfDay
                                ? '— same day'
                                : DateFormat('d MMM yyyy').format(_to),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                CheckboxListTile(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Half-day'),
                  value: _halfDay,
                  onChanged: (v) => setState(() {
                    _halfDay = v ?? false;
                    if (_halfDay) _to = _from;
                  }),
                ),
                TextFormField(
                  controller: _reasonCtrl,
                  decoration: const InputDecoration(labelText: 'Reason'),
                  maxLines: 2,
                ),
                const SizedBox(height: 20),
                FilledButton(
                  onPressed: state.busy ? null : _submit,
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 6),
                    child: state.busy
                        ? const SizedBox(
                            height: 18,
                            width: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Text('Submit'),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _BalanceCard extends StatelessWidget {
  const _BalanceCard({required this.balance});
  final LeaveBalance balance;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    balance.leaveType?.name ?? 'Leave',
                    style: theme.textTheme.titleMedium,
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'Allocated ${balance.allocated} · Used ${balance.used}',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: AppColors.textMuted,
                    ),
                  ),
                ],
              ),
            ),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '${balance.balance}',
                  style: theme.textTheme.headlineSmall?.copyWith(
                    color: AppColors.brandGoldDark,
                  ),
                ),
                const Text(
                  'remaining',
                  style: TextStyle(
                    fontSize: 10,
                    color: AppColors.textMuted,
                    letterSpacing: 1.5,
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

class _RequestCard extends StatelessWidget {
  const _RequestCard({required this.request});
  final LeaveRequest request;

  Color _color() {
    switch (request.status) {
      case 'approved':
        return AppColors.success;
      case 'rejected':
        return AppColors.error;
      case 'cancelled':
        return AppColors.textMuted;
      default:
        return AppColors.warning;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final c = _color();
    return Card(
      child: ListTile(
        title: Text(
          '${request.leaveType?.code ?? '—'} · ${request.days} day'
          '${request.days != 1 ? 's' : ''}',
        ),
        subtitle: Text(
          '${request.fromDate} → ${request.toDate}'
          '${request.reason != null ? '\n${request.reason}' : ''}',
          style: theme.textTheme.bodySmall,
        ),
        isThreeLine: request.reason != null,
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: c.withOpacity(0.15),
            borderRadius: BorderRadius.circular(6),
          ),
          child: Text(
            request.status.toUpperCase(),
            style: TextStyle(
              fontSize: 10,
              fontFamily: 'monospace',
              letterSpacing: 1.5,
              fontWeight: FontWeight.w700,
              color: c,
            ),
          ),
        ),
      ),
    );
  }
}
