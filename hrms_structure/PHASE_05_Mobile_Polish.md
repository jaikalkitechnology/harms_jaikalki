# Phase 5: Mobile App MVP Polish

**Duration:** 7-10 days
**Hours:** 80
**Priority:** HIGH
**Depends on:** Phase 4

---

## Objective

Polish the mobile app with role-based dashboards, navigation, notifications, and offline support. Make MVP production-ready.

## Deliverables

- ✅ Role-based home dashboards (Director/HR/Manager/Employee)
- ✅ Bottom navigation with 5 tabs
- ✅ Push notifications fully working
- ✅ Offline mode for critical actions
- ✅ Dark mode
- ✅ Hindi + English support
- ✅ App icon, splash screen, branding
- ✅ Performance optimization

---

## Tasks

### Task 5.1: Role-Based Dashboards (12h)

**Director Dashboard:**
- Headcount widget
- Attrition trend chart
- Pending approvals badge
- Quick stats cards
- Recent activities

**HR Dashboard:**
- Pending approvals
- Birthdays/anniversaries today
- Probation ending this month
- Document expiry alerts
- Compliance status

**Manager Dashboard:**
- Team attendance %
- Pending leave approvals
- Team strength
- This week calendar

**Employee Dashboard:**
- Today's check-in status
- Leave balance
- Next payday countdown
- Pending tasks
- Birthday wishes

### Task 5.2: Bottom Navigation (4h)

5 tabs:
1. Home (role-specific dashboard)
2. Approvals (universal inbox with badge)
3. Attendance (quick check-in)
4. More (all features menu)
5. Profile

### Task 5.3: More Menu Page (3h)

Grid of all features with icons:
- Leave
- Documents
- Team Directory
- Org Chart
- Settings
- Help

### Task 5.4: Notifications System (8h)

Firebase Cloud Messaging:
- Token registration
- Topic subscription (department-wise)
- Foreground handling
- Background handling
- Deep linking from notification
- Notification center in app
- Mark as read
- Notification preferences

### Task 5.5: Offline Mode (10h)

Use Hive for local storage:
- Cache user data
- Cache employee directory
- Queue actions when offline:
  - Apply leave
  - Mark attendance
  - Submit forms
- Sync when online
- Show offline indicator
- Conflict resolution

### Task 5.6: Theme & Dark Mode (4h)

- Light theme polished
- Dark theme implemented
- System theme detection
- Manual toggle in settings
- Smooth transitions

### Task 5.7: Localization (6h)

Setup `flutter_localizations`:
- English (default)
- Hindi
- All strings in `app_en.arb` and `app_hi.arb`
- Language picker in settings
- RTL support ready

### Task 5.8: Splash & Onboarding (4h)

- Animated splash screen
- First-time onboarding (3 screens)
- Permission requests
- Login screen redirect

### Task 5.9: Branding (3h)

- App icon (multiple sizes)
- App name customization
- Splash logo
- Loading animations

### Task 5.10: Performance (8h)

- Image lazy loading
- List pagination
- Skeleton loaders
- Code splitting
- Reduce app size
- Memory leak fixes

### Task 5.11: Error Handling (4h)

- Global error boundary
- Network error UI
- Retry mechanisms
- User-friendly error messages
- Crash reporting (Sentry)

### Task 5.12: Settings Page (4h)

- Profile quick view
- Theme toggle
- Language selector
- Notification preferences
- Biometric setup
- Privacy policy
- About app
- Logout

### Task 5.13: Testing (10h)

- Widget tests
- Integration tests
- Bloc tests
- Manual QA on multiple devices
- Different screen sizes

---

## Claude Code Prompt

```
Implement Phase 5 (Mobile App Polish).

Build:
1. Role-based dashboards for Director/HR/Manager/Employee
2. Bottom navigation with 5 tabs
3. Universal "More" menu
4. Push notifications with FCM
5. Offline mode with Hive
6. Dark mode complete
7. Hindi localization
8. Splash + onboarding
9. Settings page
10. Performance optimization

Make MVP production-ready. Test on real devices.
```

---

## Next: Phase 6 - Daily Work Planning
