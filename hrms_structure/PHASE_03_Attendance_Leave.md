# Phase 3: Attendance & Leave Management

**Duration:** 7-10 days
**Hours:** 70
**Priority:** CRITICAL
**Depends on:** Phase 2 (Employee Management)

---

## Objective

Build attendance tracking with geo-fencing + selfie, comprehensive leave management with policies, balances, and approval workflow.

## Deliverables

- ✅ Geo-fenced attendance check-in/check-out
- ✅ Selfie capture for WFH attendance
- ✅ Multiple shift management
- ✅ Leave policies & balances
- ✅ Leave application workflow
- ✅ Manager approval system
- ✅ Holiday calendar (regional)
- ✅ Comp-off management
- ✅ Mobile-first UI for all

---

## Tasks

### Task 3.1: Database Models (5h)

**Attendance:**
```python
- Attendance (id, employee_id, date, check_in, check_out,
              check_in_lat, check_in_lng, check_in_selfie_url,
              check_out_lat, check_out_lng, status,
              source, work_mode, total_hours)

- Shift (id, name, start_time, end_time, break_duration)

- EmployeeShift (employee_id, shift_id, effective_from)

- AttendanceRegularization (id, attendance_id, requested_by,
                           reason, status, approver_id)
```

**Leave:**
```python
- LeaveType (id, name, code, days_per_year,
             carry_forward, encashable, applicable_to)

- LeaveBalance (id, employee_id, leave_type_id, year,
                allocated, used, balance, carried_forward)

- LeaveRequest (id, employee_id, leave_type_id, from_date,
                to_date, days, reason, status, applied_at,
                approver_id, approved_at, comments)

- Holiday (id, date, name, type, is_optional, location)

- CompOff (id, employee_id, earned_date, expiry_date,
           days, status)
```

### Task 3.2: Migrations & Seed (2h)

**Leave Types:**
- CL (Casual Leave) - 12/year
- SL (Sick Leave) - 12/year
- PL (Privilege/Earned) - 18/year, carry forward
- ML (Maternity) - 26 weeks (182 days)
- PTL (Paternity) - 15 days
- BL (Bereavement) - 5 days

**Holidays 2026** (sample):
- 1 Jan - New Year
- 26 Jan - Republic Day
- 25 Mar - Holi
- 14 Apr - Ambedkar Jayanti
- 1 May - Labour Day
- 15 Aug - Independence Day
- 2 Oct - Gandhi Jayanti
- 1 Nov - Diwali

**Shifts:**
- General (9 AM - 6 PM)
- Early (6 AM - 3 PM)
- Late (2 PM - 11 PM)
- Night (10 PM - 7 AM)

### Task 3.3: Geo-Fencing Utility (4h)

`app/utils/geo.py`:
- Calculate distance between coordinates
- Verify within radius (configurable)
- Mock GPS detection logic

### Task 3.4: Attendance Service (6h)

`app/services/attendance_service.py`:
- `check_in(employee, lat, lng, selfie, work_mode)`
- `check_out(employee, lat, lng)`
- `get_attendance(employee_id, date_range)`
- `get_team_attendance(manager_id, date)`
- `regularize_attendance(att_id, reason)`
- `calculate_attendance_summary(employee, month)`
- `auto_mark_absent()` - Cron job

### Task 3.5: Attendance API (4h)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/attendance/check-in` | Geo + selfie validation |
| POST | `/attendance/check-out` | End shift |
| GET | `/attendance/me` | My attendance |
| GET | `/attendance/me/summary` | Monthly summary |
| GET | `/attendance/team` | Manager view |
| GET | `/attendance/report` | HR/Director |
| POST | `/attendance/regularize` | Request correction |
| POST | `/attendance/regularize/{id}/approve` | Approve correction |

### Task 3.6: Leave Service (6h)

`app/services/leave_service.py`:
- `apply_leave(employee, type, from_date, to_date, reason)`
- `cancel_leave_request(id)`
- `approve_leave(leave_id, approver)`
- `reject_leave(leave_id, approver, reason)`
- `get_leave_balance(employee, year)`
- `get_leave_requests(employee, status)`
- `get_pending_approvals(manager)`
- `get_team_calendar(manager, month)`
- `validate_leave_request(employee, dates, type)`
- Auto-deduct from balance on approval

### Task 3.7: Leave API (4h)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/leaves/types` | All leave types |
| GET | `/leaves/balance` | My balance |
| POST | `/leaves/apply` | New request |
| GET | `/leaves/requests` | My requests |
| DELETE | `/leaves/requests/{id}` | Cancel |
| GET | `/leaves/pending-approvals` | Manager inbox |
| POST | `/leaves/{id}/approve` | Approve |
| POST | `/leaves/{id}/reject` | Reject |
| GET | `/leaves/calendar` | Team calendar |
| GET | `/leaves/holidays` | Holiday list |

### Task 3.8: Comp-Off APIs (3h)

- Earn comp-off (working holiday/weekend)
- Auto-expire after 90 days
- Convert to leave
- Manager approval

### Task 3.9: Backend Tests (4h)

- Check-in within geo-fence ✓
- Check-in outside geo-fence ✗
- Mock GPS detection
- Leave balance check
- Leave overlap detection
- Approval workflow
- Permission scopes

### Task 3.10: Flutter - Attendance UI (8h)

```
features/attendance/
├── data/
├── domain/
└── presentation/
    ├── bloc/
    │   ├── attendance_bloc.dart
    │   └── attendance_history_bloc.dart
    └── pages/
        ├── attendance_home_page.dart
        ├── check_in_page.dart
        ├── attendance_history_page.dart
        ├── team_attendance_page.dart
        └── regularization_page.dart
```

**Features:**
- Quick check-in button on home
- Camera for selfie
- GPS location
- Real-time location accuracy
- Check-out button
- Today's status display
- History view (calendar)
- Regularization request

### Task 3.11: Flutter - Leave UI (8h)

```
features/leave/
└── presentation/
    ├── bloc/
    └── pages/
        ├── leave_home_page.dart
        ├── apply_leave_page.dart
        ├── leave_balance_page.dart
        ├── leave_history_page.dart
        ├── leave_calendar_page.dart
        └── pending_approvals_page.dart
```

**Apply Leave Screen:**
- Leave type dropdown
- From-To date picker
- Auto-calculate days
- Show balance check
- Reason field
- Half-day option
- File attachment (medical certificate)
- Submit with confirmation

### Task 3.12: Flutter - Manager Approval (5h)

- Pending approvals list
- Swipe right to approve
- Swipe left to reject
- Bulk approve
- Comments while approving
- Push notifications

### Task 3.13: Geolocation Setup (3h)

Use `geolocator`:
- Request location permissions
- Get current position
- Stream updates
- Handle permission denied

### Task 3.14: Camera Integration (4h)

Use `image_picker`:
- Front camera for selfie
- Image compression
- Upload to backend
- Cache locally

### Task 3.15: Push Notifications (4h)

Setup Firebase Cloud Messaging:
- Token registration
- Leave applied (to manager)
- Leave approved/rejected (to employee)
- Attendance reminder

---

## Acceptance Criteria

### Backend
- [ ] Check-in validates location within radius
- [ ] Mock GPS detection works
- [ ] Selfie URL stored
- [ ] Leave application validates balance
- [ ] Leave overlap detected
- [ ] Approval workflow correct
- [ ] Balance auto-deducted on approval
- [ ] Holiday calendar served correctly

### Frontend
- [ ] Check-in works with GPS + selfie
- [ ] Location permission flow smooth
- [ ] Camera captures selfie
- [ ] Leave application form complete
- [ ] Leave balance displayed correctly
- [ ] Manager can approve/reject
- [ ] Push notifications received

---

## Validation

```bash
# Check-in
curl -X POST http://localhost:8000/v1/attendance/check-in \
  -H "Authorization: Bearer TOKEN" \
  -F "lat=19.0760" \
  -F "lng=72.8777" \
  -F "selfie=@selfie.jpg" \
  -F "work_mode=office"

# Apply leave
curl -X POST http://localhost:8000/v1/leaves/apply \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "leave_type_id": 1,
    "from_date": "2026-05-15",
    "to_date": "2026-05-16",
    "reason": "Personal work"
  }'

# Get balance
curl http://localhost:8000/v1/leaves/balance \
  -H "Authorization: Bearer TOKEN"
```

---

## Claude Code Prompt

```
Read HRMS_Architecture.md sections 8.2 (Attendance) and 8.3 (Leave Management).

Implement Phase 3 (Attendance & Leave) as described in PHASE_03_Attendance_Leave.md.

Backend:
1. Create attendance models with geo-tracking
2. Implement geo-fencing logic with distance calculation
3. Detect mock GPS attempts
4. Build leave management with balance tracking
5. Create approval workflow
6. Setup holiday calendar
7. Comp-off management

Flutter:
1. Quick check-in with GPS + selfie
2. Attendance history with calendar view
3. Apply leave with date picker
4. Leave balance display
5. Manager approval inbox with swipe gestures
6. Push notifications setup

Make sure:
- Location permissions handled gracefully
- Camera capture works smoothly
- Geo-fence validation strict
- Leave overlaps prevented
- Balance auto-deducted

Test full flow: employee applies → manager approves → balance updated.
```

---

## Next Phase

➡️ **Phase 4: Universal Approval Engine** (PHASE_04_Approvals.md)
