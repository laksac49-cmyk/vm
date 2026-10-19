import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import smtplib
from email.mime.text import MIMEText
import os
import logging
from datetime import datetime, timedelta
import re

# Console output for immediate feedback
print(f"Script started execution at {datetime.now()}")

# Configure logging with robust path handling
log_dir = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_path = os.path.join(log_dir, 'last_update_alert_log.log')
logger = None
try:
    if not os.path.exists(log_path):
        with open(log_path, 'a') as f:
            f.write(f"Log file created at {datetime.now()}\n")
            f.flush()
            os.fsync(f.fileno())
    logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()
    logger.info("Script started execution. Log path: %s", log_path)
    with open(log_path, 'a') as f:
        f.write(f"Test write successful at {datetime.now()}\n")
        f.flush()
        os.fsync(f.fileno())
    print(f"Logging initialized to {log_path}")
except PermissionError as e:
    print(f"Warning: Cannot write to {log_path}. Error: {e}. Using console only.")
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()
    logger.info("Logging to console only due to permission error: %s", str(e))
except Exception as e:
    print(f"Warning: Logging setup failed. Error: {e}. Using console only.")
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()
    logger.info("Logging to console only due to error: %s", str(e))

# Check for required modules
try:
    import psycopg2
    import smtplib
    logger.info("Required modules (psycopg2, smtplib) are available.")
except ImportError as e:
    print(f"Error: Missing module - {e}. Install with 'pip install psycopg2-binary'.")
    logger.error("Missing module: %s", str(e))
    sys.exit(1)

# Database configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "location_tracker"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "root")
}

# Email configuration
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "email_user": "g20016.lakmal@gmail.com",
    "email_password": "cjui vzdk meyt jnqa",
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Database connection established.")
        logger.info("Database connection established.")
        return conn
    except psycopg2.Error as e:
        print(f"Database connection failed: {e}")
        logger.error("Database connection failed: %s", str(e))
        raise

def send_email(subject: str, body: str, emails: list):
    try:
        print(f"Attempting to send email to {', '.join(emails)} at {datetime.now()}")
        logger.info("Attempting to send email to %s at %s", ", ".join(emails), datetime.now())
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_CONFIG["email_user"]
        msg['To'] = ", ".join(emails)

        with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["email_user"], EMAIL_CONFIG["email_password"])
            server.send_message(msg)
        print(f"Email sent to {', '.join(emails)} at {datetime.now()}")
        logger.info("Email sent to %s at %s", ", ".join(emails), datetime.now())
        return True
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP authentication error at {datetime.now()}: {e}")
        logger.error("SMTP authentication error at %s: %s", datetime.now(), str(e))
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP email error at {datetime.now()}: {e}")
        logger.error("SMTP error at %s: %s", datetime.now(), str(e))
        return False
    except Exception as e:
        print(f"Unexpected email error at {datetime.now()}: {e}")
        logger.error("Unexpected email error at %s: %s", datetime.now(), str(e))
        return False

def parse_last_update_time(last_update_str: str) -> int | None:
    """Extract numeric minutes from last_update string (e.g., '15' from '15 min ago')."""
    if not last_update_str:
        return None
    try:
        if last_update_str.strip().lower() == "just now":
            return 0
        match = re.match(r'(\d+)', last_update_str)
        if match:
            minutes = int(match.group(1))
            return minutes
        else:
            print(f"Warning: Could not parse last_update string: {last_update_str}")
            logger.warning("Could not parse last_update string: %s", last_update_str)
            return None
    except Exception as e:
        print(f"Error parsing last_update: {last_update_str}: {e}")
        logger.error("Error parsing last_update: %s: %s", last_update_str, str(e))
        return None

def check_last_update():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT last_update, server_time, STRING_AGG(DISTINCT google_account, ', ') AS users
                FROM location_data
                WHERE server_time = (SELECT MAX(server_time) FROM location_data)
                GROUP BY last_update, server_time;
            """)
            result = cur.fetchone()
            last_update_server_time = result['server_time'] if result and result['server_time'] else None
            last_update_str = result['last_update'] if result and result['last_update'] else None
            users = result['users'] if result and result['users'] else 'Unknown User'
            last_update_minutes = parse_last_update_time(last_update_str) if last_update_str else None
            print(f"Last update from server_time: {last_update_server_time}")
            print(f"Last update string: {last_update_str}")
            print(f"Extracted last_update minutes: {last_update_minutes}")
            print(f"Users from google_account: {users}")
            logger.info("Last update from server_time: %s, last_update string: %s, extracted minutes: %s, users: %s",
                        last_update_server_time, last_update_str, last_update_minutes, users)

            cur.execute("""
                UPDATE last_update_alerts SET users = %s, user_email = %s WHERE enabled = TRUE;
            """, (users, users))
            conn.commit()
            logger.info("Updated users and user_email to %s in last_update_alerts", users)

            cur.execute("SELECT email, enabled, last_alert, users, processing, user_email, last_alert_time FROM last_update_alerts WHERE enabled = TRUE;")
            alerts = cur.fetchall()
            print(f"Retrieved alerts: {alerts}")
            logger.info("Retrieved alerts: %s", alerts)

            if last_update_str is not None and alerts:
                for alert in alerts:
                    emails = [email.strip() for email in (alert["email"] or "").split(",") if email.strip()]
                    logger.debug("Checking alert: email=%s, processing=%d, last_alert=%s, last_update_str=%s, last_update_minutes=%s",
                                 alert["email"], alert["processing"], alert["last_alert"], last_update_str, last_update_minutes)
                    if last_update_str.strip().lower() == "just now" or (last_update_minutes is not None and last_update_minutes <= 10):
                        logger.debug("Condition: last_update is 'Just now' or <= 10 minutes")
                        if alert["processing"] == 1:
                            cur.execute("UPDATE last_update_alerts SET processing = 0 WHERE email = %s", (alert["email"],))
                            conn.commit()
                            print(f"Updated processing to 0 for email {alert['email']} at {datetime.now()} (last_update: {last_update_str})")
                            logger.info("Updated processing to 0 for email %s at %s (last_update: %s)", alert["email"], datetime.now(), last_update_str)
                        print(f"No last update alert: {last_update_str}, last_alert check passed")
                        logger.info("No last update alert: %s, last_alert check passed", last_update_str)
                    elif last_update_minutes is not None and last_update_minutes > 10:
                        logger.debug("Condition: last_update_minutes > 10")
                        if alert["processing"] == 0:
                            cur.execute("UPDATE last_update_alerts SET processing = 1 WHERE email = %s", (alert["email"],))
                            conn.commit()
                            print(f"Updated processing to 1 for email {alert['email']} at {datetime.now()} (last_update: {last_update_str})")
                            logger.info("Updated processing to 1 for email %s at %s (last_update: %s)", alert["email"], datetime.now(), last_update_str)
                        
                        logger.debug("Checking email send: processing=%d, last_alert=%s, cooldown_met=%s",
                                     alert["processing"], alert["last_alert"],
                                     alert["last_alert"] is None or (datetime.now() - alert["last_alert"]).total_seconds() > 600)
                        if alert["processing"] == 1:
                            if alert["last_alert"] is None or (datetime.now() - alert["last_alert"]).total_seconds() > 600:
                                print(f"Triggering last update alert: {last_update_minutes} minutes since last update")
                                logger.info("Triggering last update alert: %d minutes since last update", last_update_minutes)
                                if send_email(
                                    subject="Last Update Alert",
                                    body=f"Alert: GPS tracker for {alert['users']} has not updated for {last_update_minutes} minutes.\n"
                                         f"Last server time: {last_update_server_time}\nLast update string: {last_update_str}",
                                    emails=emails
                                ):
                                    cur.execute("UPDATE last_update_alerts SET last_alert = NOW(), last_alert_time = NOW() WHERE email = %s", (alert["email"],))
                                    conn.commit()
                                    print(f"Updated last_alert and last_alert_time to {datetime.now()}")
                                    logger.info("Updated last_alert and last_alert_time to %s", datetime.now())
                                    break
                            else:
                                logger.debug("Email not sent: cooldown not met")
                                print(f"Email not sent: cooldown not met for {alert['email']}")
                    else:
                        print("No valid last_update minutes available")
                        logger.warning("No valid last_update minutes available")
            else:
                print("No valid last_update string or no enabled alerts available")
                logger.warning("No valid last_update string or no enabled alerts available")
    except psycopg2.Error as e:
        print(f"Error checking last update alert: {e} at {datetime.now()}")
        logger.error("Error checking last update alert: %s at %s", str(e), datetime.now())
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Unexpected error in last update check: {e} at {datetime.now()}")
        logger.error("Unexpected error in last update check: %s at %s", str(e), datetime.now())
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")
            logger.info("Database connection closed.")

if __name__ == "__main__":
    check_last_update()