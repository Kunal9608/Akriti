"""
Notification service — abstracted provider interface.
Only EmailProvider is implemented. WhatsApp/SMS are stubs.
"""
import logging
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

EMAIL_NOTIFICATIONS_ENABLED = True


class NotificationProvider(ABC):
    @abstractmethod
    def send(self, event_type: str, recipient_email: str, context: Dict[str, Any]) -> bool:
        pass


class EmailProvider(NotificationProvider):
    def send(self, event_type: str, recipient_email: str, context: Dict[str, Any]) -> bool:
        try:
            from backend.app.config import settings
            if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
                print("  [MAIL WARNING] Email not configured — settings.MAIL_USERNAME or settings.MAIL_PASSWORD is empty")
                logger.warning("Email not configured — skipping notification")
                return False

            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders

            subject_map = {
                "otp": f"Your OTP for Akriti Diagnostics — {context.get('otp', '')}",
                "password_reset": "Reset your Akriti Lab password",
                "report_ready": f"Your lab report is ready — {context.get('patient_name', '')}",
                "welcome_staff": f"Welcome to Akriti Diagnostics Center — {context.get('name', '')}",
            }
            body_map = {
                "otp": f"""
                <div style="font-family:'Manrope', -apple-system, sans-serif; max-width: 480px; margin: 20px auto; border: 1px solid #E7E7E3; border-radius: 12px; overflow: hidden; background-color: #FFFFFF; box-shadow: 0 4px 12px rgba(22,32,28,0.04);">
                  <div style="background-color: #0E5C4E; padding: 24px; text-align: center;">
                    <h2 style="color: #FFFFFF; margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.5px;">Akriti Diagnostics Center</h2>
                  </div>
                  <div style="padding: 32px; color: #16201C; line-height: 1.6;">
                    <p style="margin-top: 0; font-size: 15px; font-weight: 500;">Hello,</p>
                    <p style="font-size: 14px; color: #7A8880;">Use the following One-Time Password (OTP) to securely log in to your account. This code is valid for 5 minutes.</p>
                    <div style="font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #0E5C4E; padding: 18px; background-color: #E4EEEB; border-radius: 8px; text-align: center; margin: 24px 0; border: 1px solid #C4DFD8;">{context.get('otp','')}</div>
                    <p style="color: #A7B2AC; font-size: 12px; margin-bottom: 0; text-align: center;">If you did not request this login code, you can safely ignore this email.</p>
                  </div>
                </div>
                """,
                "password_reset": f"""
                <div style="font-family:'Manrope', -apple-system, sans-serif; max-width: 480px; margin: 20px auto; border: 1px solid #E7E7E3; border-radius: 12px; overflow: hidden; background-color: #FFFFFF; box-shadow: 0 4px 12px rgba(22,32,28,0.04);">
                  <div style="background-color: #0E5C4E; padding: 24px; text-align: center;">
                    <h2 style="color: #FFFFFF; margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.5px;">Akriti Diagnostics Center</h2>
                  </div>
                  <div style="padding: 32px; color: #16201C; line-height: 1.6;">
                    <p style="margin-top: 0; font-size: 15px; font-weight: 500;">Password Reset Request,</p>
                    <p style="font-size: 14px; color: #7A8880;">Use the following One-Time Password (OTP) to complete your password reset. This code is valid for 5 minutes.</p>
                    <div style="font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #0E5C4E; padding: 18px; background-color: #E4EEEB; border-radius: 8px; text-align: center; margin: 24px 0; border: 1px solid #C4DFD8;">{context.get('otp','')}</div>
                    <p style="color: #A7B2AC; font-size: 12px; margin-bottom: 0; text-align: center;">If you did not request a password reset, please contact system support immediately.</p>
                  </div>
                </div>
                """,
                "report_ready": f"""
                <div style="font-family:'Manrope', -apple-system, sans-serif; max-width: 480px; margin: 20px auto; border: 1px solid #E7E7E3; border-radius: 12px; overflow: hidden; background-color: #FFFFFF; box-shadow: 0 4px 12px rgba(22,32,28,0.04);">
                  <div style="background-color: #0E5C4E; padding: 24px; text-align: center;">
                    <h2 style="color: #FFFFFF; margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.5px;">Akriti Diagnostics Center</h2>
                  </div>
                  <div style="padding: 32px; color: #16201C; line-height: 1.6;">
                    <p style="margin-top: 0; font-size: 15px; font-weight: 600;">Dear {context.get('patient_name','Patient')},</p>
                    <p style="font-size: 14px; color: #7A8880;">Your diagnostic lab reports are ready and have been generated successfully.</p>
                    <div style="background-color: #FAFAF8; padding: 18px; border-radius: 8px; margin: 24px 0; border: 1px solid #E7E7E3;">
                      <div style="font-size: 13px; margin-bottom: 6px;"><strong style="color: #7A8880;">Patient ID:</strong> <span style="font-family: monospace; font-weight: 600;">{context.get('patient_code','')}</span></div>
                      <div style="font-size: 13px;"><strong style="color: #7A8880;">Status:</strong> <span style="color: #2F8F5B; font-weight: 600;">REPORT READY</span></div>
                    </div>
                    <p style="font-size: 13px; color: #7A8880; margin-bottom: 0;">Your report is attached to this email as a PDF. You may also collect a hard copy from our lab reception.</p>
                  </div>
                </div>
                """,
                "welcome_staff": f"""
                <div style="font-family:'Manrope', -apple-system, sans-serif; max-width: 480px; margin: 20px auto; border: 1px solid #E7E7E3; border-radius: 12px; overflow: hidden; background-color: #FFFFFF; box-shadow: 0 4px 12px rgba(22,32,28,0.04);">
                  <div style="background-color: #0E5C4E; padding: 24px; text-align: center;">
                    <h2 style="color: #FFFFFF; margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.5px;">Welcome to Akriti Diagnostics</h2>
                  </div>
                  <div style="padding: 32px; color: #16201C; line-height: 1.6;">
                    <p style="margin-top: 0; font-size: 15px; font-weight: 600;">Dear {context.get('name','')},</p>
                    <p style="font-size: 14px; color: #7A8880;">Your staff profile has been registered successfully. Use the temporary password below to log in and configure your account:</p>
                    <div style="font-size: 24px; font-weight: 800; color: #0E5C4E; padding: 18px; background-color: #E4EEEB; border-radius: 8px; text-align: center; margin: 24px 0; border: 1px solid #C4DFD8; font-variant-numeric: tabular-nums;">{context.get('temp_password','')}</div>
                    <p style="font-size: 13px; color: #7A8880;">You will be prompted to choose a new secure password on your first login.</p>
                    <hr style="border: 0; border-top: 1px solid #E7E7E3; margin: 24px 0;">
                    <p style="color: #A7B2AC; font-size: 12px; margin-bottom: 0; text-align: center;">Akriti Diagnostics Center · Administration portal</p>
                  </div>
                </div>
                """,
            }

            # Use 'mixed' for emails that carry attachments, 'alternative' otherwise
            attachment_bytes = context.get("attachment_bytes")
            attachment_name  = context.get("attachment_name")

            if attachment_bytes and attachment_name:
                msg = MIMEMultipart("mixed")
                html_part = MIMEMultipart("alternative")
                html_body = body_map.get(event_type, f"<p>{context}</p>")
                html_part.attach(MIMEText(html_body, "html"))
                msg.attach(html_part)

                # Attach the PDF
                part = MIMEBase("application", "pdf")
                part.set_payload(attachment_bytes)
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=attachment_name,
                )
                msg.attach(part)
            else:
                msg = MIMEMultipart("alternative")
                html_body = body_map.get(event_type, f"<p>{context}</p>")
                msg.attach(MIMEText(html_body, "html"))

            msg["Subject"] = subject_map.get(event_type, "Notification from Akriti Diagnostics")
            msg["From"] = f"{settings.MAIL_FROM_NAME} <{settings.MAIL_FROM}>"
            msg["To"] = recipient_email

            # Check if Brevo HTTP API is configured (to bypass Render SMTP block)
            brevo_api_key = os.getenv("BREVO_API_KEY")
            if brevo_api_key:
                print(f"  [MAIL INFO] Sending email via Brevo HTTP API: {event_type} -> {recipient_email}")
                import httpx
                import base64
                
                headers = {
                    "accept": "application/json",
                    "api-key": brevo_api_key,
                    "content-type": "application/json"
                }
                
                html_body = body_map.get(event_type, f"<p>{context}</p>")
                subject = subject_map.get(event_type, "Notification from Akriti Diagnostics")
                
                payload = {
                    "sender": {"name": settings.MAIL_FROM_NAME, "email": settings.MAIL_FROM},
                    "to": [{"email": recipient_email}],
                    "subject": subject,
                    "htmlContent": html_body
                }
                
                attachment_bytes = context.get("attachment_bytes")
                attachment_name = context.get("attachment_name")
                if attachment_bytes and attachment_name:
                    encoded_content = base64.b64encode(attachment_bytes).decode("utf-8")
                    payload["attachments"] = [
                        {
                            "content": encoded_content,
                            "name": attachment_name
                        }
                    ]
                
                resp = httpx.post("https://api.brevo.com/v3/smtp/email", json=payload, headers=headers, timeout=10.0)
                if resp.status_code in (200, 201, 202):
                    print(f"  [MAIL OK] Email sent successfully via Brevo: {event_type} -> {recipient_email}")
                    logger.info(f"Email sent via Brevo: {event_type} -> {recipient_email}")
                    return True
                else:
                    print(f"  [MAIL ERROR] Brevo API failed ({resp.status_code}): {resp.text}")
                    logger.error(f"Brevo API failed: {resp.text}")
                    return False

            # Fallback to standard SMTP if Brevo is not set (Local Development)
            with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=10.0) as server:
                server.ehlo()
                if settings.MAIL_TLS:
                    server.starttls()
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                server.sendmail(settings.MAIL_FROM, recipient_email, msg.as_string())

            print(f"  [MAIL OK] Email sent successfully: {event_type} -> {recipient_email}")
            logger.info(f"Email sent: {event_type} -> {recipient_email}")
            return True

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"  [MAIL ERROR] Email send failed: {e}")
            logger.error(f"Email send failed: {e}")
            return False


class WhatsAppProvider(NotificationProvider):
    """Stub — not enabled in v1. Fill in send() method to enable."""
    def send(self, event_type: str, recipient_email: str, context: Dict[str, Any]) -> bool:
        raise NotImplementedError("WhatsApp provider not enabled in this version")


class SmsProvider(NotificationProvider):
    """Stub — not enabled in v1. Fill in send() method to enable."""
    def send(self, event_type: str, recipient_email: str, context: Dict[str, Any]) -> bool:
        raise NotImplementedError("SMS provider not enabled in this version")


# Provider registry — add WhatsApp/SMS here when ready to enable
PROVIDER_REGISTRY: Dict[str, list] = {
    "otp": [EmailProvider()],
    "password_reset": [EmailProvider()],
    "report_ready": [EmailProvider()],
    "welcome_staff": [EmailProvider()],
}


def notify(event_type: str, recipient_email: str, context: Dict[str, Any]):
    print(f"  [MAIL START] notify() called: {event_type} -> {recipient_email}")
    """
    Single call point for all notifications throughout the system.
    Never call provider.send() directly — always go through this function.
    """
    if not EMAIL_NOTIFICATIONS_ENABLED:
        print(f"  [MAIL SKIP] Notification skipped (emails disabled globally): {event_type} -> {recipient_email}")
        logger.info(f"Notification skipped (emails disabled globally): {event_type} -> {recipient_email}")
        return

    providers = PROVIDER_REGISTRY.get(event_type, [])
    for provider in providers:
        try:
            provider.send(event_type, recipient_email, context)
        except NotImplementedError:
            pass
        except Exception as e:
            logger.error(f"Notification error [{event_type}]: {e}")
