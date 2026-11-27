import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class EmailService:
    """Configurable SMTP email notification service with graceful fallback when unconfigured."""

    @classmethod
    def is_configured(cls):
        """Checks if SMTP environment credentials are configured."""
        host = os.environ.get("SMTP_HOST")
        user = os.environ.get("SMTP_USER")
        return bool(host and user)

    @classmethod
    def send_email(cls, to_email, subject, body_text, body_html=None):
        """
        Sends an email via SMTP.
        Does NOT crash or block database transactions on delivery failure.
        """
        if not cls.is_configured():
            # Graceful bypass: SMTP not configured; skip sending
            logger.info("SMTP not configured. Skipping email to %s for subject: %s", to_email, subject)
            return False

        try:
            host = os.environ.get("SMTP_HOST")
            port = int(os.environ.get("SMTP_PORT", 587))
            username = os.environ.get("SMTP_USER")
            password = os.environ.get("SMTP_PASSWORD")
            sender = os.environ.get("SMTP_FROM", username)
            use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() in ("true", "1")

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = to_email

            part1 = MIMEText(body_text, "plain", "utf-8")
            msg.attach(part1)

            if body_html:
                part2 = MIMEText(body_html, "html", "utf-8")
                msg.attach(part2)

            with smtplib.SMTP(host, port, timeout=5) as server:
                if use_tls:
                    server.starttls()
                if username and password:
                    server.login(username, password)
                server.sendmail(sender, [to_email], msg.as_string())

            logger.info("Email notification successfully sent to %s", to_email)
            return True
        except Exception as err:
            logger.warning("Failed to send email to %s: %s", to_email, str(err))
            return False

