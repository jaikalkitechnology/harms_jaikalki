import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';

import '../../../core/di/injection.dart';
import '../../../core/files/file_saver.dart';
import '../../../core/theme/app_colors.dart';
import '../../employees/cubit/employees_cubit.dart' show LoadStatus;
import '../cubit/payroll_cubit.dart';
import '../data/payroll_api.dart';
import '../data/payroll_models.dart';

const _months = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
];

String _inr(num n) {
  final formatter =
      NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);
  return formatter.format(n);
}

class PayrollHomePage extends StatelessWidget {
  const PayrollHomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => PayrollCubit(sl<PayrollApi>())..load(),
      child: const _PayrollView(),
    );
  }
}

class _PayrollView extends StatelessWidget {
  const _PayrollView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Payroll')),
      floatingActionButton: BlocBuilder<PayrollCubit, PayrollState>(
        builder: (context, _) => FloatingActionButton.extended(
          onPressed: () => _openReimbursementSheet(context),
          backgroundColor: AppColors.brandGoldDark,
          foregroundColor: Colors.white,
          icon: const Icon(Icons.add),
          label: const Text('Reimbursement'),
        ),
      ),
      body: BlocConsumer<PayrollCubit, PayrollState>(
        listener: (context, state) {
          if (state.error != null && !state.busy) {
            ScaffoldMessenger.of(context)
                .showSnackBar(SnackBar(content: Text(state.error!)));
          }
        },
        builder: (context, state) {
          if (state.status == LoadStatus.loading && state.payslips.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }
          return RefreshIndicator(
            onRefresh: () => context.read<PayrollCubit>().load(),
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
              children: [
                Text(
                  '★ PAYSLIPS',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: AppColors.brandGoldDark,
                      ),
                ),
                const SizedBox(height: 8),
                if (state.payslips.isEmpty)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 12),
                    child: Text('No payslips yet — your first one will appear after the next payroll run.'),
                  )
                else
                  ...state.payslips.map(
                    (p) => _PayslipCard(payslip: p, api: sl<PayrollApi>()),
                  ),
                const SizedBox(height: 24),
                Text(
                  '★ REIMBURSEMENTS',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: AppColors.brandGoldDark,
                      ),
                ),
                const SizedBox(height: 8),
                if (state.reimbursements.isEmpty)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 12),
                    child: Text('Tap the button below to submit your first claim.'),
                  )
                else
                  ...state.reimbursements.map(
                    (r) => _ReimbursementRow(reimbursement: r),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _PayslipCard extends StatelessWidget {
  const _PayslipCard({required this.payslip, required this.api});
  final Payslip payslip;
  final PayrollApi api;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
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
                    '${_months[payslip.month - 1]} ${payslip.year}',
                    style: theme.textTheme.titleMedium,
                  ),
                ),
                Text(
                  _inr(payslip.netPay),
                  style: theme.textTheme.titleLarge?.copyWith(
                    color: AppColors.brandGoldDark,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Wrap(
              spacing: 16,
              runSpacing: 4,
              children: [
                _miniStat(theme, 'Gross', _inr(payslip.gross)),
                _miniStat(theme, 'Deductions', _inr(payslip.totalDeductions)),
                _miniStat(theme, 'Days paid', '${payslip.daysPaid}'),
              ],
            ),
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerRight,
              child: Builder(
                builder: (btnCtx) => TextButton.icon(
                  onPressed: () async {
                    final messenger = ScaffoldMessenger.of(btnCtx);
                    messenger.showSnackBar(
                      const SnackBar(content: Text('Preparing payslip…')),
                    );
                    try {
                      final bytes = await api.downloadPayslipPdf(
                        payslip.id,
                      );
                      final month =
                          payslip.month.toString().padLeft(2, '0');
                      final problem = await saveAndOpenBytes(
                        bytes,
                        filename: 'payslip_${payslip.year}_$month.pdf',
                      );
                      messenger.hideCurrentSnackBar();
                      if (problem != null) {
                        messenger.showSnackBar(
                          SnackBar(content: Text(problem)),
                        );
                      }
                    } catch (_) {
                      messenger.hideCurrentSnackBar();
                      messenger.showSnackBar(
                        const SnackBar(
                          content: Text('Could not open payslip'),
                        ),
                      );
                    }
                  },
                  icon: const Icon(Icons.picture_as_pdf, size: 18),
                  label: const Text('Open PDF'),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _miniStat(ThemeData theme, String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label.toUpperCase(),
            style: theme.textTheme.labelSmall?.copyWith(
              color: AppColors.textMuted,
            )),
        Text(value, style: theme.textTheme.bodyMedium),
      ],
    );
  }
}

class _ReimbursementRow extends StatelessWidget {
  const _ReimbursementRow({required this.reimbursement});
  final Reimbursement reimbursement;

  Color _color() {
    switch (reimbursement.status) {
      case 'approved':
        return AppColors.info;
      case 'paid':
        return AppColors.success;
      case 'rejected':
        return AppColors.error;
      default:
        return AppColors.warning;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: ListTile(
        title: Text('${_inr(reimbursement.amount)} · ${reimbursement.category}'),
        subtitle: Text(
          [
            reimbursement.billDate,
            if (reimbursement.description != null) reimbursement.description!,
          ].join(' · '),
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: theme.textTheme.bodySmall,
        ),
        trailing: Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: _color().withOpacity(0.15),
            borderRadius: BorderRadius.circular(6),
          ),
          child: Text(
            reimbursement.status.toUpperCase(),
            style: TextStyle(
              fontSize: 10,
              fontFamily: 'monospace',
              letterSpacing: 1.5,
              fontWeight: FontWeight.w700,
              color: _color(),
            ),
          ),
        ),
      ),
    );
  }
}

void _openReimbursementSheet(BuildContext context) {
  final cubit = context.read<PayrollCubit>();
  showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    builder: (sheetCtx) => Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(sheetCtx).viewInsets.bottom,
      ),
      child: BlocProvider.value(
        value: cubit,
        child: const _ReimbursementSheet(),
      ),
    ),
  );
}

class _ReimbursementSheet extends StatefulWidget {
  const _ReimbursementSheet();
  @override
  State<_ReimbursementSheet> createState() => _ReimbursementSheetState();
}

class _ReimbursementSheetState extends State<_ReimbursementSheet> {
  final _formKey = GlobalKey<FormState>();
  final _amountCtrl = TextEditingController();
  final _descCtrl = TextEditingController();
  String _category = 'travel';
  DateTime _date = DateTime.now();

  @override
  void dispose() {
    _amountCtrl.dispose();
    _descCtrl.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _date,
      firstDate: DateTime.now().subtract(const Duration(days: 90)),
      lastDate: DateTime.now(),
    );
    if (picked != null) setState(() => _date = picked);
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    final ok = await context.read<PayrollCubit>().submitReimbursement(
          category: _category,
          amount: num.tryParse(_amountCtrl.text) ?? 0,
          billDate: DateFormat('yyyy-MM-dd').format(_date),
          description:
              _descCtrl.text.trim().isEmpty ? null : _descCtrl.text.trim(),
        );
    if (!mounted) return;
    if (ok) {
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Reimbursement submitted')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final categories = const [
      ('travel', 'Travel'),
      ('food', 'Food'),
      ('internet', 'Internet'),
      ('phone', 'Phone'),
      ('medical', 'Medical'),
      ('books', 'Books'),
      ('other', 'Other'),
    ];

    return BlocBuilder<PayrollCubit, PayrollState>(
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
                    Text('★ NEW CLAIM',
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
                Text('Submit reimbursement', style: theme.textTheme.headlineSmall),
                const SizedBox(height: 16),
                Wrap(
                  spacing: 8,
                  runSpacing: 4,
                  children: categories
                      .map((c) => ChoiceChip(
                            label: Text(c.$2),
                            selected: _category == c.$1,
                            onSelected: (_) =>
                                setState(() => _category = c.$1),
                            selectedColor:
                                AppColors.brandGold.withOpacity(0.25),
                          ))
                      .toList(),
                ),
                const SizedBox(height: 16),
                InkWell(
                  onTap: _pickDate,
                  borderRadius: BorderRadius.circular(12),
                  child: InputDecorator(
                    decoration: const InputDecoration(labelText: 'Bill date'),
                    child: Row(
                      children: [
                        Expanded(
                          child: Text(DateFormat('d MMM yyyy').format(_date)),
                        ),
                        const Icon(Icons.calendar_today, size: 16),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _amountCtrl,
                  decoration: const InputDecoration(
                    labelText: 'Amount (₹)',
                    prefixText: '₹  ',
                  ),
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  validator: (v) {
                    final n = num.tryParse(v ?? '');
                    if (n == null || n <= 0) return 'Enter a positive amount';
                    return null;
                  },
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _descCtrl,
                  maxLines: 2,
                  decoration: const InputDecoration(labelText: 'Description'),
                ),
                const SizedBox(height: 24),
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
                        : const Text('Submit claim'),
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
