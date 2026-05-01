import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../cubit/employee_detail_cubit.dart';
import '../cubit/employees_cubit.dart' show LoadStatus;
import '../data/employee_api.dart';
import '../data/employee_models.dart';

class EmployeeDetailPage extends StatelessWidget {
  const EmployeeDetailPage({super.key, required this.employeeId});

  final int employeeId;

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) =>
          EmployeeDetailCubit(sl<EmployeeApi>())..load(employeeId),
      child: const _DetailView(),
    );
  }
}

class _DetailView extends StatelessWidget {
  const _DetailView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Employee')),
      body: BlocBuilder<EmployeeDetailCubit, EmployeeDetailState>(
        builder: (context, state) {
          if (state.status == LoadStatus.loading || state.employee == null) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state.status == LoadStatus.failure) {
            return Center(child: Text(state.error ?? 'Error'));
          }
          final emp = state.employee!;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _Header(employee: emp),
              const SizedBox(height: 16),
              _InfoCard(
                title: 'Work',
                rows: [
                  ('Code', emp.employeeCode),
                  ('Department', emp.department?.name ?? '—'),
                  ('Designation', emp.designation?.name ?? '—'),
                  ('Joined', emp.dateOfJoining ?? '—'),
                  ('Probation ends', emp.probationEndDate ?? '—'),
                  ('Confirmed', emp.confirmationDate ?? '—'),
                  ('Location', emp.workLocation ?? '—'),
                ],
              ),
              const SizedBox(height: 12),
              _InfoCard(
                title: 'Contact',
                rows: [
                  ('Email', emp.personalEmail ?? '—'),
                  ('Phone', emp.personalPhone ?? '—'),
                ],
              ),
              if (state.breakup != null) ...[
                const SizedBox(height: 12),
                _SalaryCard(breakup: state.breakup!),
              ],
            ],
          );
        },
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.employee});
  final EmployeeDetail employee;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final daysLeft = employee.probationEndDate == null
        ? null
        : DateTime.tryParse(employee.probationEndDate!)
            ?.difference(DateTime.now())
            .inDays;

    return Row(
      children: [
        CircleAvatar(
          radius: 36,
          backgroundColor: AppColors.brandGold.withOpacity(0.15),
          backgroundImage: employee.photoUrl != null
              ? NetworkImage(employee.photoUrl!)
              : null,
          child: employee.photoUrl == null
              ? const Icon(Icons.person,
                  size: 32, color: AppColors.brandBrownDarker)
              : null,
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '★ ${employee.employeeCode}',
                style: theme.textTheme.labelSmall?.copyWith(
                  color: AppColors.brandGoldDark,
                ),
              ),
              const SizedBox(height: 2),
              Text(employee.fullName,
                  style: theme.textTheme.headlineSmall),
              const SizedBox(height: 6),
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: [
                  if (employee.category != null)
                    _Pill(
                      text: employee.category!.code,
                      color: AppColors.brandGoldDark,
                    ),
                  if (employee.isOnProbation)
                    _Pill(
                      text: daysLeft != null
                          ? 'Probation · ${daysLeft}d left'
                          : 'On Probation',
                      color: AppColors.warning,
                    )
                  else
                    _Pill(text: 'Confirmed', color: AppColors.success),
                ],
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill({required this.text, required this.color});
  final String text;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 10,
          fontFamily: 'monospace',
          letterSpacing: 1.5,
          fontWeight: FontWeight.w600,
          color: color,
        ),
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({required this.title, required this.rows});
  final String title;
  final List<(String, String)> rows;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title.toUpperCase(),
                style: theme.textTheme.labelSmall?.copyWith(
                  color: AppColors.brandGoldDark,
                )),
            const SizedBox(height: 12),
            ...rows.map(
              (r) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    SizedBox(
                      width: 110,
                      child: Text(
                        r.$1,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: AppColors.brandBrownLight,
                        ),
                      ),
                    ),
                    Expanded(
                      child: Text(
                        r.$2,
                        style: theme.textTheme.bodyMedium,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SalaryCard extends StatelessWidget {
  const _SalaryCard({required this.breakup});
  final SalaryBreakup breakup;

  String _inr(int n) => '₹${n.toString().replaceAllMapped(
        RegExp(r'(\d)(?=(\d{2})+\d$)'),
        (m) => '${m[1]},',
      )}';

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('SALARY BREAKUP',
                style: theme.textTheme.labelSmall?.copyWith(
                  color: AppColors.brandGoldDark,
                )),
            const SizedBox(height: 4),
            Text(breakup.templateName, style: theme.textTheme.titleMedium),
            const SizedBox(height: 12),
            if (breakup.isIntern) ...[
              Text(
                'Intern — receives travel reimbursement only '
                '(max ${_inr(breakup.travelExpenseMax)}/month).',
                style: theme.textTheme.bodyMedium,
              ),
            ] else ...[
              _row('Basic', _inr(breakup.basic)),
              _row('HRA', _inr(breakup.hra)),
              if (breakup.otherAllowance > 0)
                _row('Other allowance', _inr(breakup.otherAllowance)),
              const Divider(),
              _row('Gross', _inr(breakup.gross), bold: true),
              const SizedBox(height: 8),
              _row('PF (Employee)', '- ${_inr(breakup.pfEmployee)}'),
              _row('ESIC (Employee)', '- ${_inr(breakup.esicEmployee)}'),
              if (breakup.professionalTax > 0)
                _row('Prof. Tax', '- ${_inr(breakup.professionalTax)}'),
              const Divider(),
              _row('Net Salary', _inr(breakup.netSalary),
                  bold: true, color: AppColors.brandGoldDark),
              const SizedBox(height: 12),
              _row('CTC / month', _inr(breakup.totalCtcMonthly)),
              _row('CTC / year', _inr(breakup.totalCtcAnnual),
                  bold: true, color: AppColors.brandGoldDark),
            ],
          ],
        ),
      ),
    );
  }

  Widget _row(String label, String value,
      {bool bold = false, Color? color}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label,
              style: TextStyle(
                color: color ?? AppColors.brandBrownLight,
                fontWeight: bold ? FontWeight.w600 : FontWeight.w400,
              )),
          Text(value,
              style: TextStyle(
                color: color ?? AppColors.brandBrownDarker,
                fontWeight: bold ? FontWeight.w700 : FontWeight.w500,
              )),
        ],
      ),
    );
  }
}
