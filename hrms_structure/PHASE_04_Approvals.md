# Phase 4: Universal Approval Engine

**Duration:** 5 days
**Hours:** 50
**Priority:** HIGH
**Depends on:** Phase 3

---

## Objective

Build a single approval engine that handles ALL approval workflows (leave, reimbursement, document, regularization, etc.) with multi-level approval rules.

## Why?

Currently each module has its own approval. This creates duplication. One unified system means:
- Single inbox for managers
- Consistent UX
- Easy to add new approval types
- Audit trail in one place

---

## Tasks

### Task 4.1: Database Models (3h)

```python
- ApprovalWorkflow (id, type, name, levels_config,
                    conditions_json, is_active)

- Approval (id, request_type, request_id, request_data,
            current_level, max_levels, status,
            initiated_by, initiated_at,
            final_status, final_decision_at)

- ApprovalAction (id, approval_id, level, approver_id,
                  action, comments, action_at)
```

### Task 4.2: Approval Engine Service (8h)

`app/services/approval_engine.py`:
- `submit_for_approval(type, data, employee)` → routes to workflow
- `get_pending_for_user(user)` → all types in one inbox
- `approve(approval_id, user, comments)`
- `reject(approval_id, user, reason)`
- `escalate(approval_id)` - if no action in X days
- `delegate(approval_id, to_user)`

### Task 4.3: Workflow Configuration (4h)

JSON-based config:
```json
{
  "type": "leave_request",
  "levels": [
    {
      "level": 1,
      "approver": "direct_manager",
      "auto_approve_if": "days <= 1"
    },
    {
      "level": 2,
      "approver": "skip_level",
      "condition": "days > 5"
    }
  ]
}
```

### Task 4.4: APIs (4h)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/approvals/inbox` | All pending |
| GET | `/approvals/{id}` | Detail |
| POST | `/approvals/{id}/approve` | Approve |
| POST | `/approvals/{id}/reject` | Reject |
| GET | `/approvals/history` | My past |
| POST | `/approvals/{id}/delegate` | Delegate |

### Task 4.5: Integrate Existing (4h)

Refactor leave + attendance regularization to use approval engine.

### Task 4.6: Flutter - Universal Inbox (8h)

Single screen for all approvals:
- Filter by type (Leave/Reimbursement/etc)
- Sort by date/priority
- Tinder-style swipe (right=approve, left=reject)
- Bulk actions
- Comment before approving
- Notification on new approval

### Task 4.7: Tests & Polish (4h)

---

## Claude Code Prompt

```
Implement Phase 4 (Universal Approval Engine).

Build a generic approval system that all modules can use.
Refactor existing leave approval to use this engine.

Create universal approval inbox in Flutter with swipe gestures.
```

---

## Next: Phase 5 - Mobile App MVP Polish
