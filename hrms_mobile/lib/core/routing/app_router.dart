import 'package:go_router/go_router.dart';

import '../../features/auth/login_page.dart';
import '../../features/dashboard/dashboard_page.dart';
import '../../features/splash/splash_page.dart';

class AppRoutes {
  AppRoutes._();
  static const splash = '/';
  static const login = '/login';
  static const dashboard = '/dashboard';
}

final GoRouter appRouter = GoRouter(
  initialLocation: AppRoutes.splash,
  routes: [
    GoRoute(
      path: AppRoutes.splash,
      builder: (_, __) => const SplashPage(),
    ),
    GoRoute(
      path: AppRoutes.login,
      builder: (_, __) => const LoginPage(),
    ),
    GoRoute(
      path: AppRoutes.dashboard,
      builder: (_, __) => const DashboardPage(),
    ),
  ],
);
