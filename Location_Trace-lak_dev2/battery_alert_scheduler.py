import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import smtplib
from email.mime.text import MIMEText
import os
import logging
from datetime import datetime

# Console output for immediate feedback
print(f"Script started execution at {datetime.now()}")

# Configure logging
log_dir = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_path = os.path.join(log_dir, 'battery_alert_log.log')
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
    logger.error(f"Missing module: {e}")
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

def send_email(subject: str, body: str, emails):
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
    except smtplib.SMTPException as e:
        print(f"Email error at {datetime.now()}: {e}")
        logger.error("Email error at %s: %s", datetime.now(), str(e))
    except Exception as e:
        print(f"Unexpected email error at {datetime.now()}: {e}")
        logger.error("Unexpected email error at %s: %s", datetime.now(), str(e))

def check_battery_alert():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT battery_level
                FROM location_data
                WHERE server_time = (SELECT MAX(server_time) FROM location_data);
            """)
            latest_data = cur.fetchone()
            if not latest_data or not latest_data['battery_level']:
                print(f"No valid battery level data at {datetime.now()}")
                logger.warning("No valid battery level data at %s", datetime.now())
                return

            try:
                battery_str = latest_data['battery_level'].strip()
                if battery_str.lower() == "battery info not available":
                    print(f"Battery level unavailable: {battery_str} at {datetime.now()}")
                    logger.warning("Battery level unavailable: %s at %s", battery_str, datetime.now())
                    return
                battery = float(battery_str.strip('%') if '%' in battery_str else battery_str)
            except ValueError:
                print(f"Invalid battery level format: {latest_data['battery_level']} at {datetime.now()}")
                logger.error("Invalid battery level format: %s at %s", latest_data['battery_level'], datetime.now())
                return

            cur.execute("SELECT id, emails, enabled, last_alert, users, processing FROM battery_alerts WHERE enabled = TRUE;")
            alerts = cur.fetchall()
            print(f"Retrieved alerts: {alerts}")
            logger.info("Retrieved alerts: %s", alerts)

            for alert in alerts:
                print(f"Evaluating battery: {battery}%")
                logger.info("Evaluating battery: %.1f%%", battery)
                last_alert_time = alert["last_alert"] if alert["last_alert"] else datetime.min
                time_diff = (datetime.now() - last_alert_time).total_seconds()
                time_check = last_alert_time == datetime.min or time_diff > 3600  # 1-hour cooldown

                if battery < 10 and alert["processing"] == 0:
                    cur.execute("UPDATE battery_alerts SET processing = 1 WHERE id = %s", (alert["id"],))
                    conn.commit()
                    print(f"Processing set to 1 for battery {battery:.1f}% at {datetime.now()}")
                    logger.info("Processing set to 1 for battery %.1f%% at %s", battery, datetime.now())
                    emails = [email.strip() for email in alert["emails"].split(",") if email.strip()]
                    if not emails:
                        emails = EMAIL_CONFIG["email_user"].split(",")  # Fallback to email_user
                    print(f"Triggering email to: {', '.join(emails)} with user {alert['users']} at {datetime.now()}")
                    logger.info("Triggering email to: %s with user %s at %s", ", ".join(emails), alert["users"], datetime.now())
                    send_email(
                        subject="Battery Alert",
                        body=f"Alert: Battery level for {alert['users']} is {battery:.1f}%, below 10%.",
                        emails=emails
                    )
                    cur.execute("UPDATE battery_alerts SET last_alert = NOW() WHERE id = %s", (alert["id"],))
                    conn.commit()
                    print(f"Updated last_alert to {datetime.now()}")
                    logger.info("Updated last_alert to %s", datetime.now())
                elif battery >= 10 and alert["processing"] == 1:
                    cur.execute("UPDATE battery_alerts SET processing = 0 WHERE id = %s", (alert["id"],))
                    conn.commit()
                    print(f"Processing set to 0 for battery {battery:.1f}% at {datetime.now()}")
                    logger.info("Processing set to 0 for battery %.1f%% at %s", battery, datetime.now())
                else:
                    print(f"No battery alert action at {datetime.now()} - battery={battery}%, processing={alert['processing']}")
                    logger.info("No battery alert action at %s - battery=%.1f%%, processing=%d", datetime.now(), battery, alert["processing"])
    except psycopg2.Error as e:
        print(f"Error checking battery alert: {e} at {datetime.now()}")
        logger.error("Error checking battery alert: %s at %s", str(e), datetime.now())
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Unexpected error in battery check: {e} at {datetime.now()}")
        logger.error("Unexpected error in battery check: %s at %s", str(e), datetime.now())
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")
            logger.info("Database connection closed.")

if __name__ == "__main__":
    check_battery_alert()