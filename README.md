<div align="center">
  <img src="https://img.shields.io/badge/Akriti-Diagnostics%20Center-9A0002?style=for-the-badge&logo=healthcare" alt="Akriti Pathology Lab" />
  <h1>🧪 Akriti Pathology Lab Management System</h1>
  <p><strong>A Next-Generation, AI-Powered, Highly Secure Laboratory Information System (LIS)</strong></p>

  [![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-336791?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
  [![License](https://img.shields.io/badge/License-Proprietary-red.svg?style=flat-square)](#)

  <br />
</div>

## 📖 Overview

The **Akriti Pathology Lab Management System** is a premium, secure, and modern platform custom-engineered for **Akriti Diagnostics Center**. It unifies a robust **FastAPI (Python)** backend with a responsive, high-performance **Vanilla JS/HTML5** frontend. 

Built for speed, offline-resilience, and maximum security, this system streamlines everything from patient registration and dynamic UPI payments, to AI-assisted diagnostics, WhatsApp report deliveries, and biometric staff attendance.

---

## 🌟 Key Features

### 🤖 AI Copilot (Powered by Google Gemma 4 31B)
*   **Context-Aware Chatbot:** Intelligent AI assistant powered by the blazing-fast Gemma 4 31B model for answering queries, fetching live patient statistics, and resolving operational roadblocks.
*   **Strict Anti-Hallucination Engine:** Hardened safeguards ensure the AI never invents fake patient names, financial data, or diagnostics. It responds with "Insufficient info" if exact data is absent.
*   **Smart Rate Limiting:** Enforced dynamic streaming rate limits to protect API quotas (Admin: 7 msgs/min, Staff: 3 msgs/min).

### 🏥 Reception & Patient Management
*   **Rapid Registration & Smart Billing:** Lightning-fast intake forms generating calendar-year based tracking codes (e.g., `PAT260001`). Totals are strictly computed server-side to prevent tampering.
*   **Offline-First Architecture:** Seamless queueing of registration and payments locally when internet connectivity drops. Auto-syncs to the remote server immediately once the connection is restored.
*   **Zero-Fee UPI Integration:** Instantly generates dynamic UPI payment QR codes tailored to patient totals using direct VPA—bypassing costly payment gateway commissions.

### 🔬 Lab Operations & Smart Reporting
*   **Master Test Catalog:** Pre-seeded with over 65 standard diagnostic tests.
*   **Dual-Path Report Release:**
    1.  **Structured Result Entry:** Enter parameters (e.g., Hemoglobin, WBC) to auto-render beautiful, branded PDF reports.
    2.  **Manual PDF Upload:** Drag-and-drop custom or scanned laboratory PDFs securely to Supabase/Local storage.
*   **Report Security & Verification:** Every generated PDF carries an immutable SHA-256 hash validation mechanism.

### 💬 Real-Time WhatsApp Alerts
Integrated with **WASender API** (equipped with Cloudflare bypass) for automated communication:
*   **Welcome Alerts:** Sends a greeting with the unique Patient ID immediately upon registration.
*   **Status Tracking:** Proactive mobile notifications whenever a sample's status progresses.
*   **Direct Report Delivery:** Delivers finalized PDF reports straight to the patient’s WhatsApp via secure, temporary download URLs.

### 👤 Biometric Attendance Kiosk
*   **Face Recognition Check-in:** Real-time Check-In/Check-Out station for lab staff.
*   **Anti-Spoof Liveness Gating:** Validates pose and image quality prior to accepting attendance data.
*   **High-Speed Vector Storage:** Utilizes PostgreSQL's `pgvector` for instantaneous facial recognition matching across the staff database.

---

## 🔒 Enterprise-Grade Security

Security is deeply woven into the fabric of the Akriti PathLab System.

*   **Military-Grade Password Hashing:** Powered by **Argon2id** combined with a robust HMAC-SHA256 **Password Pepper**.
*   **Multi-Device Session Revocation:** Active Session Tracking prevents concurrent logins by terminating older access tokens automatically when a new device logs in.
*   **IDOR Prevention:** Strict `check_patient_access` checks ensure staff can only view and manage patients they have registered, preventing lateral data breaches.
*   **DDoS & Brute-Force Protection:** Intelligent in-memory token-bucket and `slowapi` rate limits (e.g., 5 attempts/min on login endpoints) guard against automated attacks.
*   **Secure Deployment Scripts:** Bundled with a specialized `generate_secrets.py` CLI tool to automatically provision cryptographically secure JWT keys and Peppers for production servers.

---

## 🛠️ Technical Stack

*   **Backend:** FastAPI (Python 3.10+), SQLAlchemy (Core/ORM), Uvicorn, Gunicorn
*   **Database:** PostgreSQL (with `pgvector` & `pg_trgm` extensions), Redis (Caching & Idempotency)
*   **Frontend:** Vanilla HTML5, CSS3, ES6+ Javascript (No heavy virtual DOM frameworks for maximum speed)
*   **Design System:** Tokenized Cream Vanilla (`#EFE6DD`) & Cherry Cola (`#9A0002`) palette, Outfit/Inter Typography, custom Skeleton loaders.
*   **Integrations:** WASender API (WhatsApp), Brevo (Transactional Mail), Google GenAI SDK (Copilot).

---

## 🚀 Installation & Local Setup

### 1. Prerequisites
*   Python 3.10+
*   PostgreSQL 14+ (with the `pgvector` extension installed)
*   Redis Server (Optional; built-in fallback enabled)

### 2. Standard Installation

```bash
# 1. Clone the Repository
git clone https://github.com/Kunal9608/Akriti.git
cd Akriti

# 2. Setup Virtual Environment
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

# 3. Install Dependencies
pip install -r requirements.txt

# 4. Configure Environment
cp .env.example .env
# Important: Fill in DB credentials, Supabase keys, and WhatsApp tokens.

# 5. Generate Secure Secrets
python backend/scripts/generate_secrets.py
# Copy the output keys into your .env file

# 6. Run the Server
python main.py
```

### 3. 🐋 Docker Deployment (Recommended)

Run the entire application stack (FastAPI, Postgres, Redis) with a single command:

```bash
docker compose up --build -d
```
* **Web App:** [http://localhost:8000](http://localhost:8000)
* **Swagger API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📜 License
This software is strictly **proprietary** and custom-built for **Akriti Diagnostics Center**. Unauthorized distribution, reproduction, deployment, or reverse engineering is explicitly prohibited.
