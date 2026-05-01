# Phase 8: Justice Portal

**Duration:** 7-10 days
**Hours:** 75
**Priority:** HIGH (Legally mandatory for POSH)
**Depends on:** Phase 7

---

## Objective

Build secure complaint/grievance system with direct routing to Director/ICC, bypassing manager/HR. Includes mandatory POSH Act compliance.

## Reference

See HRMS_Architecture.md → Section 13: Justice Portal Module

## Deliverables

- ✅ 8 complaint categories
- ✅ 3 privacy levels (Anonymous/Confidential/Open)
- ✅ POSH Act compliance (mandatory)
- ✅ ICC member management
- ✅ Encrypted complaint storage
- ✅ Anti-retaliation system
- ✅ Director-direct routing
- ✅ Audit log for every access
- ✅ Annual POSH report generation
- ✅ Secure mobile access with biometric

---

## Critical Security Requirements

⚠️ **This module deals with sensitive data. Extra security measures required:**

1. **Separate Database** (recommended)
2. **End-to-end encryption** for all content
3. **No screenshots allowed** in app
4. **Biometric required** to open
5. **Audit log** every view
6. **Watermark** on exports
7. **No notification preview** on lock screen

---

## Tasks

### Task 8.1: Database Schema (Separate DB) (5h)

```python
- JusticeComplaint (id (UUID), ticket_number,
                    complaint_type, privacy_level,
                    complainant_id_encrypted,
                    subject, description_encrypted,
                    incident_date, incident_location,
                    severity, status, submitted_at,
                    assigned_to, resolved_at)

- JusticeEvidence (id, complaint_id, file_url_encrypted,
                   file_type, file_hash, uploaded_at)

- JusticeAccused (id, complaint_id, accused_name_encrypted,
                  accused_employee_id, relationship)

- JusticeWitness (id, complaint_id, witness_name,
                  witness_statement_encrypted, is_anonymous)

- JusticeAction (id, complaint_id, action_type,
                 action_date, taken_by, notes)

- JusticeTimeline (id, complaint_id, event_type,
                   event_description, event_date, done_by)

- JusticeAccessLog (id, complaint_id, user_id, action,
                    timestamp, ip_address, user_agent)

- IccMember (id, member_name, role, is_external,
             term_start, term_end)

- PoshAnnualReport (id, year, total_complaints,
                    resolved, pending, actions_taken)

- RetaliationFlag (id, complaint_id, employee_id,
                   flag_type, detected_at, resolved)
```

### Task 8.2: Encryption Service (5h)

`app/services/encryption_service.py`:
- AES-256 encryption for content
- RSA for keys
- Field-level encryption
- Decrypt only with proper permissions
- Key rotation support

### Task 8.3: Complaint Service (6h)

- `submit_complaint(employee, type, data, privacy_level, evidence)`
- `route_complaint(complaint)` - based on type
- `get_complaint(id, requester)` - with access check
- `assign_to_investigator(complaint_id, user_id)`
- `update_status(complaint_id, status, comments)`
- `resolve_complaint(complaint_id, resolution)`
- `withdraw_complaint(complaint_id, reason)`

### Task 8.4: Routing Engine (4h)

```python
ROUTING_RULES = {
    'sexual_harassment': 'icc_only',
    'fraud': ['director', 'cfo'],
    'manager_issue': ['skip_level_manager', 'hr_head'],
    'hr_issue': 'director_only',
    'director_issue': 'external_ombudsman',
    'safety': ['admin_head', 'hr', 'director'],
    'general': 'hr_head'
}
```

### Task 8.5: POSH Module (8h)

POSH-specific features:
- ICC member setup (4+ members, 50% women, external)
- POSH-only complaint routing
- Timeline tracker (90 days max)
- Standard investigation forms
- Annual report generation (govt format)
- Confidentiality penalty enforcement
- POSH training tracker

### Task 8.6: Anti-Retaliation Detection (5h)

Auto-flag suspicious actions:
- Performance review drop after complaint
- Sudden transfer
- Termination initiated
- Salary freeze
- Leave rejections increase
- Negative feedback spike

Alert Director + ICC automatically.

### Task 8.7: Access Control (4h)

```python
ACCESS_RULES = {
    'director': 'all_complaints',
    'icc_member': 'posh_only',
    'hr_head': 'general_grievance_only',
    'investigator': 'assigned_only',
    'it_admin': 'logs_only_no_content',
    'dba': 'no_decrypted_data'
}
```

Every access logged.

### Task 8.8: Evidence Management (4h)

- Encrypted file upload
- Separate S3 bucket with restricted access
- Hash for tamper detection
- Watermarking on download
- Retention policy

### Task 8.9: APIs (5h)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/justice/submit` | Submit complaint |
| GET | `/justice/me` | My complaints |
| GET | `/justice/me/{id}` | My complaint detail |
| POST | `/justice/me/{id}/evidence` | Add evidence |
| POST | `/justice/me/{id}/withdraw` | Withdraw |
| GET | `/justice/inbox` | Authority inbox |
| GET | `/justice/{id}` | Full complaint (auth) |
| POST | `/justice/{id}/assign` | Assign investigator |
| POST | `/justice/{id}/comment` | Internal note |
| POST | `/justice/{id}/action` | Record action |
| POST | `/justice/{id}/resolve` | Mark resolved |
| GET | `/justice/posh/cases` | POSH cases (ICC) |
| GET | `/justice/posh/annual-report` | Govt format report |
| GET | `/justice/resources` | Helplines |

### Task 8.10: Flutter - Justice Portal (10h)

⚠️ Special UI considerations:

```
features/justice/
└── presentation/
    ├── pages/
    │   ├── justice_home_page.dart
    │   ├── submit_complaint_page.dart
    │   ├── complaint_detail_page.dart
    │   ├── my_complaints_page.dart
    │   └── resources_page.dart
```

**Submit Complaint Wizard (Multi-step):**
1. Select category
2. Choose privacy level
3. Subject + description
4. When/where details
5. Who involved (optional)
6. Witnesses (optional)
7. Evidence upload
8. Desired outcome
9. Confirm & submit

### Task 8.11: Security Features in App (4h)

- FLAG_SECURE on Android (no screenshots)
- iOS equivalent
- Biometric required to enter section
- Auto-logout after 5 min idle
- No notification content on lock screen
- App icon disguise option (advanced)

### Task 8.12: Director Inbox (5h)

Special UI for authority:
- Critical complaints highlighted
- Unread count
- Filter by category/severity
- Encrypted view (decrypt on access)
- Audit trail visible
- Action recording

### Task 8.13: ICC Dashboard (4h)

POSH-only dashboard:
- Active cases with timeline
- Days remaining alerts
- Investigation steps tracker
- Annual report generation

### Task 8.14: Resources Page (2h)

- POSH Act explained
- Women Helpline: 1091
- Police: 100
- Counseling resources
- Company policies
- External NGO contacts

### Task 8.15: Tests (4h)

- Encryption/decryption
- Permission boundaries
- Anonymous complaint flow
- POSH routing
- Audit logging
- Anti-retaliation triggers

---

## Compliance Checklist

POSH Act compliance:
- [ ] ICC has min 4 members
- [ ] 50% women members
- [ ] 1 external member
- [ ] Senior woman as Presiding Officer
- [ ] 7-day acknowledgment timeline
- [ ] 90-day investigation timeline
- [ ] 60-day action timeline
- [ ] Annual report format ready
- [ ] Confidentiality enforced (₹5,000 penalty)
- [ ] POSH training tracker

---

## Claude Code Prompt

```
Read HRMS_Architecture.md Section 13 (Justice Portal Module).

Implement Phase 8 as described in PHASE_08_Justice.md.

⚠️ CRITICAL SECURITY MODULE - Extra care required:

Backend:
1. Separate database (or schema) for justice data
2. AES-256 encryption for all complaint content
3. Field-level encryption
4. Encrypted file storage
5. Audit log every access
6. POSH Act compliant routing
7. Anti-retaliation detection
8. Annual POSH report generation

Mobile:
1. Biometric required to access section
2. FLAG_SECURE (no screenshots)
3. No notification preview on lock screen
4. Multi-step complaint wizard
5. 3 privacy levels (Anonymous/Confidential/Open)
6. Evidence upload (encrypted)
7. Resources page with helplines

POSH Compliance:
- ICC member setup
- 7-day acknowledgment
- 90-day investigation
- Annual report (govt format)

Test extensively:
- Permission boundaries
- Encryption working
- Audit logs complete
- Anti-retaliation triggers
- Anonymous complaints route correctly

Use the highest security standards. This module is legally mandatory.
```

---

## Next: Phase 9 - Field Force Core
