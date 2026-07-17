# 🧪 Akriti Pathology Lab Management System

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](#)

A premium, secure, and modern **Pathology Laboratory Management System** custom-designed for **Akriti Diagnostics Center**. This repository packages a robust **FastAPI (Python)** backend and a responsive **Vanilla HTML5/CSS3/ES6+ JavaScript** frontend, running as a unified application for streamlined setup and local or containerized operation.

---

## 🌟 Key Modules & Features

### 1. Reception & Patient Management
*   **Registration & Billing:** Fast intake forms generating calendar-year patient codes (e.g., `PAT260001`).
*   **Smart Pricing & Billing:** Client totals are recomputed server-side from pre-seeded test lists to prevent invoice tampering.
*   **Offline Mode:** Seamless queueing of patient registration and payments locally when internet connectivity drops. Auto-syncs to the server once connection is restored.
*   **Local UPI QR Payments:** Instantly generates dynamic UPI payment links via VPA (Virtual Payment Address) tailored to patient totals without costly API gateways.

### 2. Lab Operations & Report Generation
*   **Test Catalog Master:** Pre-seeded with 65 standard diagnostic tests.
*   **Sample Tracking Workflow:** Clear progress tracking (`sample_collected` -> `sent_to_franchise` -> `under_process` -> `partial_release` -> `report_ready`).
*   **Dual-Path Report Release:**
    1.  **Structured Result Entry:** Enter parameters (e.g., Hemoglobin, WBC) to auto-render standard reports.
    2.  **Manual PDF Upload:** Drag-and-drop custom formatted or scanned laboratory PDF reports.
*   **Report Security & Versioning:** PDF modification logs, SHA-256 hash validation, and support for partial releases.

### 3. Real-Time WhatsApp Alerts (WASenderAPI Integration)
Provides instant notifications to patients via the **WASender API** (with bypass configurations for Cloudflare protection):
*   **Registration Alerts:** Instant message with patient name and unique Patient ID immediately upon staff registration.
*   **Status Updates:** Automatic notifications sent to patient's mobile number when report status changes.
*   **Report Releases:** Delivers the finalized report directly to the patient's WhatsApp using a secure, temporary document download URL.

### 4. Biometric Attendance Kiosk
*   **Face Recognition Kiosk:** Real-time Check-In / Check-Out station for lab staff.
*   **Liveness Gating:** Gated registration validating pose and image quality prior to activating staff accounts.
*   **Vector Storage:** Efficient biometric verification leveraging PostgreSQL's `pgvector` extension.

---

## 🛠️ Technical Stack

*   **Backend:** FastAPI (Python 3.10+), SQLAlchemy (Core/ORM), Uvicorn, Gunicorn
*   **Database:** PostgreSQL (with `pgvector` extension), Redis (caching and idempotency key replays)
*   **Frontend:** Vanilla HTML5, CSS3, ES6+ Javascript (no heavy frameworks)
*   **Design System:** Tokenized Cream Vanilla (`#EFE6DD`) & Cherry Cola (`#9A0002`) palette, Outfit/Inter Typography, custom Skeleton loaders.
*   **Notifications:** WASender API (WhatsApp Client), Brevo Transactional Mailer

---

## 📂 Directory Structure

```text
├── backend/
│   ├── alembic/                # DB migrations
│   ├── app/
│   │   ├── core/               # Security, Database config, and Redis connections
│   │   ├── models/             # SQLAlchemy schemas & relationships
│   │   ├── repositories/       # Database access layers (Repo pattern)
│   │   ├── routers/            # FastAPI endpoint controllers
│   │   ├── schemas/            # Pydantic schemas (validations)
│   │   ├── services/           # Core business logic (WhatsApp, PDFs, Auth)
│   │   ├── config.py           # Configuration loader
│   │   └── main.py             # FastAPI App instance & CORS configuration
│   └── seed/                   # Database seeding scripts
├── frontend/
│   ├── admin/                  # Administrative screens (Dashboard, Expenses, Audit)
│   ├── staff/                  # Staff actions (Register Patient, Result Entry)
│   ├── assets/
│   │   ├── css/                # Tokenized CSS files
│   │   ├── js/                 # Vanilla JS controllers
│   │   └── images/             # Visual assets
│   ├── index.html              # Login & Landing page
│   └── attendance-kiosk.html   # Face Recognition Kiosk screen
├── docker-compose.yml          # Container configuration
├── main.py                     # Single Root Entry Point
├── requirements.txt            # Python dependencies
└── .env.example                # Template for environment configuration
```

---

## 🚀 Installation & Local Setup

### 1. Prerequisites
*   Python 3.10+
*   PostgreSQL 14+ (optionally with the `pgvector` extension)
*   Redis Server (optional; in-memory fallback enabled if offline)
*   System dependencies for WeasyPrint (Pango, Cairo, GDK-PixBuf)

### 2. Standard Installation Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Kunal9608/Akriti.git
    cd Akriti
    ```

2.  **Create and Activate a Virtual Environment:**
    ```bash
    python -m venv .venv
    # Windows:
    .venv\Scripts\activate
    # macOS/Linux:
    source .venv/bin/activate
    ```

3.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Environment Variables:**
    Copy `.env.example` to `.env` and fill in the required keys:
    ```bash
    cp .env.example .env
    ```
    *Make sure to configure the keys for both `SUPABASE_KEY` (use service_role key starting with `eyJ...`) and `WASENDER_API_KEY` for WhatsApp.*

5.  **Run the Server:**
    ```bash
    python main.py
    ```

---

## 🐋 Running with Docker (Recommended)

Run the application stack (FastAPI web server, PostgreSQL database with `pgvector`, and Redis) with a single command:

```bash
docker compose up --build -d
```
* **Main Web App / Kiosk:** [http://localhost:8000](http://localhost:8000)
* **Swagger API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📜 License
This project is proprietary and custom-built for **Akriti Diagnostics Center**. Unauthorized duplication, distribution, or reverse engineering is prohibited.
