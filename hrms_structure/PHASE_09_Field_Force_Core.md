# Phase 9: Field Force Core

**Duration:** 10-14 days
**Hours:** 90
**Priority:** HIGH
**Depends on:** Phase 8

---

## Objective

Build core field force module - GPS tracking, geo-fenced check-in, daily activity (DA) plans, visit management, and live manager dashboard.

## Reference

See HRMS_Architecture.md → Section 14: Field Force Management Module

## Deliverables

- ✅ Daily Activity (DA) - visit/beat planning
- ✅ Live GPS tracking during work hours
- ✅ Geo-fenced check-in with selfie
- ✅ Visit workflow (check-in → form → check-out)
- ✅ Customer/Lead database
- ✅ Travel/distance tracking
- ✅ Manager live map dashboard
- ✅ Mock GPS detection
- ✅ Offline mode
- ✅ Battery optimization

---

## Tasks

### Task 9.1: Database Models (5h)

```python
- FieldEmployee (id, employee_id, type, territory,
                 vehicle_type, current_status,
                 vehicle_number, license_number)

- FieldJob (id, employee_id, job_type, customer_id,
            scheduled_date, scheduled_time, priority,
            status, assigned_by, assigned_at)

- Customer (id, name, type, address, geo_lat, geo_lng,
            contact_persons, industry, gst, pan, created_by)

- Visit (id, job_id, employee_id, check_in_time,
         check_in_lat, check_in_lng, check_in_selfie_url,
         check_out_time, check_out_lat, check_out_lng,
         visit_notes, outcome, signature_url)

- VisitPhoto (id, visit_id, photo_url, photo_type,
              geo_tagged, timestamp, watermarked, exif_data)

- LocationTrack (id, employee_id, lat, lng, accuracy,
                 timestamp, battery_level, is_mock,
                 speed, heading)

- VisitPlan (id, employee_id, plan_date, optimized_route,
             total_distance, estimated_time, actual_time)

- FieldExpense (id, employee_id, visit_id, category,
                amount, receipt_url, status, approved_by)
```

### Task 9.2: Geo-Fencing & Distance (4h)

- Haversine formula for distance
- Mock GPS detection (multiple methods)
- Geo-fence radius validation
- Battery-efficient tracking

### Task 9.3: Field Job Service (6h)

- Create job (manager assigns)
- Auto-route optimization
- Bulk assignment
- Re-assignment workflow
- Priority management

### Task 9.4: Visit Service (6h)

- `start_visit(employee, lat, lng, selfie)`
- `submit_visit_form(visit_id, data)`
- `upload_visit_photos(visit_id, photos)`
- `capture_signature(visit_id, signature)`
- `end_visit(visit_id, lat, lng)`
- Validation: lat/lng matches customer location

### Task 9.5: GPS Tracking Service (5h)

- Periodic location update (5-15 min intervals)
- Battery-aware tracking
- Compress location data
- Privacy: only during work hours
- Mock GPS detection

### Task 9.6: APIs (6h)

| Method | Endpoint |
|--------|----------|
| GET | `/field/jobs/today` |
| GET | `/field/jobs/{id}` |
| POST | `/field/jobs/{id}/checkin` |
| POST | `/field/jobs/{id}/checkout` |
| POST | `/field/jobs/{id}/visit-form` |
| POST | `/field/jobs/{id}/photos` |
| POST | `/field/jobs/{id}/signature` |
| POST | `/field/location/track` |
| GET | `/field/route/optimize` |
| GET | `/field/team/live-map` |
| GET | `/field/team/performance` |
| POST | `/field/jobs/assign` |

### Task 9.7: Manager Live Dashboard (5h)

- Live map with all field staff
- Color-coded status
- Click for details
- Route history playback
- Alerts (idle, mismatch, mock GPS)

### Task 9.8: Flutter - Field Force Home (8h)

```
features/field_force/
└── presentation/
    ├── pages/
    │   ├── field_home_page.dart
    │   ├── visit_detail_page.dart
    │   ├── visit_form_page.dart
    │   ├── route_map_page.dart
    │   ├── expense_page.dart
    │   └── manager_live_map_page.dart
```

**Home Screen:**
- Today's visit count
- Plan vs completed
- Quick check-in button
- Distance traveled
- Hours worked
- Map view

### Task 9.9: Visit Flow UI (8h)

Step-by-step:
1. Tap "Start Visit"
2. Auto-detect location (geo-fence)
3. Capture selfie
4. Open visit form
5. Fill details
6. Upload photos
7. Customer signature
8. Submit & check-out

### Task 9.10: Map Integration (6h)

Use `flutter_map` or Google Maps:
- Show all visits on map
- Optimal route
- Navigation deep link
- Distance markers
- Offline maps

### Task 9.11: Offline Mode (8h)

Critical for field staff:
- Queue all actions when offline
- Auto-sync when online
- Photos compressed
- Form data persisted
- Conflict resolution

### Task 9.12: Battery Optimization (4h)

- Adaptive tracking interval
- Reduce when stationary
- Background mode tuning
- Battery saver detection

### Task 9.13: Mock GPS Prevention (3h)

- Multiple detection methods
- Block submission if detected
- Alert manager
- Audit log

### Task 9.14: Tests (4h)

---

## Claude Code Prompt

```
Read HRMS_Architecture.md Section 14 (Field Force Management Module).

Implement Phase 9 (Field Force Core) as described in PHASE_09_Field_Force_Core.md.

Build the foundation for field force management:

Backend:
1. Field employee, job, visit, customer models
2. GPS tracking with periodic updates
3. Geo-fencing validation
4. Mock GPS detection
5. Visit workflow
6. Live tracking APIs

Mobile (CRITICAL for field staff):
1. Quick check-in with GPS + selfie
2. Today's visit list
3. Visit form (configurable)
4. Photo capture (camera-only, no gallery)
5. Customer signature
6. Map with optimal route
7. Offline mode (queue actions)
8. Battery optimization

Manager Dashboard:
1. Live map with all field staff
2. Status indicators
3. Route history
4. Performance metrics
5. Alerts for anomalies

Test thoroughly:
- Geo-fence accuracy
- Mock GPS blocked
- Offline sync working
- Photos uploaded with EXIF
- Battery usage acceptable
```

---

## Next: Phase 10 - Sales Field Force
