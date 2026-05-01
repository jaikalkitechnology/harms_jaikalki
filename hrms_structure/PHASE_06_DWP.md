# Phase 6: Daily Work Planning (DWP)

**Duration:** 7 days
**Hours:** 65
**Priority:** HIGH
**Depends on:** Phase 5

---

## Objective

Build Daily Work Planning module - employees submit morning plan + EOD summary daily, with department-specific templates.

## Reference

See HRMS_Architecture.md → Section 12: Daily Work Planning Module

## Deliverables

- ✅ Morning plan submission (SOD)
- ✅ EOD work summary
- ✅ 9 department templates (configurable)
- ✅ Voice notes + photos support
- ✅ Auto-link morning → EOD
- ✅ Manager team dashboard
- ✅ Blocker tracking
- ✅ Status tags
- ✅ Submission streaks
- ✅ Comments/kudos

---

## Tasks

### Task 6.1: Database Models (4h)

```python
- DwpTemplate (id, department_id, name, type, is_active)
- DwpTemplateField (id, template_id, field_name, field_type,
                    is_required, options, display_order)
- DwpSubmission (id, employee_id, template_id, type,
                 date, submitted_at, total_hours, mood_rating)
- DwpSubmissionData (id, submission_id, field_id, value, file_url)
- DwpComment (id, submission_id, commented_by, comment, is_kudos)
- DwpReminderSetting (id, department_id, type, reminder_times,
                      deadline_time)
- DwpTag (id, name, color, department_id)
- DwpSubmissionTag (submission_id, tag_id)
```

### Task 6.2: Default Templates Seed (4h)

Create 9 department templates:
1. IT/Development
2. Sales
3. Customer Support
4. Design
5. Marketing
6. HR/Admin
7. Cleaning/Housekeeping
8. Field Force
9. Production

Each with morning + EOD variants.

### Task 6.3: DWP Services (6h)

- `get_today_template(employee, type)` - morning or EOD
- `submit_dwp(employee, template, data)`
- `get_my_submissions(employee, date_range)`
- `get_team_submissions(manager, date)`
- `get_blockers(manager)`
- `add_comment(submission, comment, is_kudos)`
- `calculate_streak(employee)`

### Task 6.4: Auto-Link Logic (3h)

- Yesterday's "tomorrow plan" → Today's morning
- Today's morning → Today's EOD (pre-fill completed status)
- Easy edit before submit

### Task 6.5: APIs (5h)

| Method | Endpoint |
|--------|----------|
| GET | `/dwp/template/morning` |
| GET | `/dwp/template/eod` |
| POST | `/dwp/morning/submit` |
| POST | `/dwp/eod/submit` |
| GET | `/dwp/me/today` |
| GET | `/dwp/me/history` |
| GET | `/dwp/team/today` |
| GET | `/dwp/team/blockers` |
| POST | `/dwp/{id}/comment` |
| POST | `/dwp/{id}/acknowledge` |

### Task 6.6: Template Builder API (4h)

HR can:
- Create templates
- Add/edit fields
- Configure reminders
- Manage tags

### Task 6.7: Reminder System (4h)

Celery tasks:
- Morning reminder (9:15 AM configurable)
- EOD reminder (6:00 PM configurable)
- Late submission alert to manager
- Streak notifications

### Task 6.8: Flutter - DWP Feature (12h)

```
features/dwp/
└── presentation/
    ├── pages/
    │   ├── dwp_home_page.dart
    │   ├── morning_plan_page.dart
    │   ├── eod_summary_page.dart
    │   ├── dwp_history_page.dart
    │   └── team_dwp_page.dart
```

**Morning Plan Screen:**
- Date display
- Project dropdown
- Tasks list (add/edit/remove)
- Hours estimate per task
- Help needed text
- Status tag (🟢🟡🔴)
- Submit button

**EOD Summary Screen:**
- Plan vs Actual auto-display
- Mark completion %
- Blockers field
- Hours actual
- Mood rating
- Tomorrow's plan
- Submit

### Task 6.9: Voice Notes (3h)

Use `record` package:
- Record audio
- Playback
- Upload as file
- Display duration

### Task 6.10: Photos (3h)

- Multi-image picker
- Compression
- Upload
- Gallery view

### Task 6.11: Manager Team View (5h)

- Today's submissions list
- Blockers highlighted
- Filter by department
- Submission rate %
- Click to view details
- Add comments

### Task 6.12: Streaks & Gamification (4h)

- Daily streak counter
- Achievement badges
- Monthly leaderboard (optional)
- Notification on streak milestones

### Task 6.13: Tests (4h)

---

## Claude Code Prompt

```
Read HRMS_Architecture.md Section 12 (Daily Work Planning Module).

Implement Phase 6 (DWP) as described in PHASE_06_DWP.md.

Build:
1. Configurable templates per department
2. Morning + EOD submission flow
3. Auto-linking logic
4. Voice notes + photo support
5. Manager team dashboard with blocker view
6. Reminder system with Celery
7. Streaks and gamification

Make sure:
- Default 9 templates created via seed
- Templates editable by HR (no-code builder)
- Mobile UX smooth (3-5 min submission)
- Offline support for submissions

Test all departments' flows.
```

---

## Next: Phase 7 - Payroll
