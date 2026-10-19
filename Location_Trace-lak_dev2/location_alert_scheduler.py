import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import smtplib
from email.mime.text import MIMEText
import os
import logging
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

# Console output for immediate feedback
print(f"Script started execution at {datetime.now()}")

# Configure logging with robust path handling
log_dir = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
log_path = os.path.join(log_dir, 'alert_log.log')
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

# Load database configuration
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
    "email_password": "cjui vzdk meyt jnqa"
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
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP authentication error at {datetime.now()}: {e}")
        logger.error("SMTP authentication error at %s: %s", datetime.now(), str(e))
    except smtplib.SMTPException as e:
        print(f"SMTP error at {datetime.now()}: {e}")
        logger.error("SMTP error at %s: %s", datetime.now(), str(e))
    except Exception as e:
        print(f"Unexpected email error at {datetime.now()}: {e}")
        logger.error("Unexpected email error at %s: %s", datetime.now(), str(e))

def check_location_movement():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Log available location data for debugging
            cur.execute("SELECT google_account, COUNT(*), MAX(server_time) FROM location_data GROUP BY google_account;")
            data_counts = cur.fetchall()
            print(f"Available location data: {data_counts}")
            logger.info("Available location data: %s", data_counts)

            # Fetch the starting location from the first enabled alert
            cur.execute("""
                SELECT longitude, latitude, distance, email, enabled, last_alert, users, processing
                FROM location_alerts
                WHERE enabled = TRUE AND id = 1
                LIMIT 1;
            """)
            start_alert = cur.fetchone()
            if not start_alert:
                print("No valid starting location found in location_alerts.")
                logger.warning("No valid starting location found in location_alerts.")
                return

            cur.execute("""
                SELECT la.id, la.longitude, la.latitude, la.distance, la.email, la.enabled, la.last_alert, la.users, la.processing,
                       ld.longitude AS current_lon, ld.latitude AS current_lat, ld.google_account
                FROM location_alerts la
                LEFT JOIN LATERAL (
                    SELECT longitude, latitude, google_account
                    FROM location_data
                    WHERE server_time = (SELECT MAX(server_time) FROM location_data WHERE COALESCE(LOWER(google_account), LOWER(la.users)) = LOWER(la.users))
                ) ld ON TRUE
                WHERE la.enabled = TRUE;
            """)
            alerts = cur.fetchall()
            print(f"Retrieved alerts: {alerts}")
            logger.info("Retrieved alerts: %s", alerts)

            for alert in alerts:
                # Fallback to latest available data if current is None, handling case sensitivity
                if alert["current_lon"] is None or alert["current_lat"] is None:
                    print("No current location data available, falling back to latest data for user:", alert["users"])
                    logger.warning("No current location data available, falling back to latest data for user: %s", alert["users"])
                    cur.execute("""
                        SELECT longitude, latitude
                        FROM location_data
                        WHERE COALESCE(LOWER(google_account), LOWER(%s)) = LOWER(%s)
                        AND longitude IS NOT NULL AND latitude IS NOT NULL
                        ORDER BY server_time DESC
                        LIMIT 1;
                    """, (alert["users"], alert["users"]))
                    fallback = cur.fetchone()
                    if fallback:
                        alert["current_lon"] = fallback["longitude"]
                        alert["current_lat"] = fallback["latitude"]
                        print(f"Fallback location used: ({alert['current_lat']}, {alert['current_lon']})")
                        logger.info("Fallback location used: (%.6f, %.6f) for user %s", alert["current_lat"], alert["current_lon"], alert["users"])
                    else:
                        print("No fallback location data available for user:", alert["users"])
                        logger.warning("No fallback location data available for user: %s", alert["users"])
                        continue

                lon1, lat1 = radians(start_alert["longitude"]), radians(start_alert["latitude"])
                lon2, lat2 = radians(float(alert["current_lon"])), radians(float(alert["current_lat"]))
                dlon = lon2 - lon1
                dlat = lat2 - lat1

                a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                distance = 6371 * c  # Earth radius in kilometers
                tolerance = 0.001
                print(f"Calculated distance: {distance:.4f} km (tolerance: {tolerance} km), threshold: {alert['distance'] + tolerance} km")
                logger.info("Calculated distance: %.4f km (tolerance: %.3f km) for start (%.6f, %.6f) vs current (%.6f, %.6f) for user %s",
                            distance, tolerance, start_alert["longitude"], start_alert["latitude"], alert["current_lon"], alert["current_lat"], alert["users"])

                # Update processing and send email if distance exceeds threshold
                if distance >= (alert["distance"] + tolerance) and alert["processing"] == 0:
                    # Update processing
                    cur.execute("UPDATE location_alerts SET processing = 1 WHERE id = %s", (alert["id"],))
                    conn.commit()
                    print(f"Processing set to 1 for distance {distance:.2f} km for user {alert['users']}")
                    logger.info("Processing set to 1 for distance %.2f km for user %s", distance, alert["users"])

                    # Send email without cooldown
                    emails = [email.strip() for email in (alert["email"] or "").split(",") if email.strip()]
                    if not emails:
                        print("No email addresses found in location_alerts for user:", alert["users"])
                        logger.warning("No email addresses found in location_alerts for user: %s", alert["users"])
                        continue
                    print(f"Triggering email to: {', '.join(emails)}")
                    logger.info("Triggering email to: %s for user %s", ", ".join(emails), alert["users"])
                    send_email(
                        subject="Location Alert",
                        body=f"Alert: User {alert['users']} has gone more than {alert['distance']} km from the starting point ({start_alert['latitude']}, {start_alert['longitude']}). Distance: {distance:.2f} km.",
                        emails=emails
                    )
                    cur.execute("UPDATE location_alerts SET last_alert = NOW() WHERE id = %s", (alert["id"],))
                    conn.commit()
                    print(f"Alert triggered and last_alert updated for distance {distance:.2f} km to {', '.join(emails)}")
                    logger.info("Alert triggered and last_alert updated for distance %.2f km to %s", distance, ", ".join(emails))
                # Reset processing if within distance threshold and previously triggered
                elif distance < alert["distance"] and alert["processing"] == 1:
                    cur.execute("UPDATE location_alerts SET processing = 0, last_alert = NOW() WHERE id = %s", (alert["id"],))
                    conn.commit()
                    print(f"User {alert['users']} returned within {alert['distance']} km, processing set to 0.")
                    logger.info("User %s returned within %.1f km, processing set to 0.", alert["users"], alert["distance"])

    except psycopg2.Error as e:
        print(f"Error checking location movement: {e}")
        logger.error("Error checking location movement: %s", str(e))
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Unexpected error in location check: {e}")
        logger.error("Unexpected error in location check: %s", str(e))
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")
            logger.info("Database connection closed.")

if __name__ == "__main__":
    check_location_movement()