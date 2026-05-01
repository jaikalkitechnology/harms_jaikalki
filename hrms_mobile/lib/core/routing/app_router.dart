import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/presentation/bloc/auth_bloc.dart';
import '../../features/auth/presentation/pages/login_page.dart';
import '../../features/dashboard/dashboard_page.dart';
import '../../features/splash/splash_page.dart';
import '../di/injection.dart';

class AppRoutes {
  AppRoutes._();
  static const splash = '/';
  static const login = '/login';
  static const dashboard = '/dashboard';
  static const directorDashboard = '/director/dashboard';
  static const hrDashboard = '/hr/dashboard';
  static const managerDashboard = '/manager/dashboard';
  static const employeeDashboard = '/employee/dashboard';

  /// Map a role code → role-specific dashboard route. Falls back to /dashboard.
  static String dashboardFor(String? role) {
    switch (role) {
      case 'director':
      case 'super_admin':
        return directorDashboard;
      case 'hr':
        return hrDashboard;
      case 'manager':
        return managerDashboard;
      case 'employee':
      case 'intern':
      case 'trainer':
      case 'field':
        return employeeDashboard;
      default:
        return dashboard;
    }
  }
}

GoRouter buildRouter(AuthBloc authBloc) {
  return GoRouter(
    initialLocation: AppRoutes.splash,
    refreshListenable: _BlocStream(authBloc.stream),
    redirect: (context, state) {
      final auth = authBloc.state;
      final loc = state.matchedLocation;
      final loggingIn = loc == AppRoutes.login;
      final onSplash = loc == AppRoutes.splash;

      // Wait for the initial check to finish.
      if (auth.status == AuthStatus.initial ||
          auth.status == AuthStatus.loading) {
        return onSplash ? null : AppRoutes.splash;
      }

      if (!auth.isAuthenticated) {
        return loggingIn ? null : AppRoutes.login;
      }

      // Authenticated — bounce away from login/splash to role dashboard.
      if (loggingIn || onSplash) {
        return AppRoutes.dashboardFor(auth.user?.role);
      }
      return null;
    },
    routes: [
      GoRoute(
        path: AppRoutes.splash,
        builder: (_, __) => const SplashPage(),
      ),
      GoRoute(
        path: AppRoutes.login,
        builder: (_, __) => BlocProvider<AuthBloc>.value(
          value: sl<AuthBloc>(),
          child: const LoginPage(),
        ),
      ),
      GoRoute(
        path: AppRoutes.dashboard,
        builder: (_, __) => const DashboardPage(),
      ),
      GoRoute(
        path: AppRoutes.directorDashboard,
        builder: (_, __) => const DashboardPage(roleLabel: 'Director'),
      ),
      GoRoute(
        path: AppRoutes.hrDashboard,
        builder: (_, __) => const DashboardPage(roleLabel: 'HR'),
      ),
      GoRoute(
        path: AppRoutes.managerDashboard,
        builder: (_, __) => const DashboardPage(roleLabel: 'Manager'),
      ),
      GoRoute(
        path: AppRoutes.employeeDashboard,
        builder: (_, __) => const DashboardPage(roleLabel: 'Employee'),
      ),
    ],
  );
}

class _BlocStream extends ChangeNotifier {
  _BlocStream(Stream<dynamic> stream) {
    _sub = stream.listen((_) => notifyListeners());
  }
  late final StreamSubscription<dynamic> _sub;

  @override
  void dispose() {
    _sub.cancel();
    super.dispose();
  }
}
