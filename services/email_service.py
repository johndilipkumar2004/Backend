import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM", "Ideal Institute of Technology")


class EmailService:

    async def send_parent_alert(
        self,
        parent_email: str,
        student_name: str,
        roll_number: str,
        class_name: str,
        faculty_name: str,
        date: str,
    ) -> dict:
        subject = f"Attendance Alert - {student_name} ({roll_number})"
        body = f"""
Dear Parent/Guardian,

This is an automated attendance alert from Ideal Institute of Technology.

Your child {student_name} (Roll No: {roll_number}) was marked ABSENT today in:

  📚 Class   : {class_name}
  👨‍🏫 Faculty : {faculty_name}
  📅 Date    : {date}

Please ensure regular attendance for better academic performance.
Students must maintain a minimum of 75% attendance.

If you believe this is an error, please contact the faculty directly.

Regards,
Smart Attendance AI System
Ideal Institute of Technology
        """
        return await self._send_email(parent_email, subject, body)

    async def send_custom_message(
        self,
        to_email: str,
        subject: str,
        body: str,
    ) -> dict:
        return await self._send_email(to_email, subject, body)

    async def _send_email(self, to_email: str, subject: str, body: str) -> dict:
        if not EMAIL_USERNAME or not EMAIL_PASSWORD:
            # Email not configured — log and return success for dev mode
            print(f"📧 [DEV MODE] Email to {to_email}: {subject}")
            print("⚠️  Set EMAIL_USERNAME and EMAIL_PASSWORD in your .env file to send real emails.")
            return {"success": False, "message": "Email not configured. Please set EMAIL_USERNAME and EMAIL_PASSWORD in .env"}

        try:
            msg = MIMEMultipart("alternative")
            # FIX: Use actual email address in From header, not just display name
            msg["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_USERNAME}>"
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            await aiosmtplib.send(
                msg,
                hostname=EMAIL_HOST,
                port=EMAIL_PORT,
                username=EMAIL_USERNAME,
                password=EMAIL_PASSWORD,
                start_tls=True,
            )
            print(f"✅ Email sent to {to_email}: {subject}")
            return {"success": True, "message": f"Email sent to {to_email}"}
        except aiosmtplib.SMTPAuthenticationError:
            print("❌ SMTP Auth failed — check EMAIL_USERNAME and EMAIL_PASSWORD in .env")
            return {"success": False, "message": "Authentication failed. Use a Gmail App Password, not your regular password."}
        except aiosmtplib.SMTPConnectError:
            print("❌ SMTP Connect failed — check EMAIL_HOST and EMAIL_PORT in .env")
            return {"success": False, "message": "Could not connect to SMTP server. Check EMAIL_HOST and EMAIL_PORT."}
        except Exception as e:
            print(f"❌ Email error: {e}")
            return {"success": False, "message": str(e)}


email_service = EmailService()