# Phase 10: Sales Field Force

**Duration:** 7-10 days
**Hours:** 70
**Priority:** MEDIUM
**Depends on:** Phase 9

---

## Objective

Add sales-specific features to field force - lead management, customer database, visit reports, quotes, orders, promotions tracking, targets, and commissions.

## Reference

See HRMS_Architecture.md → Section 14 → Sales Field Force section

## Deliverables

- ✅ Lead management with sources & stages
- ✅ Customer database (CRM-lite)
- ✅ Detailed visit reports
- ✅ Product catalog (offline access)
- ✅ Quote generation (PDF)
- ✅ Order booking
- ✅ Promotional activity tracking
- ✅ Sales pipeline (Kanban)
- ✅ Targets & achievement
- ✅ Commission calculator
- ✅ Competition tracker

---

## Tasks

### Task 10.1: Database Models (4h)

```python
- Lead (id, customer_id, source, status,
        expected_value, expected_close_date,
        assigned_to, score, created_at)

- Opportunity (id, lead_id, stage, probability,
               amount, products, competitor,
               next_action, next_action_date)

- Quote (id, customer_id, employee_id, products,
         total_amount, discount, valid_until,
         status, pdf_url)

- Order (id, customer_id, employee_id, products,
         total_amount, payment_terms, status,
         tracking_number)

- SalesTarget (id, employee_id, period_type,
               target_amount, achievement,
               period_start, period_end)

- PromotionActivity (id, employee_id, location,
                     event_name, banners_placed,
                     brochures_distributed,
                     demos_given, leads_collected,
                     photos, voice_notes, date)

- Commission (id, employee_id, deal_id,
              amount, percentage, status, paid_at)

- Competitor (id, name, products, pricing,
              strengths, weaknesses)
```

### Task 10.2: Lead Service (5h)

- CRUD operations
- Stage transitions
- Auto-scoring algorithm
- Assignment logic
- Pipeline view data

### Task 10.3: Quote Generation (5h)

- Build quote in app
- Discount approval workflow
- PDF generation with company branding
- Email/WhatsApp share
- Digital signature

### Task 10.4: Product Catalog (4h)

- Offline-first design
- Brochure PDFs
- Demo videos
- Pricing sheets
- Comparison charts
- Periodic sync

### Task 10.5: Targets & Commissions (5h)

- Monthly/quarterly targets
- Real-time achievement tracking
- Slab-based commission
- Forecasting

### Task 10.6: Promotions Tracking (4h)

- Event/exhibition activity
- Photos with proof
- Materials distributed count
- Lead capture
- ROI tracking

### Task 10.7: APIs (5h)

| Method | Endpoint |
|--------|----------|
| GET | `/field/leads` |
| POST | `/field/leads` |
| PUT | `/field/leads/{id}/stage` |
| GET | `/field/customers` |
| POST | `/field/quotes` |
| GET | `/field/quotes/{id}/pdf` |
| POST | `/field/orders` |
| GET | `/field/products` |
| GET | `/field/targets/me` |
| GET | `/field/commission/me` |
| POST | `/field/promotions` |

### Task 10.8: Flutter - Sales Module (15h)

```
features/sales/
└── presentation/
    └── pages/
        ├── leads_page.dart
        ├── lead_detail_page.dart
        ├── pipeline_page.dart (Kanban)
        ├── customer_list_page.dart
        ├── quote_builder_page.dart
        ├── product_catalog_page.dart
        ├── targets_page.dart
        ├── promotions_page.dart
        └── commission_page.dart
```

### Task 10.9: Pipeline Kanban View (4h)

- Drag-drop between stages
- Stage-wise totals
- Probability indicators
- Filter & search

### Task 10.10: Tests (4h)

---

## Claude Code Prompt

```
Read HRMS_Architecture.md Section 14 → Sales Field Force.

Implement Phase 10 (Sales Field Force) as described.

Build CRM-lite functionality:
- Lead management with stages
- Customer database
- Quote generation with PDF
- Order booking
- Product catalog (offline-first)
- Pipeline Kanban view
- Targets & commission tracking
- Promotion activity logging

Make sure offline mode works for field staff in poor connectivity areas.
```

---

# Phase 11: Verification Field Force

**Duration:** 7-10 days
**Hours:** 70
**Priority:** MEDIUM
**Depends on:** Phase 10

---

## Objective

Add verification-specific features - configurable verification templates, OCR, digital signatures, TAT tracking, fraud detection, and report generation.

## Reference

See HRMS_Architecture.md → Section 14 → Verification Field Force

## Deliverables

- ✅ Verification job queue
- ✅ Configurable templates (no-code)
- ✅ Address/Employment/Document/Business verification
- ✅ OCR for Aadhaar, PAN
- ✅ Photo capture with watermark
- ✅ Digital signature
- ✅ Verification report PDF
- ✅ Quality audit system
- ✅ Fraud detection
- ✅ TAT tracking & SLA management

---

## Tasks

### Task 11.1: Database Models (3h)

```python
- VerificationTemplate (id, name, type, fields_json,
                        photo_requirements, signature_required)

- Verification (id, job_id, type, customer_data,
                verification_form_data, result,
                remarks, report_pdf_url,
                verifier_id, verified_at,
                audited_by, audit_status)

- VerificationFraudFlag (id, verification_id,
                         flag_type, detected_at)

- VerificationAudit (id, verification_id, auditor_id,
                     audit_date, status, comments)
```

### Task 11.2: Configurable Template Builder (5h)

JSON-based field configuration:
- Field types: text, dropdown, checkbox, photo, signature
- Validation rules
- Mandatory/optional
- Conditional fields

HR can:
- Create new verification type
- Edit existing templates
- Set photo requirements
- Configure validation

### Task 11.3: OCR Integration (5h)

Use Tesseract or cloud OCR:
- Aadhaar number extraction
- PAN extraction
- Auto-fill verification form
- Confidence score

### Task 11.4: Photo Capture System (4h)

Strict requirements:
- Camera-only (no gallery)
- Auto-watermark (date/time/location)
- EXIF preserved
- Multiple angles
- Blur detection
- Compression

### Task 11.5: Digital Signature (3h)

- Canvas-based signature
- Convert to image
- Store with timestamp
- Tamper-proof

### Task 11.6: Verification Report PDF (4h)

Auto-generate PDF:
- Customer details
- Verification result
- All photos embedded
- Signature
- Verifier details
- Standard format for clients

### Task 11.7: Fraud Detection (5h)

Pattern detection:
- Same address multiple times
- Same person photo
- GPS mismatch
- Time anomalies
- Duplicate documents

Flag for audit.

### Task 11.8: TAT/SLA Tracking (3h)

- Time stamps each stage
- SLA per client/type
- Alert when approaching breach
- Compliance reports

### Task 11.9: Quality Audit (4h)

- Random 10% sampling
- Supervisor review
- Re-verification trigger
- Quality score per agent

### Task 11.10: APIs (4h)

| Method | Endpoint |
|--------|----------|
| GET | `/field/verifications/queue` |
| POST | `/field/verifications/{id}/submit` |
| POST | `/field/verifications/{id}/photos` |
| GET | `/field/templates/{type}` |
| POST | `/field/ocr/aadhaar` |
| POST | `/field/ocr/pan` |
| GET | `/field/audit/random` |
| GET | `/field/reports/tat` |
| GET | `/field/reports/fraud` |

### Task 11.11: Flutter - Verification Module (12h)

```
features/verification/
└── presentation/
    └── pages/
        ├── verification_queue_page.dart
        ├── verification_form_page.dart
        ├── ocr_capture_page.dart
        ├── signature_page.dart
        ├── verification_report_page.dart
        └── audit_page.dart
```

### Task 11.12: Tests (4h)

---

## Claude Code Prompt

```
Read HRMS_Architecture.md Section 14 → Verification Field Force.

Implement Phase 11 (Verification Field Force) as described.

Build:
- Configurable verification templates (no-code builder)
- 4 verification types: Address, Employment, Document, Business
- OCR for Aadhaar/PAN
- Photo capture with strict requirements (camera-only, watermark)
- Digital signature
- Auto-generated PDF reports
- Fraud detection patterns
- TAT/SLA tracking
- Quality audit system

Mobile UX critical:
- Forms work offline
- Photos with EXIF
- Multi-language support
- Battery efficient

Test fraud detection thoroughly.
```

---

# Phase 12: LMS (Learning Management System)

**Duration:** 10-14 days
**Hours:** 85
**Priority:** MEDIUM
**Depends on:** Phase 11

---

## Objective

Build LMS with department-wise courses, learning paths, multiple content types, and progress tracking.

## Reference

See HRMS_Architecture.md → Section 15: LMS & Examination Module

## Deliverables

- ✅ Course library (department-wise)
- ✅ Course creation (modules → lessons)
- ✅ 9 content types (video, PDF, article, etc.)
- ✅ Learning paths
- ✅ Mandatory vs optional courses
- ✅ Progress tracking
- ✅ Auto-assignment rules
- ✅ Offline learning
- ✅ Multi-device sync
- ✅ Gamification (points, badges, streaks)

---

## Tasks

### Task 12.1: Database Models (5h)

```python
- Course (id, title, description, category,
          department_id, difficulty, hours,
          thumbnail_url, status, is_mandatory,
          validity_months, created_by)

- CourseModule (id, course_id, title, order, hours)

- CourseLesson (id, module_id, title, content_type,
                content_url, duration, order)

- LearningPath (id, name, target_role, target_department)

- LearningPathCourse (path_id, course_id, sequence_order)

- CourseEnrollment (id, employee_id, course_id,
                    enrolled_at, due_date, status,
                    progress_percentage, completed_at)

- LessonProgress (id, enrollment_id, lesson_id,
                  status, time_spent, completed_at, notes)

- ComplianceRequirement (id, course_id, frequency_months,
                          applicable_to_role)

- ComplianceStatus (id, employee_id, requirement_id,
                    last_completed_at, next_due_at, status)
```

### Task 12.2: Course Service (6h)

- CRUD operations
- Module/lesson management
- Auto-assignment based on rules
- Progress tracking
- Compliance status

### Task 12.3: Content Upload (5h)

- Video upload (chunked, large files)
- PDF upload
- Compression
- CDN for delivery
- Subtitle support

### Task 12.4: Learning Path Engine (4h)

- Pre-defined paths
- Sequential vs parallel
- Prerequisite checking
- Auto-enrollment

### Task 12.5: Auto-Assignment (4h)

Rules engine:
- New joiner → onboarding path
- Department change → new path
- Promotion → leadership path
- Annual → compliance refresh

### Task 12.6: Gamification (5h)

- Points per lesson/quiz
- Badges system
- Streaks
- Leaderboards (optional)
- Levels (Bronze/Silver/Gold/Platinum)

### Task 12.7: APIs (5h)

| Method | Endpoint |
|--------|----------|
| GET | `/lms/courses` |
| GET | `/lms/courses/recommended` |
| GET | `/lms/courses/mandatory` |
| POST | `/lms/courses/{id}/enroll` |
| GET | `/lms/my-courses` |
| GET | `/lms/lessons/{id}` |
| POST | `/lms/lessons/{id}/complete` |
| GET | `/lms/compliance/me` |
| GET | `/lms/badges/me` |

### Task 12.8: Flutter - LMS UI (15h)

```
features/lms/
└── presentation/
    └── pages/
        ├── lms_home_page.dart
        ├── course_list_page.dart
        ├── course_detail_page.dart
        ├── lesson_player_page.dart
        ├── pdf_viewer_page.dart
        ├── article_reader_page.dart
        ├── progress_page.dart
        └── certificates_page.dart
```

**Lesson Player:**
- Video player with speed control
- PDF viewer
- Article reader with annotations
- Notes panel
- Bookmark
- Mark complete

### Task 12.9: Offline Learning (6h)

- Download videos
- Save PDFs
- Track offline progress
- Sync when online

### Task 12.10: Tests (5h)

---

## Claude Code Prompt

```
Read HRMS_Architecture.md Section 15 (LMS & Examination Module).

Implement Phase 12 (LMS) as described.

Build:
- Course library with departments/categories
- Module → lesson structure
- 9 content types support
- Learning paths
- Auto-assignment rules
- Progress tracking
- Compliance tracking
- Gamification (points/badges/streaks)

Mobile:
- Course discovery
- Video/PDF/Article viewers
- Offline download support
- Progress sync across devices
- Notes & bookmarks

Don't include AI features - keep it practical.
```

---

## Next: Phase 13 - Examination System
