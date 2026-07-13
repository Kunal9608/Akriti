# SOFTWARE DESIGN DOCUMENT (SDD)
# Akriti Diagnostics Center — Pathology Laboratory Management System

**Document Version:** 1.0
**Companion Document:** SRS v3.0 (Engineering Specification) — this SDD implements the requirements defined there
**Status:** Final — Ready for Development

---

## Document Control

| Version | Description |
|---|---|
| 1.0 | Initial design document — architecture, module design, algorithms, sequence flows, deployment design |

---

## 1. Introduction

### 1.1 Purpose

While the SRS defines *what* the system must do, this Software Design Document defines *how* it will be built: the architectural style, the module and class-level breakdown, the algorithms behind non-trivial logic (Patient ID generation, face-recognition matching, audit-log hash chaining, idempotent request handling), the sequence of operations for key workflows, and the physical deployment design. A developer or AI coding agent should be able to start writing code directly from this document's module breakdown without needing to make architectural decisions independently.

### 1.2 Design Goals

1. **Correctness under concurrency** — the system will have multiple staff performing writes simultaneously at a busy counter; every design decision involving shared state (Patient ID sequences, payment updates, idempotency) must be safe by construction, not by convention.
2. **Fail-safe, not fail-blocking** — a staff member must never be stuck unable to register a patient or mark attendance because of a transient error, slow network, or unrecognized face; every such path has a defined fallback.
3. **Auditable by design** — sensitive state changes are logged as an unavoidable side effect of the write path itself (via a shared service, not scattered manual calls), so audit coverage cannot be accidentally skipped by a future feature addition.
4. **Small footprint, no unnecessary frameworks** — vanilla JS frontend, a single FastAPI service, one database. Complexity is added only where the requirement demands it (e.g. Redis for idempotency/rate-limiting, `pgvector` for face search) — not speculatively.

---

## 2. Architectural Design

### 2.1 Architectural Style

The backend follows a **layered architecture** within a single FastAPI service:

```
┌─────────────────────────────────────────────┐
│  Routers (API layer)                        │  ← FastAPI route handlers, request/response DTOs (Pydantic)
├─────────────────────────────────────────────┤
│  Services (business logic layer)            │  ← All business rules; routers call services, never touch the DB directly
├─────────────────────────────────────────────┤
│  Repositories (data access layer)            │  ← SQLAlchemy queries, isolated per entity
├─────────────────────────────────────────────┤
│  Models (ORM layer)                          │  ← SQLAlchemy declarative models mirroring the SRS §4 schema
└─────────────────────────────────────────────┘
         │
         ▼
   PostgreSQL (+ pgvector)        Redis        Background Task Queue
```

**Rule enforced throughout the codebase:** a router never imports SQLAlchemy directly; it only calls a service function. A service never constructs raw SQL; it only calls repository functions. This keeps business rules (e.g. "payment_mode is required only if amount_paid > 0") testable in isolation from the database and the HTTP layer.

### 2.2 Backend Project Structure

```
backend/
├── app/
│   ├── main.py                     # FastAPI app instantiation, middleware registration, router inclusion
│   ├── config.py                   # Pydantic Settings — loads all env vars from Appendix B of the SRS
│   ├── dependencies.py             # Shared FastAPI Depends() — current_user, require_role(), idempotency check
│   │
│   ├── models/                     # SQLAlchemy ORM models — one file per entity, matches SRS §4.2 exactly
│   │   ├── user.py
│   │   ├── face_embedding.py
│   │   ├── attendance_event.py
│   │   ├── patient.py
│   │   ├── patient_test.py
│   │   ├── test.py
│   │   ├── test_price_history.py
│   │   ├── doctor.py
│   │   ├── franchise.py
│   │   ├── report.py
│   │   ├── expense.py
│   │   ├── login_history.py
│   │   ├── active_session.py
│   │   ├── audit_log.py
│   │   └── otp_request.py
│   │
│   ├── schemas/                    # Pydantic request/response DTOs — one file per entity
│   │   ├── auth.py
│   │   ├── staff.py
│   │   ├── attendance.py
│   │   ├── patient.py
│   │   ├── test.py
│   │   ├── finance.py
│   │   └── security.py
│   │
│   ├── repositories/                # Pure data-access functions, no business rules
│   │   ├── user_repo.py
│   │   ├── patient_repo.py
│   │   ├── test_repo.py
│   │   ├── attendance_repo.py
│   │   ├── audit_repo.py
│   │   └── session_repo.py
│   │
│   ├── services/                    # Business logic — the heart of the system
│   │   ├── auth_service.py
│   │   ├── staff_service.py
│   │   ├── face_service.py          # embedding computation + matching algorithm (§4.2)
│   │   ├── attendance_service.py
│   │   ├── patient_service.py       # Patient ID generation (§4.1), payment derivation
│   │   ├── test_service.py
│   │   ├── report_service.py        # PDF + signature + verification hash
│   │   ├── finance_service.py
│   │   ├── notification_service.py  # abstracted send() + provider registry (§4.5)
│   │   ├── audit_service.py         # hash-chained append-only writer (§4.4)
│   │   └── idempotency_service.py   # Redis-backed idempotency key check (§4.3)
│   │
│   ├── routers/                     # Thin HTTP-layer handlers, one file per resource
│   │   ├── auth_router.py
│   │   ├── staff_router.py
│   │   ├── attendance_router.py
│   │   ├── patient_router.py
│   │   ├── test_router.py
│   │   ├── report_router.py
│   │   ├── finance_router.py
│   │   └── security_router.py
│   │
│   ├── middleware/
│   │   ├── rate_limit.py            # slowapi integration
│   │   ├── audit_context.py         # captures actor/IP for audit_service before request handling
│   │   └── error_handler.py         # global exception → consistent JSON error shape (SRS §9)
│   │
│   ├── background/
│   │   ├── task_runner.py           # FastAPI BackgroundTasks wrapper (or Celery app if queue grows)
│   │   ├── report_pdf_job.py
│   │   ├── email_job.py
│   │   └── audit_integrity_check_job.py   # scheduled hash-chain verification (§4.4)
│   │
│   └── core/
│       ├── security.py              # password hashing, JWT encode/decode
│       └── db.py                    # SQLAlchemy engine/session factory, connection pool config
│
├── migrations/                      # Alembic migration scripts
├── seed/
│   └── seed.py                      # creates admin account + 65 tests (SRS Appendix A)
└── tests/
    ├── test_patient_id_concurrency.py
    ├── test_idempotency.py
    ├── test_view_scope_enforcement.py
    └── test_audit_log_immutability.py
```

### 2.3 Frontend Project Structure

Vanilla HTML/CSS/JS, organized for maintainability without a framework:

```
frontend/
├── index.html                      # Login page
├── admin/
│   ├── dashboard.html
│   ├── staff.html
│   ├── tests.html
│   ├── patients.html
│   ├── revenue.html
│   ├── expenses.html
│   ├── attendance-report.html
│   ├── audit-log.html
│   └── settings.html
├── staff/
│   ├── add-patient.html
│   ├── patients.html
│   └── settings.html
├── attendance-kiosk.html            # dedicated full-screen face-recognition check-in screen
│
├── assets/
│   ├── css/
│   │   ├── tokens.css               # design tokens: cream-vanilla (#EFE6DD) + cherry-cola (#9A0002) brand palette, light+dark variants — see SRS §6.1.2 for full token table
│   │   ├── skeleton.css             # shimmer keyframe animation + skeleton block/row/card variants — see SRS §6.1.5
│   │   ├── components.css           # toast, modal, table, form, badge component styles
│   │   └── layout.css               # responsive grid/breakpoints
│   ├── icons/                       # SVG icon set (single source, one file per icon, sprite-loaded)
│   └── js/
│       ├── api-client.js            # fetch wrapper: attaches auth cookie, Idempotency-Key, handles 401 refresh
│       ├── toast.js                 # toast component (replaces alert())
│       ├── modal.js                 # modal component (replaces confirm())
│       ├── skeleton.js              # renders/swaps skeleton placeholders for tables, cards, charts, forms per SRS §6.1.5
│       ├── theme.js                 # light/dark toggle, persisted preference
│       ├── offline-queue.js         # IndexedDB queue + sync manager (SRS §5.11)
│       ├── face-capture.js          # getUserMedia wrapper, frame capture + quality checks
│       ├── patient-form.js          # Add/Edit Patient logic, test multi-select, QR rendering
│       └── table.js                 # reusable paginated/searchable/sortable table renderer
└── service-worker.js                # caches static assets, intercepts offline-tolerant API calls
```

**Design rule:** no page-specific inline `<script>` logic beyond wiring — all real logic lives in the shared `assets/js/*.js` modules so behavior (e.g. the toast system, offline queue) is identical everywhere it's used, not reimplemented per page.

---

## 3. Detailed Module Design

### 3.1 Authentication Module

**`core/security.py`**
```
function hash_password(plain: str) -> str
    return bcrypt.hash(plain)

function verify_password(plain: str, hashed: str) -> bool
    return bcrypt.verify(plain, hashed)

function create_access_token(user_id, role) -> str
    payload = { sub: user_id, role: role, exp: now + 15min }
    return jwt.encode(payload, JWT_SECRET_KEY)

function create_refresh_token(user_id) -> str
    payload = { sub: user_id, exp: now + 7days, jti: uuid4() }
    return jwt.encode(payload, JWT_SECRET_KEY)
```

**`services/auth_service.py` — login flow**
```
function login(email, password, ip, user_agent) -> LoginResult:
    user = user_repo.get_by_email(email)
    if user is None:
        login_history_repo.record(email, outcome="unknown_email", ip)
        raise AuthError("Invalid credentials")          # generic message — no user enumeration

    if redis.get(f"lockout:{email}") is not None:
        login_history_repo.record(email, outcome="locked_out", ip)
        raise AuthError("Account temporarily locked, try later")

    if not verify_password(password, user.password_hash):
        attempts = redis.incr(f"fail:{email}")
        redis.expire(f"fail:{email}", 15*60)
        if attempts >= 5:
            redis.set(f"lockout:{email}", 1, ex=15*60)
        login_history_repo.record(email, outcome="bad_password", ip)
        raise AuthError("Invalid credentials")

    redis.delete(f"fail:{email}")
    login_history_repo.record(email, outcome="success", ip, user_id=user.id)
    session_repo.create(user.id, ip, user_agent)

    if user.must_reset_password:
        return LoginResult(requires_password_reset=True, reset_token=create_short_lived_token(user.id))

    access = create_access_token(user.id, user.role)
    refresh = create_refresh_token(user.id)
    return LoginResult(access_token=access, refresh_token=refresh)
```

**Dependency injection for route protection (`dependencies.py`):**
```
function get_current_user(request) -> User:
    token = request.cookies["access_token"]
    payload = jwt.decode(token, JWT_SECRET_KEY)    # raises on expiry/invalid signature
    return user_repo.get_by_id(payload.sub)

function require_role(allowed_roles: list):
    return dependency function that raises 403 if current_user.role not in allowed_roles
```

Every Admin-only router function declares `Depends(require_role(["admin"]))`; every authenticated router declares `Depends(get_current_user)`. This is the single enforcement point for RBAC — no controller re-implements role checks inline.

### 3.2 Patient ID Generation Algorithm (`services/patient_service.py`)

```
function generate_patient_code(db_session, year: int) -> str:
    sequence_name = f"patient_seq_{year}"

    # Ensure the sequence exists (idempotent DDL, safe to call every time)
    db_session.execute(f"CREATE SEQUENCE IF NOT EXISTS {sequence_name} START 1")

    # nextval() is atomic at the Postgres engine level — this is the concurrency guarantee.
    # Two simultaneous callers can NEVER receive the same value; no application-level locking needed.
    seq_value = db_session.execute(f"SELECT nextval('{sequence_name}')").scalar()

    padded = str(seq_value).zfill(4)          # minimum 4 digits; grows naturally beyond 9999
    return f"PAT{str(year)[-2:]}{padded}"

function create_patient(payload, current_user, db_session) -> Patient:
    with db_session.begin():                              # single transaction
        code = generate_patient_code(db_session, current_year())
        total = sum(test_repo.get_current_price(t) for t in payload.test_ids)
        patient = patient_repo.insert(
            patient_code=code,
            total_amount=total,
            collected_by=current_user.id,
            **payload.other_fields
        )
        for test_id in payload.test_ids:
            patient_test_repo.insert(patient.id, test_id, price_at_booking=test_repo.get_current_price(test_id))
        audit_service.log("patient.create", actor=current_user, entity=patient)
    return patient
```

**Why this is safe:** `nextval()` on a Postgres sequence is implemented internally without taking a row lock that would block concurrent transactions — this is precisely why sequences (not `SELECT MAX(id)+1 FOR UPDATE`) are the correct primitive here; two staff saving at the same instant will always receive distinct, gapless-per-transaction values.

### 3.3 Idempotency Enforcement (`services/idempotency_service.py`)

```
function with_idempotency(key: str, user_id, handler_fn) -> Response:
    cached = redis.get(f"idem:{key}")
    if cached is not None:
        return deserialize(cached)                # replay original response verbatim, no side effect executes

    result = handler_fn()                          # executes the actual create/update logic exactly once
    redis.set(f"idem:{key}", serialize(result), ex=24*3600)
    return result
```

Applied as a decorator/wrapper on every mutating router (`create_patient`, `record_attendance`, `create_expense`, etc.):

```
@router.post("/patients")
def create_patient_endpoint(payload, idempotency_key: str = Header(...), current_user = Depends(get_current_user)):
    return idempotency_service.with_idempotency(
        key=idempotency_key,
        user_id=current_user.id,
        handler_fn=lambda: patient_service.create_patient(payload, current_user, db)
    )
```

### 3.4 Face Recognition Module (`services/face_service.py`)

**Enrollment:**
```
function enroll_face_sample(user_id, image_bytes) -> EnrollResult:
    faces_detected = detector.detect_faces(image_bytes)
    if len(faces_detected) != 1:
        return EnrollResult(accepted=False, reason="expected exactly one face")
    if faces_detected[0].blur_score > BLUR_THRESHOLD:
        return EnrollResult(accepted=False, reason="image too blurry")

    embedding = embedding_model.compute(faces_detected[0])       # 128-dim vector
    face_embedding_repo.insert(user_id, embedding)

    sample_count = face_embedding_repo.count_for_user(user_id)
    if sample_count >= 3:
        user_repo.update(user_id, face_registered=True, is_active=True)
    return EnrollResult(accepted=True, sample_count=sample_count)
```

**Matching (attendance):**
```
function recognize(image_bytes) -> RecognitionResult:
    faces = detector.detect_faces(image_bytes)
    if len(faces) != 1:
        return RecognitionResult(matched=False, reason="no single clear face")

    probe_embedding = embedding_model.compute(faces[0])

    # pgvector cosine-distance nearest neighbor query:
    # SELECT user_id, 1 - (embedding <=> :probe) AS similarity
    # FROM face_embeddings ORDER BY embedding <=> :probe LIMIT 1;
    best_match = face_embedding_repo.nearest_neighbor(probe_embedding)

    if best_match.similarity < FACE_MATCH_THRESHOLD:      # default 0.6, configurable
        return RecognitionResult(matched=False, reason="below confidence threshold")

    return RecognitionResult(matched=True, user_id=best_match.user_id, confidence=best_match.similarity)
```

**Attendance direction logic:**
```
function log_attendance(user_id, confidence, device_id) -> AttendanceEvent:
    last_event_today = attendance_repo.get_last_event_today(user_id)
    event_type = "check_in" if (last_event_today is None or last_event_today.event_type == "check_out") else "check_out"
    return attendance_repo.insert(user_id, event_type, confidence, device_id)
```

### 3.5 Immutable Audit Log Writer (`services/audit_service.py`)

```
function log(action, actor, entity_type, entity_id, before=None, after=None, ip=None):
    last_row = audit_repo.get_last_row()               # ordered by id DESC, LIMIT 1
    prev_hash = last_row.record_hash if last_row else "GENESIS"

    canonical = json_canonical({
        "action": action, "entity_type": entity_type, "entity_id": entity_id,
        "before": before, "after": after, "occurred_at": now_iso()
    })
    record_hash = sha256(canonical + prev_hash)

    audit_repo.insert(
        actor_user_id=actor.id if actor else None,
        action=action, entity_type=entity_type, entity_id=entity_id,
        before_value=before, after_value=after, ip_address=ip,
        record_hash=record_hash, prev_hash=prev_hash
    )
```

**Scheduled integrity check (`background/audit_integrity_check_job.py`), run nightly:**
```
function verify_chain():
    rows = audit_repo.get_all_ordered_by_id()
    expected_prev = "GENESIS"
    for row in rows:
        recomputed = sha256(canonical(row.fields_excluding_hashes) + expected_prev)
        if recomputed != row.record_hash:
            alert_admin("AUDIT LOG INTEGRITY VIOLATION at row id={row.id}")
            break
        expected_prev = row.record_hash
```

**Database-level enforcement (applied once via a migration, not application code):**
```sql
REVOKE UPDATE, DELETE ON audit_logs FROM app_role;
GRANT INSERT, SELECT ON audit_logs TO app_role;
```

### 3.6 Notification Service (`services/notification_service.py`)

```
interface NotificationProvider:
    function send(event_type, recipient, context) -> bool

class EmailProvider implements NotificationProvider:
    function send(event_type, recipient, context):
        template = load_template(event_type)                 # e.g. "otp_email.html", "report_ready_email.html"
        html = render(template, context, lab_name="Akriti Diagnostics Center")
        fastapi_mail.send(to=recipient.email, subject=..., html=html)

class WhatsAppProvider implements NotificationProvider:      # stub — not enabled in v1
    function send(event_type, recipient, context):
        raise NotImplementedError("Enable in future release")

class SmsProvider implements NotificationProvider:            # stub — not enabled in v1
    function send(event_type, recipient, context):
        raise NotImplementedError("Enable in future release")

PROVIDER_REGISTRY = {
    "otp": [EmailProvider()],
    "report_ready": [EmailProvider()],
    "password_reset": [EmailProvider()],
}

function notify(event_type, recipient, context):
    for provider in PROVIDER_REGISTRY.get(event_type, []):
        provider.send(event_type, recipient, context)
```

Adding WhatsApp later means implementing `WhatsAppProvider.send()` and adding it to `PROVIDER_REGISTRY["report_ready"]` — zero changes to any calling code in `report_service.py` or elsewhere.

### 3.7 Offline Sync Manager (`assets/js/offline-queue.js`, frontend)

```
function queueAction(endpoint, payload):
    key = generateUUID()
    record = { key, endpoint, payload, queuedAt: now() }
    indexedDB.add("pendingActions", record)
    updateOfflineBadge()

function attemptSync():
    if not navigator.onLine: return
    pending = indexedDB.getAll("pendingActions").sortBy("queuedAt")   # preserve original order
    for record in pending:
        response = apiClient.post(record.endpoint, record.payload, headers={"Idempotency-Key": record.key})
        if response.ok:
            indexedDB.remove("pendingActions", record.key)
            toast.success(`Synced: ${record.endpoint}`)
        else:
            break    # stop on first failure, retry whole remaining queue on next connectivity event, preserving order

window.addEventListener("online", attemptSync)
setInterval(attemptSync, 30000)     # periodic retry in case the 'online' event is unreliable on some devices
```

The `Idempotency-Key` generated at queue-time (not at sync-time) is what guarantees correctness even if `attemptSync` runs twice concurrently (e.g. both the `online` event and the interval fire close together) — the second attempt for the same record simply receives the replayed response from `idempotency_service`.

---

## 4. Sequence Design (Key Workflows)

### 4.1 Add Patient (Online, Happy Path)

```
Staff (browser)        Frontend JS            FastAPI Router         Patient Service        DB / Redis
     │  fills form           │                       │                      │                    │
     │──submit──────────────▶│                       │                      │                    │
     │                       │ disable submit button  │                      │                    │
     │                       │──POST /patients──────▶│                      │                    │
     │                       │  (Idempotency-Key: X)  │──check Redis(X)─────────────────────────▶│
     │                       │                       │◀── not found ─────────────────────────────│
     │                       │                       │──create_patient()──▶│                    │
     │                       │                       │                      │──nextval(seq)─────▶│
     │                       │                       │                      │◀── PAT260042 ──────│
     │                       │                       │                      │──insert patient────▶│
     │                       │                       │                      │──insert patient_tests──▶│
     │                       │                       │                      │──audit_service.log()──▶│
     │                       │                       │◀── Patient object ──│                    │
     │                       │                       │──store result @ Redis(X)───────────────▶│
     │                       │◀── 201 Created ───────│                      │                    │
     │◀──toast "Saved" ───────│                       │                      │                    │
```

### 4.2 Face Recognition Attendance (Real-Time)

```
Kiosk camera        face-capture.js         /attendance/recognize        face_service          pgvector index
    │──frame────────────▶│                          │                          │                      │
    │                    │──POST frame─────────────▶│                          │                      │
    │                    │                          │──recognize()────────────▶│                      │
    │                    │                          │                          │──embedding compute──│
    │                    │                          │                          │──nearest neighbor───▶│
    │                    │                          │                          │◀── best_match ───────│
    │                    │                          │◀── confidence=0.82 ─────│                      │
    │                    │◀── matched: Ramesh ───────│                          │                      │
    │◀── toast "Checked In: Ramesh" ──────────────────│                          │                      │
```

If `confidence < threshold`: response is `matched: false`; frontend shows "Face not recognized clearly — awaiting Admin review" toast and posts to a pending-review queue instead of an attendance event.

### 4.3 Offline Add Patient → Reconnect → Sync

```
[Offline]
Staff fills Add Patient form → offline-queue.js generates Idempotency-Key locally →
   payload + key stored in IndexedDB → toast: "Offline — 1 action queued"

[Connectivity restored]
'online' event fires → attemptSync() reads IndexedDB in original order →
   POST /patients with the SAME Idempotency-Key generated while offline →
   backend has never seen this key → executes normally → Patient created once →
   IndexedDB record removed → toast: "Synced"

[Edge case: sync fires twice due to flaky 'online' event]
   Second POST arrives with same Idempotency-Key → Redis already has a stored response →
   backend returns the ORIGINAL result, no second patient row created
```

### 4.4 Forced First-Login Password Reset

```
User submits temp password → auth_service.login() succeeds credential-check →
   sees must_reset_password = true → returns { requires_password_reset: true, reset_token } →
   frontend does NOT set a full session yet → shows blocking (but toast/modal-based, not native) 
   "Set New Password" modal → user submits new password + reset_token →
   backend validates reset_token, validates password against FR-1.4 regex →
   updates password_hash, sets must_reset_password = false →
   NOW issues full access+refresh session → user lands on dashboard
```

---

## 5. Interface Design (API Contract Sketches)

### 5.1 Example Request/Response — Create Patient

**Request**
```
POST /api/v1/patients
Headers: Idempotency-Key: 3f9a1c2e-...
{
  "name": "Sunita Devi",
  "age": 34,
  "gender": "female",
  "mobile": "9876543210",
  "doctor_id": "uuid-or-null",
  "test_ids": ["uuid1", "uuid2"],
  "sample_date": "2026-07-11",
  "estimated_report_date": "2026-07-13",
  "amount_paid": 300,
  "payment_mode": "cash"
}
```

**Response — 201**
```
{
  "id": "uuid",
  "patient_code": "PAT260042",
  "total_amount": 450.00,
  "amount_paid": 300.00,
  "amount_due": 150.00,
  "status": "sample_collected",
  "created_at": "2026-07-11T10:15:00Z"
}
```

**Response — 422 (validation failure example)**
```
{
  "detail": [
    { "loc": ["body", "mobile"], "msg": "must be a valid 10-digit Indian mobile number", "type": "value_error" }
  ]
}
```

### 5.2 Middleware Stack Order (`main.py`)

Order matters — each middleware wraps the next:

```
1. CORS middleware (restricts to configured frontend origin only)
2. HTTPS/HSTS enforcement
3. Rate limiting (slowapi) — rejects before any auth/DB work happens
4. Audit context middleware — captures request IP/user-agent into request-scoped context for audit_service
5. Global exception handler — catches all unhandled exceptions, returns SRS §9 error shape
6. Route handlers (with per-route Depends(get_current_user) / Depends(require_role))
```

---

## 6. Database Physical Design Notes

- **Connection pooling:** SQLAlchemy `QueuePool` sized at `pool_size=10, max_overflow=20` for the initial single-instance deployment — tuned upward only if monitoring shows saturation, not pre-emptively over-provisioned.
- **Vector index:** `face_embeddings.embedding` uses an `hnsw` index (`vector_cosine_ops`) — chosen over `ivfflat` because `hnsw` gives better recall at the small-to-medium row counts expected here (hundreds, not millions, of embeddings) without needing a separate "training" step on the index.
- **Partitioning (future, not required at launch):** `patients` and `audit_logs` are designed so that range-partitioning by year can be introduced later purely as a DBA-level operation, since `patient_code` already encodes the year and `created_at`/`occurred_at` are natural partition keys — no application code depends on the table being unpartitioned.
- **Generated column:** `patients.amount_due` is a Postgres `GENERATED ALWAYS AS ... STORED` column — this removes an entire class of bugs where application code could compute or display a stale due-amount.

---

## 7. Deployment Design

```
                         ┌─────────────────────┐
                         │   Cloudflare (DNS,   │
                         │   basic DDoS layer)  │
                         └──────────┬───────────┘
                                    │ HTTPS
                         ┌──────────▼───────────┐
                         │   Nginx               │  TLS termination, static file serving,
                         │   (reverse proxy)      │  limit_req_zone rate limiting
                         └──────────┬────────────┘
                                    │
                    ┌───────────────┴────────────────┐
                    │                                 │
          ┌─────────▼─────────┐             ┌─────────▼─────────┐
          │ Gunicorn/Uvicorn    │   (scale    │ Gunicorn/Uvicorn    │
          │ worker instance 1   │   out here  │ worker instance 2   │
          │ (FastAPI app)       │   later)    │ (FastAPI app)       │
          └─────────┬───────────┘             └─────────┬───────────┘
                    │                                     │
          ┌─────────┴─────────────────────────────────────┴───────────┐
          │                                                             │
   ┌──────▼───────┐                                          ┌─────────▼────────┐
   │ PostgreSQL     │◀── nightly encrypted backup ──────────▶│  Off-server backup │
   │ (+ pgvector)   │                                          │  storage           │
   └────────────────┘                                          └────────────────────┘
          │
   ┌──────▼───────┐
   │    Redis       │  idempotency keys, rate-limit counters, lockout counters
   └────────────────┘
```

**CI/CD (recommended minimal pipeline):**
1. On push to `main`: run `pytest` (including the concurrency/idempotency/audit-immutability tests listed in SRS §10)
2. Run `alembic upgrade head` against a staging database as a migration dry-run
3. On success, deploy to production via a simple blue-green script (spin up new Gunicorn workers, health-check them, switch Nginx upstream, drain and stop old workers) — avoids kicking staff out mid-shift during a deploy, satisfying the zero-downtime-deploy goal noted in earlier planning.

---

## 8. Error Handling Design

Centralized in `middleware/error_handler.py`: every exception type maps to exactly one response shape (SRS §9 table). Domain-specific exceptions (`AuthError`, `ValidationError`, `NotFoundError`, `ConflictError`, `RateLimitError`) are raised from services and caught once at this middleware layer — individual route handlers never write their own try/except-to-HTTP-status logic, keeping that mapping consistent everywhere.

---

## 9. Logging & Monitoring Design

- **Application logs:** structured JSON logs (not plain text) for every request (method, path, status, latency, user_id) and every unhandled exception (full stack trace, request context) — shipped to an error-tracking service (e.g. Sentry) so failures surface proactively rather than being discovered via a staff complaint.
- **Business-event logs:** distinct from the immutable `audit_logs` table — these are operational logs (e.g. "email send failed, retrying") for debugging, not compliance, and may use standard log rotation/retention.
- **Metrics to expose on `/health` or a companion `/metrics` endpoint:** DB pool utilization, Redis connectivity, background task queue depth — cheap to add now, valuable the first time something goes wrong at 8pm and no developer is around to guess blindly.

---

## Appendix — Traceability Note

Every module and algorithm in this SDD implements a specific FR/NFR from SRS v3.0:
- §3.2 (Patient ID) → FR-4.2
- §3.3 (Idempotency) → FR-11.2, NFR-4
- §3.4 (Face Service) → FR-2.2, FR-3.1, FR-3.2
- §3.5 (Audit Log) → FR-13.1, FR-13.2
- §3.6 (Notification Service) → FR-10.1
- §3.7 (Offline Sync) → FR-11.1, FR-11.2

This document should be read alongside SRS v3.0; the SRS is the contract of *what* is correct, this SDD is the design of *how* that contract is fulfilled in code.
