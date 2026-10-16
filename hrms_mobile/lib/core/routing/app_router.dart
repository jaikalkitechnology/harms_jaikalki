import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../features/approvals/pages/approvals_inbox_page.dart';
import '../../features/attendance/pages/attendance_home_page.dart';
import '../../features/auth/presentation/bloc/auth_bloc.dart';
import '../../features/auth/presentation/pages/login_page.dart';
import '../../features/dwp/pages/dwp_form_page.dart';
import '../../features/dwp/pages/dwp_home_page.dart';
import '../../features/employees/pages/employee_detail_page.dart';
import '../../features/employees/pages/employees_list_page.dart';
import '../../features/exam/pages/exam_list_page.dart' deferred as exam_list;
import '../../features/exam/pages/exam_taking_page.dart'
    deferred as exam_taking;
import '../../features/exam/pages/my_certificates_page.dart'
    deferred as my_certificates;
import '../../features/polish/data/polish_models.dart';
import '../../features/visitors/pages/visitor_pass_page.dart'
    deferred as visitor_pass;
import '../../features/visitors/pages/visitor_register_page.dart'
    deferred as visitor_register;
import '../../features/visitors/pages/visitor_scan_page.dart'
    deferred as visitor_scan;
import '../../features/visitors/pages/visitors_home_page.dart'
    deferred as visitors_home;
import '../../features/launch/pages/resignation_page.dart';
import '../../features/launch/pages/team_exits_page.dart';
import '../../features/field/pages/field_home_page.dart' deferred as field_home;
import '../../features/field/pages/field_live_map_page.dart'
    deferred as field_live_map;
import '../../features/field/pages/field_visit_page.dart'
    deferred as field_visit;
import '../../features/intern_expenses/pages/intern_expenses_page.dart';
import '../../features/justice/pages/justice_gate_page.dart'
    deferred as justice_gate;
import '../../features/justice/pages/justice_resources_page.dart'
    deferred as justice_resources;
import '../../features/justice/pages/justice_submit_page.dart'
    deferred as justice_submit;
import '../../features/leaves/pages/leaves_home_page.dart';
import '../../features/leaves/pages/manager_inbox_page.dart';
import '../../features/lms/pages/badges_page.dart' deferred as badges;
import '../../features/lms/pages/course_detail_page.dart'
    deferred as course_detail;
import '../../features/lms/pages/lms_home_page.dart' deferred as lms_home;
import '../../features/onboarding/onboarding_page.dart';
import '../../features/payroll/pages/payroll_home_page.dart';
import '../../features/performance/pages/feedback_inbox_page.dart'
    deferred as feedback_inbox;
import '../../features/launch/pages/forgot_password_page.dart';
import '../../features/launch/pages/mfa_setup_page.dart';
import '../../features/launch/pages/notifications_page.dart';
import '../../features/performance/pages/goals_page.dart' deferred as goals;
import '../../features/polish/pages/book_room_page.dart' deferred as book_room;
import '../../features/polish/pages/jobs_page.dart' deferred as jobs;
import '../../features/polish/pages/my_assets_page.dart' deferred as my_assets;
import '../../features/reports/pages/director_dashboard_page.dart'
    deferred as director_dashboard;
import '../../features/sales/pages/lead_detail_page.dart'
    deferred as lead_detail;
import '../../features/sales/pages/my_leads_page.dart' deferred as my_leads;
import '../../features/sales/pages/new_lead_page.dart' deferred as new_lead;
import '../../features/sales/pages/sales_pipeline_page.dart'
    deferred as sales_pipeline;
import '../../features/sales/pages/sales_targets_page.dart'
    deferred as sales_targets;
import '../../features/trainer/pages/sessions_page.dart' deferred as sessions;
import '../../features/trainer/pages/trainer_marketplace_page.dart'
    deferred as trainer_marketplace;
import '../../features/verification/pages/verification_form_page.dart'
    deferred as verification_form;
import '../../features/verification/pages/verification_queue_page.dart'
    deferred as verification_queue;
import '../../features/settings/cubit/settings_cubit.dart';
import '../../features/settings/pages/settings_page.dart';
import '../../features/shell/home_shell.dart';
import '../../features/splash/splash_page.dart';
import '../di/injection.dart';
import 'deferred_page.dart';

class AppRoutes {
  AppRoutes._();
  static const splash = '/';
  static const onboarding = '/onboarding';
  static const login = '/login';
  static const home = '/home';
  // Legacy aliases — all roles land on /home (the bottom-nav shell).
  static const dashboard = home;
  static const hrDashboard = home;
  static const managerDashboard = home;
  static const employeeDashboard = home;

  static const employees = '/employees';
  static const internExpenses = '/intern/expenses';
  static const attendance = '/attendance';
  static const leaves = '/leaves';
  static const managerInbox = '/manager/inbox';
  static const approvalsInbox = '/approvals';
  static const settings = '/settings';
  static const dwp = '/dwp';
  static const dwpMorning = '/dwp/morning';
  static const dwpEod = '/dwp/eod';
  static const payroll = '/payroll';
  static const justice = '/justice';
  static const justiceSubmit = '/justice/submit';
  static const justiceResources = '/justice/resources';
  static const fieldHome = '/field';
  static const fieldLiveMap = '/field/live-map';
  static const salesPipeline = '/sales/pipeline';
  static const salesTargets = '/sales/targets';
  static const myLeads = '/sales/leads';
  static const newLead = '/sales/leads/new';
  static const verificationQueue = '/verification';
  static const lmsHome = '/lms';
  static const lmsBadges = '/lms/badges';
  static const exams = '/exams';
  static const myCertificates = '/exams/me/certificates';
  static const visitors = '/visitors';
  static const visitorRegister = '/visitors/new';
  static const visitorScan = '/visitors/scan';
  static const visitorPass = '/visitors/pass';
  static const resignation = '/resignation';
  static const teamExits = '/team-exits';
  static const trainers = '/trainers';
  static const trainerSessions = '/trainers/sessions';
  static const myGoals = '/performance/goals';
  static const feedbackInbox = '/performance/feedback';
  static const directorDashboard = '/reports/dashboard';
  static const myAssets = '/polish/assets';
  static const bookRoom = '/polish/rooms';
  static const browseJobs = '/polish/jobs';
  static const notifications = '/notifications';
  static const mfaSetup = '/mfa/setup';
  static const forgotPassword = '/forgot-password';

  static String dashboardFor(String? role) => home;
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
      final onOnboarding = loc == AppRoutes.onboarding;
      final onForgotPassword = loc == AppRoutes.forgotPassword;

      if (auth.status == AuthStatus.initial ||
          auth.status == AuthStatus.loading) {
        return onSplash ? null : AppRoutes.splash;
      }

      if (!auth.isAuthenticated) {
        // First-launch onboarding gate before login. Forgot-password is
        // also reachable without auth.
        if (!onOnboarding && !loggingIn && !onForgotPassword) {
          final onboarded = sl<SettingsCubit>().state.onboardingCompleted;
          if (!onboarded) return AppRoutes.onboarding;
          return AppRoutes.login;
        }
        return null;
      }

      if (loggingIn || onSplash || onOnboarding || onForgotPassword) {
        return AppRoutes.home;
      }
      return null;
    },
    routes: [
      GoRoute(
        path: AppRoutes.splash,
        builder: (_, __) => const SplashPage(),
      ),
      GoRoute(
        path: AppRoutes.onboarding,
        builder: (_, __) => BlocProvider.value(
          value: sl<SettingsCubit>(),
          child: const OnboardingPage(),
        ),
      ),
      GoRoute(
        path: AppRoutes.login,
        // The root AuthBloc is provided at MaterialApp level — don't wrap
        // again or the login form would dispatch to a stale factory bloc.
        builder: (_, __) => const LoginPage(),
      ),
      GoRoute(
        path: AppRoutes.home,
        builder: (_, __) => const HomeShell(),
      ),
      GoRoute(
        path: AppRoutes.settings,
        builder: (_, __) => BlocProvider.value(
          value: sl<SettingsCubit>(),
          child: const SettingsPage(),
        ),
      ),
      GoRoute(
        path: AppRoutes.employees,
        builder: (_, __) => const EmployeesListPage(),
      ),
      GoRoute(
        path: '/employees/:id',
        builder: (_, state) => EmployeeDetailPage(
          employeeId: int.parse(state.pathParameters['id']!),
        ),
      ),
      GoRoute(
        path: AppRoutes.internExpenses,
        builder: (_, __) => const InternExpensesPage(),
      ),
      GoRoute(
        path: AppRoutes.attendance,
        builder: (_, __) => const AttendanceHomePage(),
      ),
      GoRoute(
        path: AppRoutes.leaves,
        builder: (_, __) => const LeavesHomePage(),
      ),
      GoRoute(
        path: AppRoutes.managerInbox,
        builder: (_, __) => const ManagerInboxPage(),
      ),
      GoRoute(
        path: AppRoutes.approvalsInbox,
        builder: (_, __) => const ApprovalsInboxPage(),
      ),
      GoRoute(
        path: AppRoutes.dwp,
        builder: (_, __) => const DwpHomePage(),
      ),
      GoRoute(
        path: AppRoutes.dwpMorning,
        builder: (_, __) => const DwpFormPage(type: 'morning'),
      ),
      GoRoute(
        path: AppRoutes.dwpEod,
        builder: (_, __) => const DwpFormPage(type: 'eod'),
      ),
      GoRoute(
        path: AppRoutes.payroll,
        builder: (_, __) => const PayrollHomePage(),
      ),
      GoRoute(
        path: AppRoutes.justice,
        builder: (_, __) => DeferredPage(
            justice_gate.loadLibrary, (_) => justice_gate.JusticeGatePage()),
      ),
      GoRoute(
        path: AppRoutes.justiceSubmit,
        builder: (_, __) => DeferredPage(justice_submit.loadLibrary,
            (_) => justice_submit.JusticeSubmitPage()),
      ),
      GoRoute(
        path: AppRoutes.justiceResources,
        builder: (_, __) => DeferredPage(justice_resources.loadLibrary,
            (_) => justice_resources.JusticeResourcesPage()),
      ),
      GoRoute(
        path: AppRoutes.fieldHome,
        builder: (_, __) => DeferredPage(
            field_home.loadLibrary, (_) => field_home.FieldHomePage()),
      ),
      GoRoute(
        path: AppRoutes.fieldLiveMap,
        builder: (_, __) => DeferredPage(field_live_map.loadLibrary,
            (_) => field_live_map.FieldLiveMapPage()),
      ),
      GoRoute(
        path: '/field/visit/:jobId',
        builder: (_, state) => DeferredPage(
            field_visit.loadLibrary,
            (_) => field_visit.FieldVisitPage(
                  jobId: int.parse(state.pathParameters['jobId']!),
                )),
      ),
      GoRoute(
        path: AppRoutes.salesPipeline,
        builder: (_, __) => DeferredPage(sales_pipeline.loadLibrary,
            (_) => sales_pipeline.SalesPipelinePage()),
      ),
      GoRoute(
        path: AppRoutes.salesTargets,
        builder: (_, __) => DeferredPage(
            sales_targets.loadLibrary, (_) => sales_targets.SalesTargetsPage()),
      ),
      GoRoute(
        path: AppRoutes.myLeads,
        builder: (_, __) =>
            DeferredPage(my_leads.loadLibrary, (_) => my_leads.MyLeadsPage()),
      ),
      GoRoute(
        path: AppRoutes.newLead,
        builder: (_, __) =>
            DeferredPage(new_lead.loadLibrary, (_) => new_lead.NewLeadPage()),
      ),
      GoRoute(
        path: '/sales/leads/:id',
        builder: (_, state) => DeferredPage(
            lead_detail.loadLibrary,
            (_) => lead_detail.LeadDetailPage(
                  leadId: int.parse(state.pathParameters['id']!),
                )),
      ),
      GoRoute(
        path: AppRoutes.verificationQueue,
        builder: (_, __) => DeferredPage(verification_queue.loadLibrary,
            (_) => verification_queue.VerificationQueuePage()),
      ),
      GoRoute(
        path: '/verification/:id',
        builder: (_, state) => DeferredPage(
            verification_form.loadLibrary,
            (_) => verification_form.VerificationFormPage(
                  verificationId: int.parse(state.pathParameters['id']!),
                )),
      ),
      GoRoute(
        path: AppRoutes.lmsHome,
        builder: (_, __) =>
            DeferredPage(lms_home.loadLibrary, (_) => lms_home.LmsHomePage()),
      ),
      GoRoute(
        path: AppRoutes.lmsBadges,
        builder: (_, __) =>
            DeferredPage(badges.loadLibrary, (_) => badges.BadgesPage()),
      ),
      GoRoute(
        path: '/lms/course/:id',
        builder: (_, state) => DeferredPage(
            course_detail.loadLibrary,
            (_) => course_detail.CourseDetailPage(
                  courseId: int.parse(state.pathParameters['id']!),
                )),
      ),
      GoRoute(
        path: AppRoutes.exams,
        builder: (_, __) => DeferredPage(
            exam_list.loadLibrary, (_) => exam_list.ExamListPage()),
      ),
      GoRoute(
        path: '/exams/:id/take',
        builder: (_, state) => DeferredPage(
            exam_taking.loadLibrary,
            (_) => exam_taking.ExamTakingPage(
                  examId: int.parse(state.pathParameters['id']!),
                )),
      ),
      GoRoute(
        path: AppRoutes.myCertificates,
        builder: (_, __) => DeferredPage(my_certificates.loadLibrary,
            (_) => my_certificates.MyCertificatesPage()),
      ),
      GoRoute(
        path: AppRoutes.visitors,
        builder: (_, __) => DeferredPage(
            visitors_home.loadLibrary, (_) => visitors_home.VisitorsHomePage()),
      ),
      GoRoute(
        path: AppRoutes.resignation,
        builder: (_, __) => const ResignationPage(),
      ),
      GoRoute(
        path: AppRoutes.teamExits,
        builder: (_, __) => const TeamExitsPage(),
      ),
      GoRoute(
        path: AppRoutes.visitorRegister,
        builder: (_, __) => DeferredPage(visitor_register.loadLibrary,
            (_) => visitor_register.VisitorRegisterPage()),
      ),
      GoRoute(
        path: AppRoutes.visitorScan,
        builder: (_, __) => DeferredPage(
            visitor_scan.loadLibrary, (_) => visitor_scan.VisitorScanPage()),
      ),
      GoRoute(
        path: '${AppRoutes.visitorPass}/:id',
        builder: (_, state) {
          final extra = state.extra;
          if (extra is Visitor) {
            return DeferredPage(visitor_pass.loadLibrary,
                (_) => visitor_pass.VisitorPassPage(visitor: extra));
          }
          return const Scaffold(
            body: Center(child: Text('Visitor pass not found')),
          );
        },
      ),
      GoRoute(
        path: AppRoutes.trainers,
        builder: (_, __) => DeferredPage(trainer_marketplace.loadLibrary,
            (_) => trainer_marketplace.TrainerMarketplacePage()),
      ),
      GoRoute(
        path: AppRoutes.trainerSessions,
        builder: (_, __) => DeferredPage(
            sessions.loadLibrary, (_) => sessions.TrainerSessionsPage()),
      ),
      GoRoute(
        path: AppRoutes.myGoals,
        builder: (_, __) =>
            DeferredPage(goals.loadLibrary, (_) => goals.MyGoalsPage()),
      ),
      GoRoute(
        path: AppRoutes.feedbackInbox,
        builder: (_, __) => DeferredPage(feedback_inbox.loadLibrary,
            (_) => feedback_inbox.FeedbackInboxPage()),
      ),
      GoRoute(
        path: AppRoutes.directorDashboard,
        builder: (_, __) => DeferredPage(director_dashboard.loadLibrary,
            (_) => director_dashboard.DirectorDashboardPage()),
      ),
      GoRoute(
        path: AppRoutes.myAssets,
        builder: (_, __) => DeferredPage(
            my_assets.loadLibrary, (_) => my_assets.MyAssetsPage()),
      ),
      GoRoute(
        path: AppRoutes.bookRoom,
        builder: (_, __) => DeferredPage(
            book_room.loadLibrary, (_) => book_room.BookRoomPage()),
      ),
      GoRoute(
        path: AppRoutes.browseJobs,
        builder: (_, __) =>
            DeferredPage(jobs.loadLibrary, (_) => jobs.JobsPage()),
      ),
      GoRoute(
        path: AppRoutes.notifications,
        builder: (_, __) => const NotificationsPage(),
      ),
      GoRoute(
        path: AppRoutes.mfaSetup,
        builder: (_, __) => const MfaSetupPage(),
      ),
      GoRoute(
        path: AppRoutes.forgotPassword,
        builder: (_, __) => const ForgotPasswordPage(),
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
