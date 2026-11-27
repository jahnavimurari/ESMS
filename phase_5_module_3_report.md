# Phase 5, Module 3: Leave Management Implementation Report

**Date & Time:** 2026-11-25T12:54:30+05:30  
**Status:** **COMPLETED AND VERIFIED (56/56 Tests Passing - 100%, 0 Build Errors)**

---

## 1. Overview & Scope

In accordance with Phase 5 guidelines, **Module 3: Leave Management** has been implemented, integrated, and verified without starting or modifying any subsequent modules (Tasks or Performance Reviews).

All existing functionality from Phases 1–4, Phase 5 Module 1 (Employee Management), and Phase 5 Module 2 (Attendance Management) was strictly preserved.

---

## 2. Existing Models Reused & Overlap Protection

The existing Phase 3 models in `backend/app/models/leave.py` (`LeaveType` and `LeaveRequest`) were reused directly without duplicate tables or destructive migrations:
- **`LeaveType`**: Code, name, description, annual entitlement (`days_per_year`), `is_paid` flag, and `is_active` status. Standard default types seeded: Casual Leave (CL, 12d), Sick Leave (SL, 10d), Earned Leave (EL, 15d), Unpaid Leave (UL, 0d/unlimited).
- **`LeaveRequest`**: Linked to `Employee`, `LeaveType`, and reviewer `User`.
- **Database Overlap Prevention**:
  - Leverages the PostgreSQL transactional advisory lock (`pg_advisory_xact_lock`) on the `employee_id` hash during validation.
  - Checks date intervals using:
    $$\text{existing.start\_date} \le \text{new.end\_date} \quad \text{AND} \quad \text{existing.end\_date} \ge \text{new.start\_date}$$
    for requests in `PENDING` or `APPROVED` status.
  - Check constraints enforced: `status IN ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED')`, `end_date >= start_date`, and `total_days > 0`.

---

## 3. Files Created and Modified

### Backend:
- `backend/app/models/leave.py` (Modified): Added `description` to `LeaveType`, `to_dict()` helpers, and `BigInteger().with_variant(Integer, "sqlite")` on `LeaveRequest.id` for cross-dialect compatibility.
- `backend/app/schemas/leave_schema.py` (Created): Marshmallow request validation schemas (`LeaveApplySchema`, `LeaveUpdateSchema`, `LeaveReviewSchema`, `LeaveTypeCreateSchema`, `LeaveTypeUpdateSchema`).
- `backend/app/services/leave_service.py` (Created): Complete domain logic:
  - Application boundary validation and atomic locking.
  - PENDING request updates.
  - Approval and rejection workflows with duplicate approval protection.
  - Employee cancellation workflow.
  - Accurate year-wise balance accounting (entitlement, approved taken, pending requested, remaining paid balance).
  - Summary KPI metrics.
- `backend/app/routes/leaves.py` (Created): REST API endpoints under `/api/leaves`.
- `backend/app/__init__.py` (Modified): Registered `leave_bp` with the application factory.
- `backend/tests/test_leaves.py` (Created): 9 Pytest tests verifying application, validations, overlap rejections, multi-employee isolation, approval/rejection balance impacts, cancellation, and RBAC.

### Frontend:
- `frontend/src/services/leaveService.js` (Created): Axios API client for all leave operations.
- `frontend/src/components/leaves/ApplyLeaveModal.jsx` (Created): Modal UI for submitting leave applications with date picker validation.
- `frontend/src/components/leaves/ReviewLeaveModal.jsx` (Created): Modal UI for HR/Admin approval or rejection with mandatory rejection comments.
- `frontend/src/pages/leaves/LeaveManagementPage.jsx` (Created): Responsive management view with employee balance cards, HR summary KPI cards, filters, and action tables.
- `frontend/src/pages/dashboard/EmployeeDashboard.jsx` & `HRDashboard.jsx` (Modified): Added navigation links to Leave Management.
- `frontend/src/App.jsx` (Modified): Registered `/leaves` protected route in React Router.

---

## 4. Implemented REST APIs

All endpoints are registered under `/api/leaves`:

| Method | Endpoint | Authorization | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/leaves` | Authenticated Employee | Submits a leave application. Validates dates, checks overlap, locks employee transactionally, and calculates total days. |
| `GET` | `/api/leaves/my` | Authenticated Employee | Returns the employee's personal leave history and annual balance breakdown. |
| `GET` | `/api/leaves/balance` | Authenticated Employee | Returns detailed year-wise balance metrics per leave type. |
| `GET` | `/api/leaves` | HR or Admin | Lists company-wide leave applications with search, department, type, and status filters. |
| `GET` | `/api/leaves/summary` | HR or Admin | Returns real-time KPI metrics (pending approvals, approved this year, rejected this year, employees on leave today). |
| `GET` | `/api/leaves/<id>` | Authenticated | Retrieves detailed leave request info (employees restricted to their own requests). |
| `PUT` | `/api/leaves/<id>` | Authenticated Employee | Updates an employee's own PENDING request with overlap re-verification. |
| `PATCH` | `/api/leaves/<id>/approve` | HR or Admin | Approves a PENDING request, logs reviewer and timestamp, and deducts approved balance. |
| `PATCH` | `/api/leaves/<id>/reject` | HR or Admin | Rejects a PENDING request with reviewer comments, leaving balances intact. |
| `PATCH` | `/api/leaves/<id>/cancel` | Authenticated Employee | Cancels a PENDING or APPROVED request. |
| `GET` | `/api/leaves/types` | Authenticated | Lists all active leave types. |
| `POST` | `/api/leaves/types` | Admin | Creates a new organizational leave type. |
| `PUT` | `/api/leaves/types/<id>` | Admin | Updates leave type metadata or active status. |

---

## 5. Leave Application & Approval Workflow Rules

1. **Balance Accounting**:
   - `PENDING` requests display separately and do **NOT** prematurely reduce approved remaining balance.
   - Upon `APPROVED`, days are permanently counted against that year's entitlement for paid leave types.
   - `REJECTED` or `CANCELLED` requests do not deduct from approved balance.
2. **Duplicate Operation Guard**:
   - Approving an already approved request returns `400 Bad Request` (*"This leave request is already approved"*).
   - Rejecting a non-pending request returns `400 Bad Request`.
3. **Double Deduction Prevention**:
   - Balance is computed dynamically using SQL aggregations (`SUM(total_days) WHERE status = 'APPROVED'`), preventing race condition double deductions.

---

## 6. Test Results

### Pytest Regression Execution:
Command: `cmd /c "cd /d c:\JANNU\projects\ESMS\backend && venv\Scripts\pytest -v"`

```
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-8.2.1, pluggy-1.7.0 -- c:\JANNU\projects\ESMS\backend\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: c:\JANNU\projects\ESMS\backend
configfile: pytest.ini
testpaths: tests
plugins: flask-1.3.0
collecting ... collected 56 items

tests/test_attendance.py::test_check_in_success PASSED                   [  1%]
tests/test_attendance.py::test_repeated_check_in_rejection PASSED        [  3%]
tests/test_attendance.py::test_check_out_success PASSED                  [  5%]
tests/test_attendance.py::test_check_out_without_active_session_rejected PASSED [  7%]
tests/test_attendance.py::test_multiple_shifts_in_one_day PASSED         [  8%]
tests/test_attendance.py::test_employee_my_attendance_and_rbac PASSED    [ 10%]
tests/test_attendance.py::test_hr_and_admin_attendance_listing_and_summary PASSED [ 12%]
tests/test_attendance.py::test_attendance_correction_by_admin PASSED     [ 14%]
tests/test_attendance.py::test_unauthenticated_attendance_requests_rejected PASSED [ 16%]
tests/test_attendance_advanced.py::test_concurrent_checkin_protection PASSED [ 17%]
tests/test_attendance_advanced.py::test_multiple_shift_cumulative_hours_and_status PASSED [ 19%]
tests/test_attendance_advanced.py::test_timezone_integrity_and_comparisons PASSED [ 21%]
tests/test_attendance_advanced.py::test_cross_employee_access_authorization PASSED [ 23%]
tests/test_attendance_advanced.py::test_validation_checkout_before_checkin_rejected PASSED [ 25%]
tests/test_auth.py::test_auth_health_endpoint PASSED                     [ 26%]
tests/test_auth.py::test_login_success PASSED                            [ 28%]
tests/test_auth.py::test_login_incorrect_password PASSED                 [ 30%]
tests/test_auth.py::test_login_unknown_email PASSED                      [ 32%]
tests/test_auth.py::test_login_inactive_account PASSED                   [ 33%]
tests/test_auth.py::test_login_validation_errors PASSED                  [ 35%]
tests/test_auth.py::test_get_current_user_me PASSED                      [ 37%]
tests/test_auth.py::test_refresh_token_strategy PASSED                   [ 39%]
tests/test_auth.py::test_logout_and_token_revocation PASSED              [ 41%]
tests/test_auth.py::test_change_password PASSED                          [ 42%]
tests/test_auth.py::test_role_based_access_control PASSED                [ 44%]
tests/test_auth.py::test_cli_admin_creation PASSED                       [ 46%]
tests/test_employees.py::test_department_creation_and_listing PASSED     [ 48%]
tests/test_employees.py::test_employee_creation_success PASSED           [ 50%]
tests/test_employees.py::test_employee_creation_missing_required_fields PASSED [ 51%]
tests/test_employees.py::test_employee_creation_duplicate_email PASSED   [ 53%]
tests/test_employees.py::test_employee_creation_invalid_department PASSED [ 55%]
tests/test_employees.py::test_employee_list_and_details_rbac PASSED      [ 57%]
tests/test_employees.py::test_employee_update_and_status_deactivation PASSED [ 58%]
tests/test_employees.py::test_unauthenticated_requests_rejected PASSED   [ 60%]
tests/test_health.py::test_service_health PASSED                         [ 62%]
tests/test_health.py::test_db_health_unconfigured PASSED                 [ 64%]
tests/test_leaves.py::test_leave_application_success_and_balance PASSED  [ 66%]
tests/test_leaves.py::test_invalid_date_range_rejected PASSED            [ 67%]
tests/test_leaves.py::test_overlapping_leave_rejection_for_same_employee PASSED [ 69%]
tests/test_leaves.py::test_different_employees_can_apply_for_same_dates PASSED [ 71%]
tests/test_leaves.py::test_approval_workflow_and_balance_deduction PASSED [ 73%]
tests/test_leaves.py::test_rejection_workflow_does_not_deduct_balance PASSED [ 75%]
tests/test_leaves.py::test_cancellation_workflow PASSED                  [ 76%]
tests/test_leaves.py::test_cross_employee_access_authorization PASSED    [ 78%]
tests/test_leaves.py::test_unauthenticated_requests_rejected PASSED      [ 80%]
tests/test_models.py::test_models_registered_in_metadata PASSED          [ 82%]
tests/test_models.py::test_user_model_attributes PASSED                  [ 83%]
tests/test_models.py::test_employee_model_and_properties PASSED          [ 85%]
tests/test_models.py::test_attendance_model_constraints_and_multi_shift PASSED [ 87%]
tests/test_models.py::test_leave_request_date_constraints PASSED         [ 89%]
tests/test_models.py::test_leave_concurrency_overlap_logic PASSED        [ 91%]
tests/test_models.py::test_leave_validate_and_submit_validation_errors PASSED [ 92%]
tests/test_task_model_constraints PASSED                                 [ 94%]
tests/test_performance_review_rating_constraint PASSED                   [ 96%]
tests/test_revoked_token_attributes PASSED                               [ 98%]
tests/test_audit_log_attributes PASSED                                   [100%]

======================== 56 passed in 87.70s (0:01:27) ========================
```

- **Total Tests:** 56
- **Passed:** 56 (100%)
- **Failed:** 0
- **Pass Rate:** 100%

---

## 7. Frontend Production Build Results

Command: `cmd /c "cd /d c:\JANNU\projects\ESMS\frontend && npm run build"`

```
> esms-frontend@1.0.0 build
> vite build

vite v5.4.21 building for production...
transforming...
✓ 1579 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.75 kB │ gzip:  0.42 kB
dist/assets/index-BIP418B-.css    1.08 kB │ gzip:  0.59 kB
dist/assets/index-Cxk0i0pY.js   329.72 kB │ gzip: 91.14 kB
✓ built in 5.66s
```
- **Build Errors:** 0
- **Build Warnings:** 0

---

## 8. Known Limitations & Next Steps

- **Downstream Modules Pending**: Tasks and Performance Management remain untouched and are ready to be implemented in subsequent modules.
- **Holiday Calendar Exclusions**: Standard leave calculation currently counts consecutive calendar days inclusive. Company holiday calendar exclusion can be integrated into `LeaveService.calculate_requested_days` when holiday tables are introduced.

