import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../../employees/cubit/employees_cubit.dart' show LoadStatus;
import '../cubit/intern_expenses_cubit.dart';
import '../data/intern_expense_api.dart';
import '../data/intern_expense_models.dart';

class InternExpensesPage extends StatelessWidget {
  const InternExpensesPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => InternExpensesCubit(sl<InternExpenseApi>())..load(),
      child: const _InternView(),
    );
  }
}

class _InternView extends StatelessWidget {
  const _InternView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Travel Expenses')),
      floatingActionButton: BlocBuilder<InternExpensesCubit, InternExpensesState>(
        builder: (context, state) => FloatingActionButton.extended(
          onPressed: () => _openSubmitSheet(context),
          backgroundColor: AppColors.brandGoldDark,
          foregroundColor: Colors.white,
          icon: const Icon(Icons.add),
          label: const Text('Submit'),
        ),
      ),
      body: BlocBuilder<InternExpensesCubit, InternExpensesState>(
        builder: (context, state) {
          if (state.status == LoadStatus.loading && state.items.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state.items.isEmpty) {
            return const Center(
              child: Padding(
                padding: EdgeInsets.all(24),
                child: Text(
                  'No expenses yet. Tap Submit to add your first travel reimbursement claim.',
                  textAlign: TextAlign.center,
                ),
              ),
            );
          }
          return RefreshIndicator(
            onRefresh: () => context.read<InternExpensesCubit>().load(),
            child: ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
              itemCount: state.items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (_, i) => _ExpenseRow(expense: state.items[i]),
            ),
          );
        },
      ),
    );
  }
}

void _openSubmitSheet(BuildContext context) {
  final cubit = context.read<InternExpensesCubit>();
  showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    builder: (sheetCtx) => Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(sheetCtx).viewInsets.bottom,
      ),
      child: BlocProvider.value(
        value: cubit,
        child: const _SubmitSheet(),
      ),
    ),
  );
}

class _SubmitSheet extends StatefulWidget {
  const _SubmitSheet();
  @override
  State<_SubmitSheet> createState() => _SubmitSheetState();
}

class _SubmitSheetState extends State<_SubmitSheet> {
  final _formKey = GlobalKey<FormState>();
  final _amountCtrl = TextEditingController();
  final _descriptionCtrl = TextEditingController();
  String _expenseType = 'office_commute';
  DateTime _date = DateTime.now();

  @override
  void dispose() {
    _amountCtrl.dispose();
    _descriptionCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _date,
      firstDate: DateTime.now().subtract(const Duration(days: 60)),
      lastDate: DateTime.now(),
    );
    if (picked != null) setState(() => _date = picked);
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    final ok = await context.read<InternExpensesCubit>().submit(
          expenseDate: DateFormat('yyyy-MM-dd').format(_date),
          expenseType: _expenseType,
          amount: num.tryParse(_amountCtrl.text) ?? 0,
          description: _descriptionCtrl.text.trim().isEmpty
              ? null
              : _descriptionCtrl.text.trim(),
        );
    if (!mounted) return;
    if (ok) {
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Expense submitted')),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            context.read<InternExpensesCubit>().state.error ?? 'Failed',
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 28),
      child: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                Text('★ NEW EXPENSE',
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
            Text('Submit travel reimbursement',
                style: theme.textTheme.headlineSmall),
            const SizedBox(height: 24),

            // Type chips
            Wrap(
              spacing: 8,
              children: [
                _typeChip('office_commute', 'Office commute'),
                _typeChip('local_travel', 'Local travel'),
                _typeChip('project_visit', 'Project visit'),
              ],
            ),
            const SizedBox(height: 16),

            // Date
            InkWell(
              onTap: _pickDate,
              borderRadius: BorderRadius.circular(12),
              child: InputDecorator(
                decoration: const InputDecoration(labelText: 'Date'),
                child: Row(
                  children: [
                    Expanded(child: Text(DateFormat('d MMM yyyy').format(_date))),
                    const Icon(Icons.calendar_today, size: 16),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),

            // Amount
            TextFormField(
              controller: _amountCtrl,
              decoration: const InputDecoration(
                labelText: 'Amount (₹)',
                prefixText: '₹  ',
              ),
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: false),
              validator: (v) {
                final n = num.tryParse(v ?? '');
                if (n == null || n <= 0) return 'Enter a positive amount';
                return null;
              },
            ),
            const SizedBox(height: 12),

            // Description
            TextFormField(
              controller: _descriptionCtrl,
              maxLines: 2,
              decoration: const InputDecoration(
                labelText: 'Description (optional)',
              ),
            ),
            const SizedBox(height: 24),

            BlocBuilder<InternExpensesCubit, InternExpensesState>(
              builder: (context, state) => FilledButton(
                onPressed: state.submitting ? null : _submit,
                child: Padding(
                  padding: const EdgeInsets.symmetric(vertical: 6),
                  child: state.submitting
                      ? const SizedBox(
                          height: 18,
                          width: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Text('Submit for approval'),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _typeChip(String value, String label) {
    final selected = _expenseType == value;
    return ChoiceChip(
      label: Text(label),
      selected: selected,
      onSelected: (_) => setState(() => _expenseType = value),
      selectedColor: AppColors.brandGold.withOpacity(0.25),
    );
  }
}

class _ExpenseRow extends StatelessWidget {
  const _ExpenseRow({required this.expense});
  final InternExpense expense;

  Color _statusColor() {
    switch (expense.status) {
      case 'approved':
        return AppColors.info;
      case 'rejected':
        return AppColors.error;
      case 'reimbursed':
        return AppColors.success;
      default:
        return AppColors.warning;
    }
  }

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
                  Text('₹${expense.amount}',
                      style: theme.textTheme.titleLarge),
                  const SizedBox(height: 2),
                  Text(
                    '${expense.expenseDate} · ${expense.expenseType.replaceAll('_', ' ')}',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: AppColors.textMuted,
                    ),
                  ),
                  if (expense.description != null) ...[
                    const SizedBox(height: 4),
                    Text(expense.description!,
                        style: theme.textTheme.bodySmall),
                  ],
                ],
              ),
            ),
            Container(
              padding:
                  const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: _statusColor().withOpacity(0.15),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                expense.status.toUpperCase(),
                style: TextStyle(
                  fontSize: 10,
                  fontFamily: 'JetBrainsMono',
                  letterSpacing: 1.5,
                  fontWeight: FontWeight.w700,
                  color: _statusColor(),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
