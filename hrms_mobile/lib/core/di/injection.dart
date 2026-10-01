import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:get_it/get_it.dart';
import 'package:local_auth/local_auth.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../features/approvals/data/approval_api.dart';
import '../../features/attendance/data/attendance_api.dart';
import '../../features/auth/data/datasources/auth_remote_datasource.dart';
import '../../features/auth/data/repositories/auth_repository_impl.dart';
import '../../features/auth/domain/repositories/auth_repository.dart';
import '../../features/auth/presentation/bloc/auth_bloc.dart';
import '../../features/dashboard/data/dashboard_api.dart';
import '../../features/dwp/data/dwp_api.dart';
import '../../features/employees/data/employee_api.dart';
import '../../features/exam/data/exam_api.dart';
import '../../features/field/data/field_api.dart';
import '../../features/intern_expenses/data/intern_expense_api.dart';
import '../../features/justice/data/justice_api.dart';
import '../../features/launch/data/launch_api.dart';
import '../../features/leaves/data/leave_api.dart';
import '../../features/lms/data/lms_api.dart';
import '../../features/payroll/data/payroll_api.dart';
import '../../features/performance/data/performance_api.dart';
import '../../features/polish/data/polish_api.dart';
import '../../features/reports/data/reports_api.dart';
import '../../features/sales/data/sales_api.dart';
import '../../features/settings/cubit/settings_cubit.dart';
import '../../features/trainer/data/trainer_api.dart';
import '../../features/verification/data/verification_api.dart';
import '../modules/enabled_modules_service.dart';
import '../network/dio_client.dart';
import '../storage/secure_storage.dart';

final GetIt sl = GetIt.instance;

Future<void> setupDependencies() async {
  // Persistent prefs (must come first — used by SettingsCubit during boot)
  final prefs = await SharedPreferences.getInstance();
  sl.registerSingleton<SharedPreferences>(prefs);
  sl.registerSingleton<SettingsCubit>(SettingsCubit(prefs)..hydrate());

  // Storage
  sl.registerLazySingleton<FlutterSecureStorage>(
    () => const FlutterSecureStorage(),
  );
  sl.registerLazySingleton<SecureStorage>(() => SecureStorage(sl()));

  // Networking
  sl.registerLazySingleton<Dio>(DioClient.create);

  // Biometrics
  sl.registerLazySingleton<LocalAuthentication>(() => LocalAuthentication());

  // Auth feature
  sl.registerLazySingleton<AuthRemoteDataSource>(
    () => AuthRemoteDataSource(sl()),
  );
  sl.registerLazySingleton<AuthRepository>(
    () => AuthRepositoryImpl(remote: sl(), storage: sl()),
  );
  sl.registerFactory<AuthBloc>(
    () => AuthBloc(
      repository: sl(),
      storage: sl(),
      localAuth: sl(),
    ),
  );

  // Feature APIs
  sl.registerLazySingleton<EmployeeApi>(() => EmployeeApi(sl()));
  sl.registerLazySingleton<InternExpenseApi>(() => InternExpenseApi(sl()));
  sl.registerLazySingleton<AttendanceApi>(() => AttendanceApi(sl()));
  sl.registerLazySingleton<LeaveApi>(() => LeaveApi(sl()));
  sl.registerLazySingleton<ApprovalApi>(() => ApprovalApi(sl()));
  sl.registerLazySingleton<DashboardApi>(() => DashboardApi(sl(), sl()));
  sl.registerLazySingleton<DwpApi>(() => DwpApi(sl()));
  sl.registerLazySingleton<PayrollApi>(() => PayrollApi(sl()));
  sl.registerLazySingleton<JusticeApi>(() => JusticeApi(sl()));
  sl.registerLazySingleton<FieldApi>(() => FieldApi(sl()));
  sl.registerLazySingleton<SalesApi>(() => SalesApi(sl()));
  sl.registerLazySingleton<VerificationApi>(() => VerificationApi(sl()));
  sl.registerLazySingleton<LmsApi>(() => LmsApi(sl()));
  sl.registerLazySingleton<ExamApi>(() => ExamApi(sl()));
  sl.registerLazySingleton<TrainerApi>(() => TrainerApi(sl()));
  sl.registerLazySingleton<PerformanceApi>(() => PerformanceApi(sl()));
  sl.registerLazySingleton<ReportsApi>(() => ReportsApi(sl()));
  sl.registerLazySingleton<PolishApi>(() => PolishApi(sl()));
  sl.registerLazySingleton<LaunchApi>(() => LaunchApi(sl()));

  // Per-department mobile module whitelist (caches the More-menu gating
  // decision in SharedPreferences and refreshes from the API on launch).
  sl.registerSingleton<EnabledModulesService>(
    EnabledModulesService(sl<Dio>(), sl<SharedPreferences>()),
  );
}
