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
EMAIL_FROM = os.getenv("EMAIL_FROM", "Smart Attendance AI")


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

This is an automated attendance alert from Smart Attendance AI.

Your child {student_name} (Roll No: {roll_number}) was marked ABSENT today in:

  📚 Class   : {class_name}
  👨‍🏫 Faculty : {faculty_name}
  📅 Date    : {date}

Please ensure regular attendance for better academic performance.
Students must maintain a minimum of 75% attendance.

If you believe this is an error, please contact the faculty directly.

Regards,
Smart Attendance AI System
University Attendance Management
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
            return {"success": True, "message": "Email logged (dev mode — configure SMTP to send)"}

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = EMAIL_FROM
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
            return {"success": True, "message": f"Email sent to {to_email}"}
        except Exception as e:
            return {"success": False, "message": str(e)}


email_service = EmailService()
