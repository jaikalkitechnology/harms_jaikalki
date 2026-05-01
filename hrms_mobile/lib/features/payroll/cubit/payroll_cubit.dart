import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../employees/cubit/employees_cubit.dart' show LoadStatus;
import '../data/payroll_api.dart';
import '../data/payroll_models.dart';

class PayrollState extends Equatable {
  const PayrollState({
    this.status = LoadStatus.initial,
    this.payslips = const [],
    this.reimbursements = const [],
    this.busy = false,
    this.error,
  });

  final LoadStatus status;
  final List<Payslip> payslips;
  final List<Reimbursement> reimbursements;
  final bool busy;
  final String? error;

  PayrollState copyWith({
    LoadStatus? status,
    List<Payslip>? payslips,
    List<Reimbursement>? reimbursements,
    bool? busy,
    String? error,
    bool clearError = false,
  }) =>
      PayrollState(
        status: status ?? this.status,
        payslips: payslips ?? this.payslips,
        reimbursements: reimbursements ?? this.reimbursements,
        busy: busy ?? this.busy,
        error: clearError ? null : (error ?? this.error),
      );

  @override
  List<Object?> get props => [status, payslips, reimbursements, busy, error];
}

class PayrollCubit extends Cubit<PayrollState> {
  PayrollCubit(this._api) : super(const PayrollState());
  final PayrollApi _api;

  Future<void> load() async {
    emit(state.copyWith(status: LoadStatus.loading, clearError: true));
    try {
      final results = await Future.wait([
        _api.myPayslips(),
        _api.myReimbursements(),
      ]);
      emit(state.copyWith(
        status: LoadStatus.success,
        payslips: results[0] as List<Payslip>,
        reimbursements: results[1] as List<Reimbursement>,
      ));
    } catch (_) {
      emit(state.copyWith(
        status: LoadStatus.failure,
        error: 'Could not load payroll',
      ));
    }
  }

  Future<bool> submitReimbursement({
    required String category,
    required num amount,
    required String billDate,
    String? description,
  }) async {
    emit(state.copyWith(busy: true, clearError: true));
    try {
      await _api.submitReimbursement(
        category: category,
        amount: amount,
        billDate: billDate,
        description: description,
      );
      emit(state.copyWith(busy: false));
      await load();
      return true;
    } catch (e) {
      emit(state.copyWith(busy: false, error: 'Could not submit'));
      return false;
    }
  }
}
