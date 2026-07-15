import re
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, time
from backend.app.models.user import User, RoleEnum
from backend.app.models.doctor import Doctor
from backend.app.models.patient import Patient
from backend.app.models.report import Report
from backend.app.models.test import Test

def build_copilot_context(message: str, current_user: User, db: Session) -> str:
    """
    Analyzes the user message and dynamically builds a real-time context
    by querying the database based on detected keywords and RBAC.
    """
    system_prompt = f"""You are PathLab AI, a highly advanced Laboratory Management Assistant for Akriti Diagnostics Center.
The current user is {current_user.name}, Role: {current_user.role}.
You must be helpful, professional, and concise. Format your responses in Markdown.

CRITICAL RULES:
1. You are currently in a READ-ONLY mode. If any user (Staff or Admin) asks you to edit, modify, delete, or update patient records, test prices, or any other data, YOU MUST POLITELY REFUSE and tell them that you currently do not have modification access and they must do it manually via the dashboard.
2. Always base your answers on the EXACT LIVE DATA provided below. Do not hallucinate or make up ANY data.
3. If a user asks to see a patient's report, provide the exact clickable markdown link provided in the context below so they can view/download the PDF.
"""

    msg_lower = message.lower()
    injected_data = []

    # 1. PATIENT MODULE
    patient_ids = re.findall(r'PAT\d{6}', message.upper())
    if patient_ids:
        for pid in patient_ids:
            if current_user.role == RoleEnum.staff:
                patient = db.query(Patient).filter(Patient.patient_code == pid, Patient.collected_by == current_user.id).first()
            else:
                patient = db.query(Patient).filter(Patient.patient_code == pid).first()
                
            if patient:
                # Get report info
                reports = db.query(Report).filter(Report.patient_id == patient.id).all()
                report_details = []
                for r in reports:
                    uploaded_by = db.query(User).filter(User.id == r.uploaded_by).first()
                    uploader_name = uploaded_by.name if uploaded_by else "Unknown"
                    report_link = f"[View PDF](/api/v1/reports/download/{r.id})"
                    report_details.append(f"Report ID {r.id}: Uploaded by {uploader_name} on {r.created_at.strftime('%Y-%m-%d %H:%M')}. Link: {report_link}")
                
                reports_str = " | ".join(report_details) if report_details else "No reports uploaded."
                
                injected_data.append(
                    f"[Patient {pid}]: Name: {patient.name}, Status: {patient.status.name}, "
                    f"Amount Paid: Rs {patient.amount_paid}, Total Amount: Rs {patient.total_amount}. "
                    f"Reports: {reports_str}"
                )
            else:
                injected_data.append(f"[Patient {pid}]: Not found or access denied.")

    elif any(k in msg_lower for k in ["patient", "patients", "record"]):
        # General patient query
        if current_user.role == RoleEnum.staff:
            count = db.query(Patient).filter(Patient.collected_by == current_user.id).count()
            injected_data.append(f"[Patients Summary]: You have registered {count} patients.")
        else:
            count = db.query(Patient).count()
            injected_data.append(f"[Patients Summary]: There are {count} total patients in the system.")

    # 2. TEST CATALOG MODULE
    if any(k in msg_lower for k in ["test", "tests", "catalog", "price"]):
        active_tests = db.query(Test).filter(Test.is_active == True).all()
        test_summary = ", ".join([f"{t.name} (Code: {t.test_code}, Rs {t.price})" for t in active_tests[:10]])
        test_count = len(active_tests)
        injected_data.append(f"[Test Catalog]: {test_count} active tests available. Sample: {test_summary}")

    # 3. ADMIN ONLY: STAFF, DOCTORS, REVENUE
    if current_user.role == RoleEnum.admin:
        if any(k in msg_lower for k in ["staff", "employee", "team", "who"]):
            staff_records = db.query(User).filter(User.role == RoleEnum.staff).all()
            staff_names = ", ".join([f"{s.name} (Code: {s.staff_code})" for s in staff_records]) if staff_records else "None"
            injected_data.append(f"[Staff Info]: Total Staff: {len(staff_records)}. Names: {staff_names}.")
            
        if any(k in msg_lower for k in ["doctor", "radiologist", "pathologist", "who"]):
            doc_records = db.query(Doctor).all()
            doc_names = ", ".join([f"Dr. {d.name}" for d in doc_records]) if doc_records else "None"
            injected_data.append(f"[Doctor Info]: Total Doctors: {len(doc_records)}. Names: {doc_names}.")
            
        if any(k in msg_lower for k in ["revenue", "earning", "collection", "money", "today", "month", "total"]):
            today_start = datetime.combine(datetime.now().date(), time.min)
            today_rev = db.query(func.sum(Patient.amount_paid)).filter(Patient.created_at >= today_start).scalar() or 0
            total_rev = db.query(func.sum(Patient.amount_paid)).scalar() or 0
            injected_data.append(f"[Revenue Info]: Today's Revenue: Rs {today_rev}. Total Revenue: Rs {total_rev}.")

    if injected_data:
        system_prompt += "\n\nCRITICAL LIVE DATA (Use this to answer the user's query):\n"
        system_prompt += "\n".join(injected_data)
        
    return system_prompt
