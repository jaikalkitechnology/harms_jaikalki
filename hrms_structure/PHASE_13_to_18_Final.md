# Phase 13: Examination System

**Duration:** 7-10 days
**Hours:** 75
**Priority:** MEDIUM
**Depends on:** Phase 12 (LMS)

---

## Objective

Build MCQ-based examination system with question bank, anti-cheating, auto-evaluation, and certificate generation.

## Reference

See HRMS_Architecture.md → Section 15 → Examination System

## Deliverables

- ✅ Question bank (department/topic/difficulty)
- ✅ MCQ exam engine (6 question types)
- ✅ 4 exam modes (Practice/Assessment/Certification/Mandatory)
- ✅ Anti-cheating (full-screen lock, tab detection)
- ✅ Auto-evaluation
- ✅ Certificate generation with QR code
- ✅ Department-wise exams
- ✅ Result analytics
- ✅ Bulk question import (CSV)

---

## Tasks

### Task 13.1: Database Models (4h)

```python
- QuestionBank (id, question_text, question_type,
                department_id, topic, difficulty,
                language, marks, time_seconds,
                explanation, status)

- QuestionOption (id, question_id, option_text,
                  is_correct, order)

- Exam (id, title, course_id, department_id,
        total_questions, time_limit_minutes,
        passing_percentage, exam_type,
        question_selection, shuffle_questions,
        attempts_allowed, cooldown_hours,
        anti_cheat_settings, validity_months)

- ExamQuestion (exam_id, question_id, marks_override)

- ExamAttempt (id, exam_id, employee_id, started_at,
               submitted_at, time_taken_seconds,
               total_score, percentage, status,
               passed, attempt_number,
               ip_address, device_info, cheating_flags)

- AttemptAnswer (id, attempt_id, question_id,
                 selected_option_ids, is_correct,
                 marks_awarded, time_taken_seconds)

- Certificate (id, employee_id, course_id,
               exam_attempt_id, certificate_number,
               issued_date, expiry_date, pdf_url, qr_code)
```

### Task 13.2: Question Bank Service (5h)

- CRUD operations
- Bulk import (CSV)
- Search/filter
- Topic-based organization
- Difficulty distribution

### Task 13.3: Exam Engine (8h)

- Exam configuration
- Question selection (random/fixed)
- Question shuffling
- Option shuffling
- Time tracking
- Auto-save every 30 seconds
- Auto-submit on time end

### Task 13.4: Anti-Cheating (6h)

Implement:
- Full-screen mode enforcement
- Tab switch detection (3 warnings)
- Copy-paste blocking
- Right-click disable
- Multiple device login detection
- IP address logging
- Browser fingerprinting
- Time per question tracking

### Task 13.5: Auto-Evaluation (4h)

- Score calculation
- Negative marking
- Section-wise scoring
- Percentage calculation
- Pass/fail determination

### Task 13.6: Certificate Generation (5h)

- PDF with company branding
- QR code for verification
- Unique certificate number
- Tamper-proof
- Expiry tracking
- LinkedIn share

### Task 13.7: APIs (5h)

| Method | Endpoint |
|--------|----------|
| GET | `/lms/exams/upcoming` |
| GET | `/lms/exams/{id}/start` |
| POST | `/lms/exams/{id}/answer` |
| POST | `/lms/exams/{id}/submit` |
| GET | `/lms/exams/{id}/result` |
| GET | `/lms/my-attempts` |
| GET | `/lms/certificates/me` |
| GET | `/lms/certificates/verify/{number}` |
| POST | `/lms/questions/import` |

### Task 13.8: Flutter - Exam UI (12h)

```
features/exam/
└── presentation/
    └── pages/
        ├── exam_list_page.dart
        ├── exam_instructions_page.dart
        ├── exam_taking_page.dart
        ├── exam_review_page.dart
        ├── exam_result_page.dart
        └── certificate_page.dart
```

### Task 13.9: Exam Taking Experience (8h)

- Timer always visible
- Question navigation
- Progress bar
- Mark for review
- Submit confirmation
- Auto-save
- Force full-screen on Android
- Detect minimize/lock

### Task 13.10: Result Analysis (4h)

- Score breakdown
- Section-wise performance
- Wrong answers with explanations
- Time analysis
- Comparison with average

### Task 13.11: Tests (4h)

---

## Claude Code Prompt

```
Read HRMS_Architecture.md Section 15 → Examination System.

Implement Phase 13 (Examination) as described.

Build:
- Question bank with multiple types
- Exam engine with random selection
- Anti-cheating mechanisms (full-screen, tab detection)
- Auto-evaluation
- Certificate generation with QR
- Department-wise exams
- Bulk question import

Mobile UX:
- Distraction-free exam mode
- Timer prominent
- Question navigation
- Auto-save protection
- Result analysis with explanations

Test all anti-cheating measures.
```

---

# Phase 14: Trainer Department Module

**Duration:** 7-10 days
**Hours:** 70
**Priority:** MEDIUM
**Depends on:** Phase 13

---

## Reference

See HRMS_Architecture.md → Section 16: Trainer Department Module

## Tasks Summary

### Task 14.1: Database Models (3h)
- Trainer profiles, specializations
- Training sessions, participants
- Trainer reviews, calendar
- External trainer contracts

### Task 14.2: Course Builder (drag-drop) (6h)
### Task 14.3: Live Session Management (5h)
- Schedule with calendar
- Zoom/Meet integration
- QR code attendance
- Recording management

### Task 14.4: Trainer Dashboard (4h)
### Task 14.5: Internal Trainer Marketplace (4h)
- Browse trainers by skill
- Booking system
- Reviews & ratings

### Task 14.6: APIs (5h)
### Task 14.7: Flutter - Trainer Module (15h)
### Task 14.8: Tests (4h)

## Claude Code Prompt

```
Read HRMS_Architecture.md Section 16 (Trainer Department Module).

Implement Phase 14 (Trainer Module).

Build:
- Trainer profile management
- Course builder with drag-drop
- Live session scheduling
- Zoom/Meet integration
- QR-based attendance
- Recording management
- Trainer marketplace
- Analytics dashboard

Test full workflow: trainer creates course → schedules session → participants join → recording uploaded.
```

---

# Phase 15: Performance Management

**Duration:** 5-7 days
**Hours:** 50
**Priority:** LOW
**Depends on:** Phase 14

---

## Tasks Summary

### Task 15.1: Models (3h)
- Review cycles, reviews
- Goals (OKRs)
- 360-degree feedback
- 1-on-1 notes

### Task 15.2: Goal Setting Service (4h)
### Task 15.3: Review Cycle Engine (6h)
- Quarterly/annual cycles
- Self + manager + skip-level
- Calibration meetings

### Task 15.4: 360-Degree Feedback (5h)
- Peer + reportee + manager
- Anonymous option
- Aggregated reports

### Task 15.5: 1-on-1 Notes (3h)
### Task 15.6: APIs (4h)
### Task 15.7: Flutter - Performance UI (15h)
### Task 15.8: Tests (4h)

## Claude Code Prompt

```
Read HRMS_Architecture.md Section 8.5 (Performance Management).

Implement Phase 15 (Performance Management).

Build:
- OKR/goal setting
- Quarterly review cycles
- Self + manager + skip-level reviews
- 360-degree feedback (anonymous option)
- 1-on-1 meeting notes
- Rating calibration
- Increment recommendations

Mobile-first design.
```

---

# Phase 16: Reports & Analytics

**Duration:** 5-7 days
**Hours:** 50
**Priority:** LOW
**Depends on:** Phase 15

---

## Tasks Summary

### Task 16.1: Reporting Engine (6h)
- Custom report builder
- Saved reports
- Scheduled reports

### Task 16.2: Standard Reports (8h)
- Headcount trend
- Attrition rate
- Department-wise productivity
- Compliance status
- Cost per employee

### Task 16.3: Director Dashboard (6h)
### Task 16.4: HR Analytics (5h)
### Task 16.5: Manager Reports (4h)
### Task 16.6: Export Functionality (4h)
- PDF, Excel, CSV
- Email scheduling

### Task 16.7: APIs (4h)
### Task 16.8: Flutter - Dashboards (10h)
- Charts using fl_chart
- Interactive filters
- Drill-down

### Task 16.9: Tests (3h)

## Claude Code Prompt

```
Implement Phase 16 (Reports & Analytics).

Build:
- Custom report builder
- 15+ standard reports
- Role-specific dashboards
- Charts and visualizations
- PDF/Excel export
- Email scheduling
- Drill-down capability

Use fl_chart in Flutter for visualizations.
```

---

# Phase 17: Polish & Additional Features

**Duration:** 5-7 days
**Hours:** 45
**Priority:** LOW
**Depends on:** Phase 16

---

## Tasks Summary

### Task 17.1: Asset Management (8h)
- Asset register
- Assignment workflow
- Maintenance tracking

### Task 17.2: Visitor Management (5h)
- Pre-register visitors
- QR code generation
- Auto-notify host

### Task 17.3: Meeting Room Booking (5h)
### Task 17.4: Travel Desk (6h)
### Task 17.5: Holiday Calendar (3h)
### Task 17.6: Birthday/Anniversary (3h)
### Task 17.7: Internal Job Postings (5h)
### Task 17.8: Referral Program (5h)
### Task 17.9: Resignation Module (5h)

## Claude Code Prompt

```
Implement Phase 17 (Polish & Additional Features).

Add these supporting modules:
- Asset management
- Visitor management
- Meeting room booking
- Travel desk
- Holiday calendar (regional)
- Birthday/anniversary automation
- Internal job postings (IJP)
- Referral program
- Resignation & exit module

Each is small but adds significant value.
```

---

# Phase 18: Testing & Deployment

**Duration:** 7-10 days
**Hours:** 65
**Priority:** CRITICAL (Final phase)
**Depends on:** Phase 17

---

## Tasks Summary

### Task 18.1: End-to-End Testing (15h)
- Critical user journeys
- Cross-role testing
- Edge cases

### Task 18.2: Performance Testing (5h)
- Load testing
- Database query optimization
- Caching review

### Task 18.3: Security Audit (8h)
- Penetration testing checklist
- OWASP top 10
- Data encryption review
- Permission boundaries

### Task 18.4: Mobile Testing (6h)
- Multiple devices
- Different OS versions
- Network conditions
- Battery usage

### Task 18.5: CI/CD Setup (8h)
- GitHub Actions for backend
- Codemagic for Flutter
- Auto-deploy to staging
- Manual approval for production

### Task 18.6: Production Setup (10h)
- AWS/GCP setup
- Database hosting
- CDN configuration
- SSL certificates
- Domain setup
- Backup automation

### Task 18.7: Documentation (8h)
- API documentation (OpenAPI)
- User manuals
- Admin guides
- Developer onboarding

### Task 18.8: Training Materials (5h)
- HR training videos
- Manager guides
- Employee onboarding guides

## Claude Code Prompt

```
Implement Phase 18 (Final Testing & Deployment).

Tasks:
1. Comprehensive E2E testing of all phases
2. Performance optimization
3. Security audit (OWASP top 10)
4. Mobile testing on real devices
5. Setup CI/CD pipelines
6. Production infrastructure (AWS/GCP)
7. SSL, CDN, backups
8. Complete documentation
9. Training materials

Ensure system is production-ready and secure.

Final checklist:
- All tests passing
- No critical security issues
- Performance acceptable
- Mobile works on Android 8+ and iOS 13+
- Backups automated
- Monitoring active
- Documentation complete
```

---

## 🎉 PROJECT COMPLETE

After Phase 18, you'll have a production-ready HRMS with:
- ✅ 16+ feature modules
- ✅ Mobile + Web (admin)
- ✅ Role-based access
- ✅ Indian compliance (PF/ESI/TDS/POSH)
- ✅ Field force management
- ✅ LMS with examinations
- ✅ Justice portal
- ✅ Multi-language
- ✅ Offline support

Total: **~24 weeks (~6 months) | ~1,200 hours**

Ready to launch! 🚀
