# SOFTWARE REQUIREMENTS SPECIFICATION
# Akriti Diagnostics Center — Pathology Laboratory Management System

**Document Version:** 4.0
**Status:** Final — Ready for Development
**Classification:** Internal / Confidential
**Prepared for:** Akriti Diagnostics Center

---

## Document Control

| Version | Description |
|---|---|
| 1.0 | Initial requirements — core admin/staff dashboards, tests, patient overview |
| 2.0 | Added biometric attendance, offline sync, expense management, immutable audit logs |
| 3.0 | Full engineering specification — schema-level data model, API contracts, detailed flows, non-functional acceptance criteria |
| 4.0 | Enterprise enhancement release — full Admin/Staff parity, enhanced multi-stage face enrollment with liveness detection, dedicated Face Recognition Attendance application sharing the same database, offline-first expansion (payments, receipts, attendance), expanded Expense module, full Dashboard KPI suite, Patient Timeline, Report Version Control, Dynamic Report Builder (future-ready), Lab Settings module, enhanced Login History/Active Sessions, Global Search, Analytics & Export, formal Receipt/Invoice/Expense/Attendance numbering schemes, expanded notification-provider abstraction, additional enterprise security controls, and architecture placeholders for future modules. All content from v3.0 is preserved unchanged; this version only extends it. |

---

## 1. Introduction

### 1.1 Purpose

This document is the authoritative technical specification for the design and construction of the Akriti Diagnostics Center Pathology Laboratory Management System (hereafter "the System"). It defines functional behavior, data structures, interface contracts, and quality attributes to a level of detail sufficient for direct implementation without further requirements discovery. It is written for backend engineers, frontend engineers, and any AI coding agent responsible for producing the running system.

### 1.2 Intended Audience

Software architects, backend/frontend developers, QA engineers, and the system owner (lab management), who will use this document to verify that delivered functionality matches specification.

### 1.3 Scope

The System is a single-tenant (single-branch, multi-branch-ready) web application supporting:
- Staff identity management with biometric (facial) enrollment and attendance
- Patient registration, test billing, and sample-to-report lifecycle tracking
- Financial operations: revenue tracking, expense tracking, and net profitability reporting
- Security and compliance infrastructure: authentication, session control, login history, and tamper-evident audit logging
- Offline-tolerant data capture at the point of service, with guaranteed-consistent synchronization

**Out of scope (explicit exclusions):**
- Patient-facing portal or patient login of any kind
- A distinct "Doctor" user role, login, or doctor-facing module — doctors exist solely as a reference lookup table used during patient registration
- Third-party payment gateway integration (no Razorpay/PayU/Paytm API, no automated transaction verification) — UPI QR codes are generated locally against the lab's own VPA (UPI ID); payment receipt confirmation is a manual staff action
- Outbound WhatsApp/SMS messaging (the notification subsystem must be architected to support adding these later without modification to calling code — see §5.10)

### 1.4 Definitions, Acronyms, and Abbreviations

| Term | Meaning |
|---|---|
| System | The complete software product described in this document |
| Admin | Lab owner/manager role; superset of Staff permissions |
| Staff | Lab counter/technical employee role |
| Patient ID | System-generated unique identifier, format `PAT{YY}{SEQ}` |
| VPA | Virtual Payment Address (UPI ID) |
| JWT | JSON Web Token |
| FR | Functional Requirement |
| NFR | Non-Functional Requirement |
| Embedding | A fixed-length numeric vector representation of a face, used for similarity-based recognition |
| Idempotency Key | A client-generated unique token attached to a mutating request, used by the server to guarantee at-most-once execution |
| WAL | Write-Ahead Log (PostgreSQL durability mechanism) |

### 1.5 References

Internal source materials: Akriti Diagnostics Center test-rate quotation (65-test master price list); prior requirement discussions consolidated into this document.

---

## 2. Overall Description

### 2.1 Product Perspective

The System is a new, standalone, self-hosted application. It is not an extension of any existing third-party lab-management SaaS. It consists of three deployable units:

1. **Backend API service** (FastAPI, Python) — stateless, horizontally scalable
2. **Frontend web client** (HTML/CSS/vanilla JS, PWA-capable) — served as static assets, works on desktop, tablet, and phone browsers
3. **PostgreSQL database** — single source of truth, including the `pgvector` extension for biometric similarity search

Supporting infrastructure: Redis (caching, idempotency-key store, rate-limit counters), Nginx (reverse proxy, TLS termination, first-layer rate limiting), an SMTP relay (Gmail, via App Password) for outbound email.

### 2.2 Product Functions (Summary)

1. Role-based authentication (Admin, Staff) with email + password and email-OTP login
2. Staff lifecycle management including mandatory biometric enrollment
3. Real-time facial-recognition attendance logging against the same database
4. Patient registration and editing by both Admin and Staff, with multi-test billing
5. Test catalog management
6. Patient/sample lifecycle tracking (collected → processing → report ready)
7. Digitally signed report generation and secure delivery
8. Revenue analytics and expense bookkeeping with net profitability reporting
9. Offline-tolerant data capture with guaranteed-consistent background synchronization
10. Full security subsystem: rate limiting, lockouts, session management, login history, and immutable audit logging

### 2.3 User Classes and Characteristics

| Class | Technical proficiency | Primary environment | Notes |
|---|---|---|---|
| Admin | Low-to-moderate; business owner, not a technologist | Desktop primarily, occasional phone | Needs oversight views, financial reports, and full override capability |
| Staff | Low; fast-paced counter environment, high daily repetition of the same 2–3 tasks | Tablet primarily, some desktop | Needs speed, minimal clicks, tolerant of intermittent connectivity, must never be blocked by system errors |

### 2.4 Operating Environment

- Server OS: Linux (Ubuntu LTS recommended)
- Application server: Uvicorn workers managed by Gunicorn
- Reverse proxy: Nginx, TLS 1.2+ only
- Database: PostgreSQL 15+ with `pgvector` extension
- Client browsers: current versions of Chrome, Edge, Safari, Firefox on Windows, Android, iOS
- Camera hardware: any standard webcam (laptop-integrated or USB), minimum 720p recommended for reliable face-recognition accuracy

### 2.5 Design and Implementation Constraints

- Frontend must be plain HTML/CSS/JavaScript — no SPA framework (React/Vue/Angular) — but must still be modular (component-like reusable JS files/functions), not a single monolithic script.
- Backend must be FastAPI/Python; ORM must be SQLAlchemy with Alembic-managed migrations — no direct unmanaged schema changes in production.
- No native browser dialogs (`alert`/`confirm`/`prompt`) may appear anywhere in the UI (see §6.1).
- No emoji characters may appear anywhere in UI strings, icons, logs, or generated documents; all iconography is SVG.

### 2.6 Assumptions and Dependencies

- The lab has (or will create) a dedicated Gmail account with 2-Step Verification enabled to generate an SMTP App Password.
- The lab has its own UPI VPA for receiving QR-based payments; the System only renders QR codes against this VPA, it does not process or settle payments.
- Initial deployment is single-branch; the schema reserves a `branch_id` column pattern (nullable/defaulted for now) so multi-branch expansion does not require a schema migration that breaks existing data.

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
[ Browser / Tablet / Kiosk Camera ]
            │  HTTPS
            ▼
   [ Nginx Reverse Proxy ]  ── rate limiting, TLS termination, static asset serving
            │
            ▼
   [ FastAPI Application (Uvicorn/Gunicorn workers) ]
        │        │              │
        │        │              └── [ Background Task Runner ] ── PDF generation, email dispatch, embedding computation
        │        │
        │        └── [ Redis ] ── idempotency keys, rate-limit counters, session/cache store
        │
        └── [ PostgreSQL (+ pgvector) ] ── all persistent data, single source of truth
                        │
                        └── [ Nightly Backup Job ] ── encrypted dump → off-server storage

   [ SMTP Relay (Gmail App Password) ] ←── outbound email only, invoked by background tasks
```

### 3.2 Component Breakdown

| Component | Responsibility |
|---|---|
| `auth` module | Login, OTP issuance/verification, JWT issuance/refresh, password policy enforcement, lockouts |
| `staff` module | CRUD for staff, face-enrollment workflow, view-scope configuration |
| `attendance` module | Face-embedding matching, check-in/check-out event logging, attendance reporting |
| `patients` module | Patient CRUD, Patient ID generation, test-selection billing, payment recording |
| `tests` module | Test catalog CRUD |
| `reports` module | Report upload/generation, digital signature embedding, secure delivery links |
| `finance` module | Revenue aggregation, expense CRUD, net profit/loss computation |
| `notifications` module | Abstracted send-interface; Email provider implemented, others stubbed |
| `sync` module | Offline action queue ingestion, idempotent replay handling |
| `security` module | Login history, active sessions, immutable audit log writer/reader |

### 3.3 Technology Stack and Justification

| Layer | Choice | Justification |
|---|---|---|
| Frontend | HTML/CSS/JS + PWA (Service Worker, IndexedDB) | Explicit requirement; PWA layer enables offline queueing without a framework |
| Backend | FastAPI | Native async support, automatic OpenAPI schema generation (useful for contract-testing the API surface defined in §8), first-class Pydantic validation |
| Database | PostgreSQL + `pgvector` | ACID guarantees for financial/patient data; `pgvector` gives production-grade nearest-neighbor search for face embeddings without a separate vector database |
| ORM/Migrations | SQLAlchemy + Alembic | Explicit, reviewable schema migrations — critical for a system handling patient and financial records |
| Cache/Ephemeral store | Redis | Sub-millisecond idempotency-key lookups and rate-limit counters; also usable later for session revocation lists |
| Face Recognition | `face_recognition` (dlib ResNet embedding model) or DeepFace | Mature, well-documented, produces fixed-length embeddings compatible with `pgvector` cosine-distance search |
| PDF Generation | WeasyPrint | HTML/CSS-to-PDF rendering keeps report templates maintainable by anyone who knows CSS, not a proprietary PDF DSL |
| Mail | `fastapi-mail` | Python-native SMTP client with async support, template rendering built in |

### 3.4 Deployment Architecture

Single application server initially. Because JWT-based auth is stateless and all shared mutable state (idempotency keys, rate limits) lives in Redis rather than in-process memory, a second Uvicorn/Gunicorn instance can be added behind Nginx load-balancing at any time with no code change — this satisfies the future-scalability requirement without over-engineering the initial deployment.

---

## 4. Data Model

### 4.1 Entity List

`staff`, `admin_accounts` (or a unified `users` table with a `role` discriminator — recommended, see note below), `face_embeddings`, `attendance_events`, `patients`, `patient_tests` (junction), `tests`, `doctors`, `franchises`, `transactions`, `expenses`, `reports`, `login_history`, `active_sessions`, `audit_logs`, `otp_requests`, `idempotency_keys`, `offline_sync_queue` (transient, may be client-side only).

**Design note:** Admin and Staff are recommended to be modeled as a single `users` table with a `role` enum column (`admin` / `staff`), rather than two separate tables, since both authenticate through the same login flow and share the majority of fields (email, password_hash, name, status). Role-specific fields (Aadhar, view_scope, face embedding link) are nullable for the admin row types where not applicable.

### 4.2 Detailed Table Schemas

**`users`**
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK, default `gen_random_uuid()` |
| role | ENUM('admin','staff') | NOT NULL |
| name | VARCHAR(120) | NOT NULL |
| email | VARCHAR(255) | NOT NULL, UNIQUE |
| password_hash | VARCHAR(255) | NOT NULL |
| mobile | CHAR(10) | CHECK (mobile ~ '^[6-9][0-9]{9}$') |
| dob | DATE | NULL (staff only) |
| aadhar_encrypted | BYTEA | NULL, encrypted via pgcrypto (staff only) |
| aadhar_last4 | CHAR(4) | NULL, for masked display without decrypting |
| view_scope | ENUM('all','own') | DEFAULT 'own' (staff only, ignored for admin) |
| face_registered | BOOLEAN | DEFAULT FALSE |
| is_active | BOOLEAN | DEFAULT FALSE — flips TRUE only after face enrollment completes for staff; admin defaults TRUE post password reset |
| must_reset_password | BOOLEAN | DEFAULT TRUE |
| branch_id | UUID | NULL, reserved for future multi-branch use |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| deactivated_at | TIMESTAMPTZ | NULL (soft delete) |

Indexes: UNIQUE(email); INDEX(role); INDEX(is_active).

**`face_embeddings`**
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id, NOT NULL |
| embedding | VECTOR(128) | NOT NULL (`pgvector` type; 128-dim typical for dlib ResNet model) |
| sample_index | SMALLINT | 1–5, which capture sample this is |
| created_at | TIMESTAMPTZ | DEFAULT now() |

Index: `ivfflat` or `hnsw` index on `embedding` using cosine distance ops for fast nearest-neighbor matching at attendance time.

**`attendance_events`**
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id, NOT NULL |
| event_type | ENUM('check_in','check_out') | NOT NULL |
| matched_confidence | NUMERIC(5,4) | NOT NULL |
| device_id | VARCHAR(64) | kiosk/device identifier |
| event_time | TIMESTAMPTZ | DEFAULT now() |
| source | ENUM('online','offline_synced') | DEFAULT 'online' |

Index: INDEX(user_id, event_time DESC).

**`patients`**
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| patient_code | VARCHAR(16) | NOT NULL, UNIQUE — the human-facing `PATyyNNNN` ID |
| name | VARCHAR(120) | NOT NULL |
| age | SMALLINT | NOT NULL, CHECK (age > 0 AND age < 130) |
| gender | ENUM('male','female','trans') | NOT NULL |
| mobile | CHAR(10) | NOT NULL, CHECK format |
| doctor_id | UUID | FK → doctors.id, NULL if self-referred |
| collected_by | UUID | FK → users.id, NOT NULL |
| collection_type | ENUM('self_center','courier_serum','courier_redcliffe') | NOT NULL |
| sample_date | DATE | DEFAULT current_date, editable |
| estimated_report_date | DATE | NOT NULL |
| total_amount | NUMERIC(10,2) | NOT NULL |
| amount_paid | NUMERIC(10,2) | DEFAULT 0 |
| amount_due | NUMERIC(10,2) | GENERATED ALWAYS AS (total_amount - amount_paid) STORED |
| payment_mode | ENUM('cash','qr') | NULL if fully due |
| status | ENUM('sample_collected','under_process','report_ready') | DEFAULT 'sample_collected' |
| processing_note | VARCHAR(120) | e.g. "Under Process by Ramesh" or "Under Process by Redcliffe" |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | auto-updated via trigger |
| deleted_at | TIMESTAMPTZ | NULL (soft delete) |

Indexes: UNIQUE(patient_code); INDEX(mobile); INDEX(created_at DESC); INDEX(status); INDEX(doctor_id).

Sequence object: `patient_seq_2026` (and one created per calendar year programmatically) backing `patient_code` generation — see §5.4.2.

**`patient_tests`** (junction, many-to-many patients↔tests with price snapshot)
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| patient_id | UUID | FK → patients.id |
| test_id | UUID | FK → tests.id |
| price_at_booking | NUMERIC(10,2) | NOT NULL — snapshot, so later price edits never retroactively change historical bills |

**`tests`**
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(150) | NOT NULL, UNIQUE (case-insensitive) |
| price | NUMERIC(10,2) | NOT NULL |
| category | VARCHAR(80) | NULL |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**`test_price_history`**
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| test_id | UUID | FK → tests.id |
| old_price | NUMERIC(10,2) | |
| new_price | NUMERIC(10,2) | |
| changed_by | UUID | FK → users.id |
| changed_at | TIMESTAMPTZ | DEFAULT now() |

**`doctors`**
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(120) | NOT NULL |
| clinic_name | VARCHAR(150) | NULL |
| is_active | BOOLEAN | DEFAULT TRUE |

UNIQUE(name, clinic_name) to prevent near-duplicate doctor entries.

**`franchises`**
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| name | VARCHAR(100) | NOT NULL, e.g. "Serum Analysis", "Redcliffe Labs" |
| contact_info | VARCHAR(200) | NULL |
| default_tat_days | SMALLINT | expected turnaround time, for overdue flagging |

**`reports`**
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| patient_id | UUID | FK → patients.id |
| file_path | VARCHAR(255) | storage path, outside web root |
| signed | BOOLEAN | DEFAULT FALSE |
| signature_applied_at | TIMESTAMPTZ | NULL |
| verification_hash | VARCHAR(128) | NULL — for the optional tamper-verification QR (§5.7) |
| uploaded_by | UUID | FK → users.id |
| uploaded_at | TIMESTAMPTZ | DEFAULT now() |

**`expenses`**
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| category | ENUM('rent','reagents','salaries','utilities','equipment_maintenance','courier_charges','misc') | NOT NULL |
| description | VARCHAR(200) | NULL |
| amount | NUMERIC(10,2) | NOT NULL |
| paid_to | VARCHAR(150) | NULL |
| payment_mode | ENUM('cash','bank_transfer','upi') | NOT NULL |
| attachment_path | VARCHAR(255) | NULL |
| expense_date | DATE | NOT NULL |
| recorded_by | UUID | FK → users.id |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**`login_history`**
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id, NULL if login attempted with unknown email |
| email_attempted | VARCHAR(255) | NOT NULL |
| outcome | ENUM('success','bad_password','bad_otp','locked_out','unknown_email') | NOT NULL |
| ip_address | INET | NOT NULL |
| user_agent | VARCHAR(255) | NULL |
| attempted_at | TIMESTAMPTZ | DEFAULT now() |

**`active_sessions`**
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK → users.id |
| refresh_token_hash | VARCHAR(255) | NOT NULL — never store the raw token |
| device_label | VARCHAR(100) | derived from user-agent |
| ip_address | INET | |
| issued_at | TIMESTAMPTZ | DEFAULT now() |
| last_active_at | TIMESTAMPTZ | updated on each refresh |
| revoked_at | TIMESTAMPTZ | NULL |

**`audit_logs`** (immutable — see §5.13 for enforcement mechanism)
| Column | Type | Constraints |
|---|---|---|
| id | BIGSERIAL | PK, sequential — order matters for the hash chain |
| actor_user_id | UUID | FK → users.id, NULL for system-generated events |
| action | VARCHAR(60) | e.g. `patient.edit`, `test.price_change`, `staff.deactivate` |
| entity_type | VARCHAR(40) | |
| entity_id | UUID | |
| before_value | JSONB | NULL |
| after_value | JSONB | NULL |
| ip_address | INET | |
| occurred_at | TIMESTAMPTZ | DEFAULT now() |
| record_hash | CHAR(64) | SHA-256 of this row's canonical content |
| prev_hash | CHAR(64) | `record_hash` of the immediately preceding row (chain link) |

**`idempotency_keys`** (Redis-backed primarily; optionally mirrored to Postgres for audit purposes)
| Column | Type | Constraints |
|---|---|---|
| key | VARCHAR(100) | PK |
| user_id | UUID | |
| response_snapshot | JSONB | the original response, replayed verbatim on duplicate calls |
| expires_at | TIMESTAMPTZ | short TTL, e.g. 24h |

**`otp_requests`**
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| email | VARCHAR(255) | NOT NULL |
| otp_hash | VARCHAR(255) | NOT NULL — never store plaintext OTP |
| purpose | ENUM('login','password_reset') | |
| expires_at | TIMESTAMPTZ | NOT NULL, issued_at + 5 minutes |
| used_at | TIMESTAMPTZ | NULL |
| requesting_ip | INET | |

### 4.3 Relationships (Summary)

- `users` 1—N `face_embeddings` (one staff member has 3–5 embedding rows)
- `users` 1—N `attendance_events`
- `users` 1—N `patients` (as `collected_by`)
- `patients` N—N `tests` via `patient_tests`
- `patients` N—1 `doctors`
- `patients` 1—N `reports`
- `tests` 1—N `test_price_history`
- `users` 1—N `login_history`, 1—N `active_sessions`
- `users` 1—N `audit_logs` (as actor)

### 4.4 Indexing Strategy

All foreign keys indexed by default via FK constraint. Additional composite/functional indexes:
- `patients(created_at DESC)` for default latest-first listing
- `patients(status)` for dashboard "pending reports" counts
- `patients(mobile)` for returning-patient lookup
- `face_embeddings(embedding)` using `ivfflat`/`hnsw` vector index for sub-second attendance matching even with hundreds of staff × 5 embeddings
- `audit_logs(occurred_at)` for date-range compliance queries

---

## 5. Functional Requirements

Each requirement below is written with a unique ID, trigger/precondition, main flow, and exception handling, to remove ambiguity for implementation.

### 5.1 Authentication & Session Management

**FR-1.1 — Login**
- Precondition: user account exists and `is_active = true`.
- Main flow: user submits email + password → backend verifies hash → if `must_reset_password = true`, response instructs frontend to show the forced password-reset modal before issuing a full session → otherwise issue JWT access token (15 min) + refresh token (7 days) as httpOnly/Secure/SameSite=Strict cookies → log a `login_history` row with outcome `success` → create an `active_sessions` row.
- Exception flow: wrong password → increment failed-attempt counter (Redis, keyed by email) → log `login_history` with outcome `bad_password` → after 5 failures within 15 minutes, lock account for 15 minutes (`locked_out` outcome on further attempts) and surface a toast, never a native alert.

**FR-1.2 — OTP Login**
- User requests OTP for their email → backend checks rate limit (max 3 per 10 min per email AND per IP) → generates 6-digit OTP, stores only its hash with 5-minute expiry in `otp_requests` → sends via the Notification Service (Email provider) → user submits OTP → backend hashes input and compares → on match, marks `used_at`, proceeds as a successful login (same session issuance as FR-1.1) → OTP is single-use; a second verification attempt with the same code fails even if not yet expired.

**FR-1.3 — Forgot Password**
- Same OTP mechanism as FR-1.2 with `purpose = password_reset` → successful OTP verification grants a short-lived (10 min) password-reset token, not a full session → user sets new password against the policy in FR-1.4 → all existing `active_sessions` for that user are revoked as a security measure.

**FR-1.4 — Password Policy**
- Enforced identically client-side (immediate feedback) and server-side (authoritative): minimum 6 characters, at least one letter and one digit, no special characters permitted, case-insensitive. Regex: `^(?=.*[A-Za-z])(?=.*\d)[A-Za-z0-9]{6,}$`.

**FR-1.5 — Seed Admin Account**
- A one-time seed script (run via Alembic data migration or a standalone `seed.py`) creates: email `kunaldixit.2995@gmail.com`, `role = admin`, temporary password `123456` (hashed before storage, never stored plaintext), `must_reset_password = true`. This account follows the identical forced-reset flow as any staff account — no code path may special-case it as permanently exempt from password policy.

### 5.2 Staff Management & Face Registration

**FR-2.1 — Add Staff (Admin only)**
- Fields and validation: name (required), mobile (regex `^[6-9]\d{9}$`), email (unique, RFC-valid), DOB (valid past date, age auto-computed server-side, never trust a client-sent age value), Aadhar (exactly 12 digits, Verhoeff-checksum validation recommended, unique, encrypted via `pgcrypto` before storage, only last 4 digits retained in plaintext-adjacent column for masked UI display), view_scope (`all`/`own`, default `own`).
- On save: `is_active` is set to `false` and a temporary password is generated and emailed. The account **cannot be flipped to `is_active = true` until FR-2.2 (face registration) completes** — enforced by a database check or application-layer gate, not merely a UI step that can be skipped.

**FR-2.2 — Mandatory Face Registration**
- Precondition: staff record created via FR-2.1, `face_registered = false`.
- Main flow: enrollment UI activates the device camera → captures 3–5 frames across different head angles/expressions → each frame is validated for a single clearly detected face (reject frames with zero or multiple faces, poor lighting, or excessive blur) → each accepted frame is passed through the embedding model → resulting 128-dimension vectors stored as rows in `face_embeddings` → once minimum sample count (3) is reached, `face_registered = true` and `is_active = true` are set together in one transaction.
- Exception flow: if fewer than 3 usable samples are captured after 5 attempts, the flow surfaces a clear retry prompt (toast-based) — the staff account remains inactive until this is resolved; Admin can re-open this flow anytime from Edit Staff to re-enroll (e.g. replacing degraded samples).

**FR-2.3 — Edit/Deactivate Staff (Admin only)**
- All fields editable except Aadhar (Aadhar changes require an explicit "Override Aadhar" action that is separately logged in `audit_logs` with justification text, since Aadhar correction is rare and sensitive).
- Deactivate is a soft delete (`deactivated_at` set, `is_active = false`); the record and all its historical patient/attendance associations remain intact for reporting and audit purposes.

### 5.3 Real-Time Face Recognition Attendance

**FR-3.1 — Attendance Check-In/Check-Out**
- Precondition: staff has completed FR-2.2.
- Main flow: kiosk/attendance screen streams camera frames client-side → on detecting a face, the frontend sends a single captured frame to `POST /api/v1/attendance/recognize` → backend computes an embedding for the incoming frame → performs a `pgvector` cosine-distance nearest-neighbor query against all stored `face_embeddings` → if the best match's similarity exceeds the configured threshold (default 0.6 cosine similarity, tunable), the corresponding `user_id` is treated as recognized.
- The system determines automatically whether this is a check-in or check-out based on the user's most recent `attendance_events` row for the current day (no event yet today → check-in; check-in exists without a matching check-out → check-out).
- A new `attendance_events` row is written with `matched_confidence` and `device_id`. The kiosk UI shows a toast: "Recognized: {Name} — Checked In at {time}" — never a native alert.

**FR-3.2 — Low-Confidence Fallback**
- If the best match similarity is below threshold, the system does **not** silently log an unverified attendance event. Instead it surfaces a "Face not recognized clearly — request Admin approval" toast, and creates a `pending` (unmatched) record an Admin can manually resolve (assign to a staff member or discard) from the Attendance section — this prevents both false attendance and complete blocking of a legitimate but poorly-lit attempt.

**FR-3.3 — Attendance Reporting (Admin)**
- Daily/monthly view per staff member: check-in time, check-out time, computed hours present, late-arrival flag (configurable expected shift-start time per staff or lab-wide default), exportable to CSV.

### 5.4 Patient Management

**FR-4.1 — Add/Edit Patient (Admin and Staff)**
- Both roles have full add/edit capability on this form; Staff's **visibility** in the Patient Overview listing (not their ability to create new patients) is the only place `view_scope` applies (see FR-4.4).
- Field validation: name (required, 2–120 chars), age (1–129), gender (enum), mobile (10-digit Indian format), doctor (dropdown from `doctors` table, "Self" maps to `doctor_id = NULL`), tests (at least one required, multi-select), sample_date (defaults to today, editable to any date not in the future), estimated_report_date (must be ≥ sample_date), total_amount (server-recomputed from selected tests' current prices at save time — never trust a client-submitted total), payment fields per FR-4.3.

**FR-4.2 — Patient ID Generation**
- On patient creation, the backend calls `nextval('patient_seq_' || current_year)` inside the same transaction as the insert. If the year's sequence object does not yet exist (first patient of a new calendar year), it is created on-demand (`CREATE SEQUENCE IF NOT EXISTS ... START 1`) before use. The resulting integer is zero-padded to a minimum of 4 digits and concatenated as `PAT{YY}{padded_seq}` — e.g. sequence value 1 → `PAT260001`; sequence value 1000 → `PAT261000`; sequence value 10000 → `PAT2610000` (padding never truncates, it only sets the *minimum* width). This guarantees uniqueness under concurrent inserts because Postgres sequences are inherently safe against race conditions — this must never be reimplemented as an application-level `SELECT MAX(...) + 1`.

**FR-4.3 — Payment Handling**
- Payment status is derived, not separately stored, from `amount_paid` vs `total_amount`: `amount_paid = 0` → Due; `0 < amount_paid < total_amount` → Partial; `amount_paid = total_amount` → Paid.
- `payment_mode` (`cash`/`qr`) is required only when `amount_paid > 0`; the field is hidden by the frontend (and rejected server-side if submitted) when the entry is being saved as fully Due.
- If `payment_mode = qr`, the frontend requests `POST /api/v1/patients/{id}/qr-code` which returns a UPI deep-link string (`upi://pay?pa={lab_vpa}&pn=Akriti Diagnostics Center&am={amount}&cu=INR&tn={patient_code}`) rendered client-side as a QR image via a JS QR-generation library — no external payment API call is made; this is pure local string construction and rendering.

**FR-4.4 — Returning Patient Lookup & Duplicate Warning**
- As mobile number is typed (debounced), the frontend queries `GET /api/v1/patients/search?mobile={value}` — if a match exists, prior name/age/doctor are offered as an autofill suggestion (not silently applied).
- If a new entry is being saved with the same mobile and a similarity-matched name to a patient created within the prior 24 hours, a non-blocking confirmation modal ("A similar recent entry exists — continue anyway?") is shown before final save.

### 5.5 Test Management

**FR-5.1 — Test CRUD (Admin only)**
- Add/search/edit-price/soft-delete as previously specified. Every price edit writes a `test_price_history` row and an `audit_logs` entry. Historical patient bills reference `patient_tests.price_at_booking`, which is immutable once written — so a later price change never alters a previously issued bill.
- Seed data: the 65 tests listed in Appendix A are inserted by the seed script at first deployment.

### 5.6 Patient Overview

**FR-6.1 — Listing, Search, Filter**
- `GET /api/v1/patients` supports query parameters: `q` (free-text across name/mobile/patient_code), `doctor_id`, `date_from`, `date_to`, `status`, `page`, `page_size` (max 100). Default ordering `created_at DESC`. Response includes `total_count` for pagination UI.
- **View-scope enforcement:** if the requesting user is Staff with `view_scope = own`, the query is transparently constrained to `collected_by = current_user_id` at the query-building layer — this must be enforced in the backend query construction itself, not filtered client-side, so it cannot be bypassed by a modified frontend request.
- Admin requests are never scope-constrained.

### 5.7 Reports & Digital Signature

**FR-7.1 — Report Upload & Signature**
- On report PDF upload/generation, a background task (never inline in the request) applies the lab's stored signature image and letterhead to the final PDF using WeasyPrint template rendering, computes a SHA-256 `verification_hash` of the final PDF content, stores both in the `reports` row, and sets `patients.status = 'report_ready'`.
- A Notification Service event (`report_ready`) is dispatched (Email in this version) to the patient's registered mobile-linked email if available, or the referring context configured by the lab.
- Optionally, a small QR code encoding a verification URL (`https://{domain}/verify/{report_id}?h={short_hash}`) is embedded on the report footer; visiting this URL displays "Verified authentic — issued on {date}" without exposing any patient data, purely as an anti-tampering signal for anyone receiving a physical/forwarded copy.

### 5.8 Revenue Dashboard

**FR-8.1 — Aggregation Endpoints**
- `GET /api/v1/revenue/daily?from&to`, `GET /api/v1/revenue/monthly?year`, `GET /api/v1/revenue/payment-split?from&to` back the three charts specified. These are read-heavy, reporting-style queries and should be considered candidates for a read-replica or materialized-view optimization once data volume grows (documented here as a forward-looking note, not required at initial launch scale).

### 5.9 Expense Management

**FR-9.1 — Expense CRUD (Admin only)**
- Standard CRUD against the `expenses` table per the schema in §4.2. `GET /api/v1/finance/profit-loss?from&to` returns `{ total_revenue, total_expenses, net_profit }` computed by joining `transactions` (derived from `patients.amount_paid`) and `expenses` over the given range — this is the "actual profitability," not just gross billing, that the lab did not have visibility into previously.

### 5.10 Notification Service (Architecture Requirement)

**FR-10.1 — Abstracted Interface**
- All notification-triggering code (OTP issuance, password reset, report-ready, any future event) calls a single internal function signature, e.g. `notification_service.send(event_type: str, user_or_patient_ref, context: dict)`. This function looks up which provider(s) are enabled for that event type from a small provider-registry table/config, and dispatches accordingly.
- **Only the `EmailProvider` class is implemented and enabled in this version.** `WhatsAppProvider` and `SmsProvider` are to be created as empty/stub classes implementing the same interface, disabled by default, so that enabling them later is a configuration change plus filling in the provider's `send()` method — never a refactor of the calling code throughout the system.

### 5.11 Offline Mode & Auto-Sync

**FR-11.1 — Offline Queueing**
- The frontend registers a Service Worker and detects connectivity loss. While offline, the two supported actions — Add Patient (FR-4.1) and Attendance Check-in/out (FR-3.1) — are not blocked: the request payload, together with a client-generated `Idempotency-Key` (UUID v4), is written to an IndexedDB queue instead of being sent over the network. The UI shows a persistent, non-blocking toast/badge: "Offline — N action(s) queued."

**FR-11.2 — Auto-Sync**
- On connectivity restoration (detected via periodic `navigator.onLine` checks plus an actual lightweight ping to `/health`), queued actions are replayed **in original order** against their respective endpoints, each still carrying its original Idempotency-Key.
- Backend behavior for any state-changing endpoint: on receiving a request with an `Idempotency-Key` header, it first checks Redis for that key. If found, the previously computed response is returned as-is (the action is *not* re-executed). If not found, the action executes normally and its result is stored against that key with a 24-hour TTL before responding. This guarantees that a sync retry — whether from a flaky reconnect, a duplicate service-worker replay, or a user closing and reopening the tab mid-sync — can never create a duplicate patient or attendance record.
- On successful sync of each queued item, it is removed from the IndexedDB queue and the toast updates to "Synced" then auto-dismisses.

### 5.12 Login History & Active Sessions

**FR-12.1 — Login History**
- Every row written per FR-1.1–1.3 (all outcomes, not just successes) is visible: to Admin for all users, filterable by user/date/outcome; to each Staff member for their own history only, under their Settings page.

**FR-12.2 — Active Sessions**
- `GET /api/v1/sessions/mine` lists non-revoked `active_sessions` rows for the current user with device label, IP, issued time, last-active time. `POST /api/v1/sessions/{id}/revoke` sets `revoked_at` and the corresponding refresh token is rejected on its next use. Admin has an equivalent endpoint scoped to any user for incident response (e.g. suspected compromised staff device).

### 5.13 Immutable Audit Log

**FR-13.1 — Write-Only Enforcement**
- The PostgreSQL role used by the application connects with a grant of `INSERT` only on `audit_logs` — no `UPDATE` or `DELETE` grant exists for that role at the database level. This is enforced by database permissions, not application logic alone, so that even a fully compromised application server cannot rewrite history through the normal connection.

**FR-13.2 — Hash Chaining**
- Each inserted row computes `record_hash = SHA256(canonical_json(action, entity_type, entity_id, before_value, after_value, occurred_at) || prev_hash)`, where `prev_hash` is the `record_hash` of the row with the immediately preceding `id`. A scheduled integrity-check job periodically recomputes the chain from the beginning (or from the last verified checkpoint) and alerts if any row's stored hash no longer matches its recomputed value — which would indicate the underlying table was tampered with outside the normal insert path (e.g. direct DB manipulation with elevated credentials).
- Admin's Audit Log viewer (`GET /api/v1/audit-logs`) is strictly read-only in the UI — no edit or delete affordance is ever rendered for this data, by design.

---

## 6. External Interface Requirements

### 6.1 User Interface Requirements

#### 6.1.1 Design Philosophy

The System's visual language is **modern, professional, advanced, and premium — expressed through minimalism**, not decoration. This means: generous white space, restrained color usage (two brand colors plus neutral grays, never a rainbow of accent colors), flat surfaces with subtle depth via shadow/elevation rather than heavy borders or gradients, and typography-led hierarchy rather than boxes-within-boxes. The interface must never resemble a generic open-source admin template — every screen should look deliberately designed for a diagnostics brand, not assembled from a component library's defaults.

#### 6.1.2 Color System (Mandatory Brand Palette)

| Token | Hex | Usage |
|---|---|---|
| `--color-cream-vanilla` | `#EFE6DD` | Primary background (light theme) — page background, card background on elevated surfaces uses a slightly lighter/whiter tint derived from this base |
| `--color-cherry-cola` | `#9A0002` | Primary brand/action color — primary buttons, active nav item indicator, key headings/logo accent, focus rings, selected states |
| `--color-cherry-cola-hover` | derived, ~12% darker | Hover/active state of primary buttons |
| `--color-cherry-cola-tint-10` | `#9A0002` at 10% opacity over cream | Subtle backgrounds for selected rows, active nav item background, badge backgrounds |
| `--color-ink` | `#2A2320` (warm near-black, not pure black) | Primary text — pairs naturally with the warm cream background |
| `--color-ink-muted` | `#6B5E56` | Secondary text, placeholder text, table sub-labels |
| `--color-surface` | `#FAF6F1` | Card/panel surface, sits one step lighter than the page background to create depth without a border |
| `--color-border` | `#DCD0C4` | Hairline borders/dividers — warm-neutral, never cool gray (cool gray would clash with the cream base) |
| `--color-success` | `#3F7D58` (muted forest green) | Success toasts/badges (e.g. Report Ready, Paid) |
| `--color-warning` | `#B8792D` (muted amber/ochre) | Warning toasts/badges (e.g. Under Process, Partial) |
| `--color-error` | uses `--color-cherry-cola` directly | Error toasts/badges reuse the brand color itself at full strength — reinforces brand consistency and avoids introducing a second, unrelated red |
| `--color-info` | `#3D6B7D` (muted teal-blue) | Informational toasts, neutral badges (e.g. Sample Collected) |

**Dark theme variant** (same brand identity, inverted for low-light counter use): background `#1E1A17` (warm near-black derived from ink), surface `#2A2420`, text `#EFE6DD` (the cream becomes the text color — a deliberate brand inversion), cherry cola `#C4342F` (brightened ~15% so it retains sufficient contrast against a dark background per WCAG AA), borders `#3D352E`. The two brand colors always remain the anchor of the identity in both themes; only their exact luminance is adjusted for contrast compliance.

**Application rule:** Cherry cola is used **sparingly and intentionally** — primary call-to-action buttons, the active navigation indicator, the logo, key data-point highlights (e.g. an outstanding-due amount), and focus outlines. It is never used as a large background fill (e.g. never a solid cherry-cola header bar covering a large area) — doing so would fight the minimalist goal and reduce its impact as an accent. Cream vanilla is the dominant surface color throughout the light theme.

#### 6.1.3 Typography

- **Font pairing (mandatory):** a display serif — **Fraunces** (Google Fonts, variable, optical-size + weight axes) — used for the brand name/logo lockup, page titles, panel/section titles, KPI figures, and modal titles, paired with **Inter** as the body/UI face used everywhere else (table data, form labels, buttons, badges, toasts, meta text). This pairing gives the product a warm, premium, editorial character in its headings while keeping dense data (tables, forms) rendered in a highly legible, tabular-figure-capable UI font — never use the display face for body copy or vice versa.
- No more than two weights of Inter in regular use (Regular 400, Semibold 600), Fraunces used at Medium/Semibold/Bold (500/600/700) depending on hierarchy.
- Type scale (approximate, adjusted per breakpoint): page title 28–32px (Fraunces), section/panel heading 16–18px (Fraunces), table/body text 14–15px (Inter), secondary/meta text 12–13px (Inter), KPI/monetary figures in dashboard cards 24–28px (Fraunces, tabular numerals).
- Numerals (amounts, Patient IDs, dates) use tabular/monospaced-figure rendering (`font-variant-numeric: tabular-nums`) where the font supports it, so columns of numbers in tables align cleanly.

#### 6.1.4 Component Design Specifications

- **Buttons:** Primary (solid cherry cola fill, cream text, subtle elevation on hover), Secondary (outline in cherry cola or ink-muted border, transparent fill), Destructive (same cherry cola fill as primary but paired with a confirmation modal per §6.1.6 before firing), Ghost/Text (for low-emphasis actions like "Cancel"). Consistent border-radius across all buttons (moderately rounded, not pill-shaped, not sharp-cornered — a defining trait of the premium-minimalist tone).
- **Cards:** Used for dashboard KPI tiles and grouped content — `--color-surface` background, 1px `--color-border` hairline, soft low-opacity shadow (never a hard drop shadow), consistent internal padding.
- **Tables:** Sticky header row, zebra-striping using a near-imperceptible tint (1–2% darker row, not a strong alternating pattern), row-hover uses `--color-cherry-cola-tint-10`, status values always rendered as a **badge** (colored background pill + SVG icon + text label — see §5.6/badge rule already established), never plain colored text alone.
- **Forms:** Floating or top-aligned labels (not placeholder-only labels, which disappear and hurt usability for less tech-fluent staff), clear focus state using a cherry-cola focus ring, inline validation messages appear directly under the field in `--color-error`, never as a separate summary block the user has to scroll to find.
- **Badges:** Pill-shaped, colored background at ~15% opacity of the semantic color with full-opacity text/icon of that same color — Sample Collected (info/teal), Under Process (warning/ochre), Report Ready (success/green), Due (cherry cola full-strength), Partial (warning/ochre).
- **Toasts and Modals:** As specified in the base UI/UX requirements already defined in this document — toast/modal color-coding uses the same semantic tokens above; the modal's destructive-confirm button uses the cherry-cola solid button style.
- **Navigation sidebar:** Cream vanilla or surface-toned background, active item shown via a left accent bar in cherry cola plus a subtle tinted background (`--color-cherry-cola-tint-10`) — not a solid cherry-cola block, keeping with the minimalism rule above.

#### 6.1.5 Skeleton Loading (Mandatory Real-Time Loading States)

No screen may show a blank white page, a spinner-only overlay, or a layout-shifting "pop-in" of content while data loads. Every data-driven view implements **skeleton screens** that mirror the exact shape of the content about to appear, so the layout is stable the instant real data arrives (no cumulative layout shift).

- **Dashboard KPI cards:** each card renders its container, icon placeholder, and label immediately; only the numeric value area shows an animated shimmer block (a soft left-to-right gradient sweep in a muted tone derived from `--color-border`) until the figure resolves.
- **Tables (Patient Overview, Manage Staff, Attendance Report, Login History, Audit Log, etc.):** render the full header row immediately (columns are known statically), then 6–10 skeleton rows with shimmer blocks sized to each column's typical content width (a shorter block for a badge column, a longer block for a name column) — replaced row-by-row as real data streams in if paginated, or all at once when the page response completes.
- **Charts (Revenue, Expense, Attendance Summary, Analytics):** the chart's axes/frame and legend render immediately; the plotted area shows a low-opacity shimmer placeholder shaped like a generic bar/line pattern until real data points are ready.
- **Forms that pre-fill data (Edit Patient, Edit Staff, Edit Test):** each field renders its label immediately with a shimmer block in place of the input's value until the record loads, then swaps to the real editable input.
- **Attendance kiosk / face-recognition screen:** the camera frame container and instruction text render immediately; a subtle pulsing ring around the face-detection guide indicates "scanning," distinct from the shimmer pattern used for data skeletons — this is a live-processing indicator rather than a loading placeholder, and must never be a native browser spinner.
- **Report list / Report Version history / Patient Timeline:** timeline-shaped skeleton (a vertical connector line with 3–4 placeholder event blocks) rather than a generic rectangle, since the real content is inherently a vertical sequence.
- Skeleton shimmer implementation: pure CSS keyframe animation (background-position sweep over a gradient), no external animation library required — keeps the frontend dependency-free per the vanilla-JS constraint already established.
- Minimum/maximum display duration: skeletons must not flash for less than ~150ms (which reads as a flicker) — a short artificial minimum display time is acceptable for very fast responses so the loading state doesn't feel glitchy, and must never persist beyond the actual data-fetch time (no artificial delays beyond what a slow network/query genuinely takes).

#### 6.1.6 Iconography and Native-Dialog Prohibition (carried forward, restated for completeness)

- All icons SVG, one consistent set, theme-aware via `currentColor` so icons automatically adopt cherry cola or cream/ink tones correctly in both themes without separate icon assets per theme.
- No native browser `alert()`, `confirm()`, or `prompt()` calls anywhere in the codebase — verified as a code-review/lint rule, not just a design guideline.
- No emoji characters in any UI string, generated PDF, or log message.
- Toast component: color-coded per §6.1.2 semantic tokens, matching SVG icon, auto-dismiss ~3–4s, stacking, top-right (desktop) / top-center (mobile).
- Modal component: center-screen, backdrop blur, focus-trapped, Esc-to-close, cherry-cola solid confirm button for destructive actions.
- Responsive breakpoints: <640px (phone, card-based list views), 640–1024px (tablet, primary staff-use size, 2-column forms), >1024px (desktop, full multi-column dashboard with persistent sidebar).

### 6.2 Hardware Interfaces

- Standard USB or integrated webcam, accessed via the browser's `getUserMedia` API — no proprietary SDK or dedicated biometric hardware required for initial launch.

### 6.3 Software Interfaces

- SMTP: Gmail relay via App Password, invoked through `fastapi-mail`.
- No external payment gateway API (explicitly excluded per §1.3).

### 6.4 Communication Interfaces

- All client-server communication over HTTPS/REST, JSON request/response bodies, versioned under `/api/v1/`.

---

## 7. Non-Functional Requirements

| ID | Requirement | Acceptance Criteria |
|---|---|---|
| NFR-1 | Throughput | System supports ≥50 patient registrations/day sustained, with headroom to ≥500,000 total historical patient rows without query-time degradation beyond 500ms for standard listing queries (with pagination and indexes per §4.4) |
| NFR-2 | Attendance recognition latency | End-to-end face match (frame capture → recognized result shown) completes in under 2 seconds under normal lighting on standard hardware |
| NFR-3 | Availability | `/health` endpoint responds within 200ms; external uptime monitoring alerts within 5 minutes of downtime |
| NFR-4 | Security | Passwords hashed with bcrypt/argon2; all state-changing endpoints require a valid Idempotency-Key; audit log insert-only at the DB role level (FR-13.1) |
| NFR-5 | Data durability | Automated encrypted daily backups retained off-server; restore procedure documented and tested at least once before go-live |
| NFR-6 | Offline tolerance | Add Patient and Attendance actions remain fully functional with zero network connectivity, syncing without data loss or duplication upon reconnection |
| NFR-7 | Maintainability | All schema changes applied via Alembic migrations only; API surface versioned (`/api/v1/`) so future breaking changes do not require simultaneous frontend/backend redeployment |
| NFR-8 | Usability | Staff can complete an Add Patient entry, from opening the form to confirmation toast, in under 60 seconds for a typical 2–3 test booking, via keyboard-first tab flow |

---

## 8. API Endpoint Reference (Representative — not exhaustive)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/auth/login` | Email + password login |
| POST | `/api/v1/auth/otp/request` | Request login/reset OTP |
| POST | `/api/v1/auth/otp/verify` | Verify OTP, issue session or reset token |
| POST | `/api/v1/auth/password/reset` | Set new password (first-login or forgot-password flow) |
| POST | `/api/v1/auth/refresh` | Rotate access token using refresh cookie |
| POST | `/api/v1/staff` | Create staff (Admin only) |
| POST | `/api/v1/staff/{id}/face-enroll` | Submit a face-capture sample |
| GET | `/api/v1/staff` | List staff (Admin only) |
| PATCH | `/api/v1/staff/{id}` | Edit staff / view_scope / deactivate |
| POST | `/api/v1/attendance/recognize` | Submit a captured frame for recognition + logging |
| GET | `/api/v1/attendance/report` | Attendance report (Admin) |
| POST | `/api/v1/patients` | Create patient (idempotency-key required) |
| PATCH | `/api/v1/patients/{id}` | Edit patient |
| GET | `/api/v1/patients` | List/search/filter patients (view-scope enforced) |
| GET | `/api/v1/patients/search` | Returning-patient lookup by mobile |
| POST | `/api/v1/patients/{id}/qr-code` | Generate local UPI QR payload |
| POST | `/api/v1/tests` | Add test (Admin only) |
| PATCH | `/api/v1/tests/{id}` | Edit price (Admin only, logs history) |
| POST | `/api/v1/reports/{patient_id}` | Upload/generate signed report |
| GET | `/api/v1/revenue/daily` | Daily revenue series |
| GET | `/api/v1/revenue/monthly` | Monthly revenue series |
| POST | `/api/v1/finance/expenses` | Log an expense (Admin only) |
| GET | `/api/v1/finance/profit-loss` | Net profit/loss report |
| GET | `/api/v1/sessions/mine` | List own active sessions |
| POST | `/api/v1/sessions/{id}/revoke` | Revoke a session |
| GET | `/api/v1/login-history` | Login history (scoped by role) |
| GET | `/api/v1/audit-logs` | Read-only audit log viewer (Admin only) |

All mutating endpoints (`POST`/`PATCH`/`DELETE`) require an `Idempotency-Key` request header.

---

## 9. Error Handling & Status Code Conventions

| Scenario | HTTP Status | Notes |
|---|---|---|
| Validation failure (bad input) | 422 | Pydantic-generated field-level detail |
| Auth failure (bad credentials/OTP) | 401 | Generic message, no user-enumeration hints |
| Authorization failure (role/scope) | 403 | e.g. Staff attempting an Admin-only action |
| Not found | 404 | e.g. patient_id doesn't exist |
| Conflict (duplicate unique field) | 409 | e.g. email already registered |
| Idempotent replay | 200 | Original response returned verbatim, no duplicate side-effect |
| Rate-limited | 429 | Includes `Retry-After` header |
| Unexpected server error | 500 | Logged with full context to the error-tracking service; user sees a generic toast, never a raw stack trace |

---

## 10. Acceptance Testing Guidance

Before go-live, the following must be explicitly verified, not just assumed from code review:
1. Two staff members saving a new patient within the same second produce two distinct, correctly sequential Patient IDs (concurrency test).
2. Submitting the same Add Patient request twice with the same Idempotency-Key produces exactly one patient record.
3. A staff account cannot log in (remains `is_active = false`) until face enrollment completes.
4. Disconnecting network mid-session, performing an Add Patient and an Attendance check-in, then reconnecting, results in both actions appearing exactly once server-side.
5. Attempting to modify or delete a row directly in `audit_logs` via the application's DB role fails at the database permission level.
6. A Staff account with `view_scope = own` cannot retrieve another staff member's patients even via a manually crafted API request with modified query parameters.

---

## Appendix A — Test Master List (65 tests, pre-loaded via seed script)

CBC 5 Part — ₹230, TC DC OF WBC — ₹60, HB% — ₹65, Blood Sugar(F) — ₹50, Blood Sugar(R) — ₹50, Blood Sugar Fasting/PP — ₹100, Blood Urea — ₹200, Urine Culture — ₹350, HIV 1&2 Test — ₹200, TB Platinum Test — ₹200, Para Check of P.F — ₹200, Lipid Profile — ₹400, Para Check for (PV & PF) — ₹250, Para Screen for P.F — ₹150, Serum Electrolytes (Na,K,Cl) — ₹400, Trust Test — ₹60, VDRL — ₹60, Vitamin D — ₹750, Vitamin B12 — ₹750, Total Protein A/G Ratio — ₹200, Dengue (IgE/IgM) — ₹500, Testosterone Total — ₹500, R/E of Urine — ₹100, Stool R/E — ₹150, Micral Test Albumin Urine — ₹250, Aldehyde — ₹150, Serum Calcium — ₹180, T3,T4,TSH — ₹450, Thyroid Profile (FT3,FT4,TSH) — ₹650, PSA — ₹450, HbA1c — ₹250, Preg Colour — ₹50, Parahit Total — ₹230, Triglyceride — ₹200, Cholesterol — ₹200, Montox Test 5TU/10TU — ₹150, IgE — ₹450, HBsAg — ₹200, HCV — ₹220, Blood Group and Rh Typing — ₹100, R.A. Test — ₹250, Hypertension Profile — ₹850, Arthritis Profile — ₹750, Serum Bilirubin — ₹200, SGPT — ₹100, SGOT — ₹100, LFT — ₹500, KFT — ₹500, Serum Creatinine — ₹200, Serum Uric Acid — ₹200, Diabetic Profile — ₹850, Kidney Profile — ₹850, ASO Titer — ₹250, CRP (Quantitative Test) — ₹300, Widal — ₹180, PBS for MP — ₹100, RK 39 — ₹650, PT/INR — ₹230, USG Whole Abdomen — ₹650, USG Upper Abdomen — ₹550, USG Lower Abdomen — ₹550, USG Uterus and Adnexa — ₹550, USG Fetal Profile — ₹550, ECG — ₹250, Anemia Profile (HB%, CBC, Iron, TIBC, Ferritin) — ₹1000.

## Appendix B — Environment Variables Reference

`DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, `JWT_ACCESS_EXPIRE_MINUTES`, `JWT_REFRESH_EXPIRE_DAYS`, `MAIL_USERNAME`, `MAIL_PASSWORD` (Gmail App Password), `MAIL_FROM_NAME` ("Akriti Diagnostics Center"), `LAB_UPI_VPA`, `FACE_MATCH_THRESHOLD` (default 0.6), `ADMIN_SEED_EMAIL`, `ADMIN_SEED_TEMP_PASSWORD`.

## Appendix C — Glossary

See §1.4.
