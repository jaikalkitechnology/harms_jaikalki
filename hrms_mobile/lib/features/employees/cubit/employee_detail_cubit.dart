import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../data/employee_api.dart';
import '../data/employee_models.dart';

import 'employees_cubit.dart' show LoadStatus;

class EmployeeDetailState extends Equatable {
  const EmployeeDetailState({
    this.status = LoadStatus.initial,
    this.employee,
    this.breakup,
    this.error,
  });

  final LoadStatus status;
  final EmployeeDetail? employee;
  final SalaryBreakup? breakup;
  final String? error;

  EmployeeDetailState copyWith({
    LoadStatus? status,
    EmployeeDetail? employee,
    SalaryBreakup? breakup,
    String? error,
    bool clearError = false,
  }) =>
      EmployeeDetailState(
        status: status ?? this.status,
        employee: employee ?? this.employee,
        breakup: breakup ?? this.breakup,
        error: clearError ? null : (error ?? this.error),
      );

  @override
  List<Object?> get props => [status, employee, breakup, error];
}

class EmployeeDetailCubit extends Cubit<EmployeeDetailState> {
  EmployeeDetailCubit(this._api) : super(const EmployeeDetailState());

  final EmployeeApi _api;

  Future<void> load(int id) async {
    emit(state.copyWith(status: LoadStatus.loading, clearError: true));
    try {
      final emp = await _api.get(id);
      SalaryBreakup? breakup;
      if (emp.salaryTemplateId != null) {
        try {
          breakup = await _api.calculate(
            emp.salaryTemplateId!,
            ctc: emp.ctcAnnual > 0 ? emp.ctcAnnual : null,
          );
        } catch (_) {
          // Permission may not allow calculate; ignore.
        }
      }
      emit(state.copyWith(
        status: LoadStatus.success,
        employee: emp,
        breakup: breakup,
      ));
    } catch (e) {
      emit(state.copyWith(
        status: LoadStatus.failure,
        error: 'Could not load employee',
      ));
    }
  }
}
