import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../employees/cubit/employees_cubit.dart' show LoadStatus;
import '../data/intern_expense_api.dart';
import '../data/intern_expense_models.dart';

class InternExpensesState extends Equatable {
  const InternExpensesState({
    this.status = LoadStatus.initial,
    this.items = const [],
    this.submitting = false,
    this.error,
  });

  final LoadStatus status;
  final List<InternExpense> items;
  final bool submitting;
  final String? error;

  InternExpensesState copyWith({
    LoadStatus? status,
    List<InternExpense>? items,
    bool? submitting,
    String? error,
    bool clearError = false,
  }) =>
      InternExpensesState(
        status: status ?? this.status,
        items: items ?? this.items,
        submitting: submitting ?? this.submitting,
        error: clearError ? null : (error ?? this.error),
      );

  @override
  List<Object?> get props => [status, items, submitting, error];
}

class InternExpensesCubit extends Cubit<InternExpensesState> {
  InternExpensesCubit(this._api) : super(const InternExpensesState());

  final InternExpenseApi _api;

  Future<void> load() async {
    emit(state.copyWith(status: LoadStatus.loading, clearError: true));
    try {
      final items = await _api.mine();
      emit(state.copyWith(status: LoadStatus.success, items: items));
    } catch (e) {
      emit(state.copyWith(
        status: LoadStatus.failure,
        error: 'Could not load expenses',
      ));
    }
  }

  Future<bool> submit({
    required String expenseDate,
    required String expenseType,
    required num amount,
    String? description,
  }) async {
    emit(state.copyWith(submitting: true, clearError: true));
    try {
      final created = await _api.submit(
        expenseDate: expenseDate,
        expenseType: expenseType,
        amount: amount,
        description: description,
      );
      emit(state.copyWith(
        submitting: false,
        items: [created, ...state.items],
      ));
      return true;
    } catch (e) {
      emit(state.copyWith(
        submitting: false,
        error: 'Could not submit expense',
      ));
      return false;
    }
  }
}
