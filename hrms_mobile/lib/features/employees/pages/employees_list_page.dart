import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../cubit/employees_cubit.dart';
import '../data/employee_api.dart';
import '../data/employee_models.dart';

class EmployeesListPage extends StatelessWidget {
  const EmployeesListPage({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => EmployeesCubit(sl<EmployeeApi>())..load(),
      child: const _EmployeesView(),
    );
  }
}

class _EmployeesView extends StatefulWidget {
  const _EmployeesView();

  @override
  State<_EmployeesView> createState() => _EmployeesViewState();
}

class _EmployeesViewState extends State<_EmployeesView> {
  final _searchCtrl = TextEditingController();

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Employees')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: TextField(
              controller: _searchCtrl,
              decoration: const InputDecoration(
                hintText: 'Search by name or code…',
                prefixIcon: Icon(Icons.search, size: 18),
              ),
              onSubmitted: (v) =>
                  context.read<EmployeesCubit>().load(search: v),
            ),
          ),
          Expanded(
            child: BlocBuilder<EmployeesCubit, EmployeesState>(
              builder: (context, state) {
                if (state.status == LoadStatus.loading && state.items.isEmpty) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (state.status == LoadStatus.failure) {
                  return Center(
                    child: Text(
                      state.error ?? 'Error',
                      style: TextStyle(color: theme.colorScheme.error),
                    ),
                  );
                }
                if (state.items.isEmpty) {
                  return const Center(child: Text('No employees found'));
                }
                return RefreshIndicator(
                  onRefresh: () => context.read<EmployeesCubit>().load(),
                  child: ListView.separated(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 8,
                    ),
                    itemCount: state.items.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 8),
                    itemBuilder: (_, i) => _EmployeeRow(employee: state.items[i]),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _EmployeeRow extends StatelessWidget {
  const _EmployeeRow({required this.employee});

  final EmployeeListItem employee;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: () => context.push('/employees/${employee.id}'),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            children: [
              CircleAvatar(
                radius: 24,
                backgroundColor: AppColors.brandGold.withOpacity(0.15),
                backgroundImage: employee.photoUrl != null
                    ? NetworkImage(employee.photoUrl!)
                    : null,
                child: employee.photoUrl == null
                    ? Text(
                        employee.firstName.isNotEmpty
                            ? employee.firstName[0]
                            : '?',
                        style: TextStyle(
                          fontWeight: FontWeight.w600,
                          color: context.textPrimary,
                        ),
                      )
                    : null,
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      employee.fullName,
                      style: theme.textTheme.titleMedium,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      [
                        employee.employeeCode,
                        if (employee.designation != null)
                          employee.designation!.name,
                        if (employee.department != null)
                          employee.department!.name,
                      ].join(' · '),
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: AppColors.brandBrownLight,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        if (employee.category != null)
                          _CategoryChip(code: employee.category!.code),
                        const SizedBox(width: 6),
                        if (employee.isOnProbation)
                          _StatusChip(
                            label: 'Probation',
                            color: AppColors.warning,
                          )
                        else
                          _StatusChip(
                            label: 'Confirmed',
                            color: AppColors.success,
                          ),
                      ],
                    ),
                  ],
                ),
              ),
              const Icon(
                Icons.arrow_forward_ios,
                size: 14,
                color: AppColors.brandBrownLight,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _CategoryChip extends StatelessWidget {
  const _CategoryChip({required this.code});
  final String code;

  @override
  Widget build(BuildContext context) {
    final color = switch (code) {
      'INTERN' => AppColors.brandGoldLighter,
      'TRAINEE' => AppColors.info,
      'PERMANENT' => AppColors.success,
      'CONTRACT' => AppColors.warning,
      _ => AppColors.brandBrownLight,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        code,
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

class _StatusChip extends StatelessWidget {
  const _StatusChip({required this.label, required this.color});
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        label,
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
