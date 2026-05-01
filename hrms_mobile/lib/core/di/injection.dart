import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:get_it/get_it.dart';
import 'package:local_auth/local_auth.dart';

import '../../features/auth/data/datasources/auth_remote_datasource.dart';
import '../../features/auth/data/repositories/auth_repository_impl.dart';
import '../../features/auth/domain/repositories/auth_repository.dart';
import '../../features/auth/presentation/bloc/auth_bloc.dart';
import '../network/dio_client.dart';
import '../storage/secure_storage.dart';

final GetIt sl = GetIt.instance;

Future<void> setupDependencies() async {
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
}
