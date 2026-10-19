```markdown
# Deployment Documentation for Location Trace Project and Cron Job on Ubuntu Linux

This document provides a step-by-step guide to deploy the Location Trace project, consisting of a React frontend, FastAPI backend, and PostgreSQL database, along with a cron job for automation, on any Ubuntu Linux machine (Ubuntu 24.04 LTS or later). The guide uses absolute paths and generic credentials to ensure portability across any Ubuntu PC with administrative (sudo) privileges.

## Prerequisites

### General
- An Ubuntu Linux machine with sudo privileges.
- Internet access to install dependencies.
- Basic knowledge of the terminal and Git.

### Project-Specific
- The React frontend and FastAPI backend files (e.g., `main.py`, React source code) available locally or from a Git repository.
- The cron job script `upload_json_to_postgis.py` for automation.

### Credentials
- **SSH**: `user@gmail.com` with password `password123` (replace with actual credentials during deployment).
- **PostgreSQL**: User `postgres`, password `password123`, database `location_tracker`.
- **FastAPI**: JWT `SECRET_KEY` (e.g., a random string like `your-secret-key`), user `user@gmail.com`, password `password123`.

## Deployment Steps

### 1. Prepare the System
Ensure the system is up-to-date and required packages are installed.

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git
```

### 2. Configure PostgreSQL
Set up the database for the Location Trace project.

```bash
sudo -u postgres psql
```

Inside `psql`:
```sql
CREATE DATABASE location_tracker;
ALTER USER postgres WITH PASSWORD 'password123';
\q
```

Verify database access:
```bash
psql -h localhost -U postgres -d location_tracker -c "\dt"
```

### 3. Deploy the Backend
Set up the FastAPI backend.

#### Create Project Directory
```bash
sudo mkdir -p /home/user/my-map-app
sudo chown user:user /home/user/my-map-app
```

#### Set Up Virtual Environment
```bash
cd /home/user/my-map-app
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn psycopg2-binary python-jose[cryptography] passlib[bcrypt] python-multipart python-dotenv
```

#### Transfer and Configure `main.py`
Assume `main.py` is available locally (e.g., downloaded or cloned):
```bash
sudo mv /path/to/main.py /home/user/my-map-app/main.py
```

Set environment variables:
```bash
nano /home/user/my-map-app/.env
```

Add to `.env`:
```
SECRET_KEY=your-secret-key
DB_HOST=localhost
DB_PORT=5432
DB_NAME=location_tracker
DB_USER=postgres
DB_PASSWORD=password123
```

Save and exit. Load variables:
```bash
export $(cat /home/user/my-map-app/.env | xargs)
echo 'export $(cat /home/user/my-map-app/.env | xargs)' >> ~/.bashrc
source ~/.bashrc
```

#### Start FastAPI
```bash
cd /home/user/my-map-app
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8080 &
```

#### Test the API
```bash
curl -X POST http://localhost:8080/api/login -d "username=user@gmail.com&password=password123"
curl -H "Authorization: Bearer <jwt-token>" http://localhost:8080/api/location-data
```

### 4. Deploy the Frontend
Build and deploy the React frontend.

#### Install Frontend Dependencies
Clone the repository (replace `<repository-url>` with your Git URL):
```bash
git clone <repository-url> /home/user/my-map-app
cd /home/user/my-map-app
npm install axios react-plotly.js plotly.js moment moment-timezone
```

#### Build the Frontend
```bash
npm run build
```

#### Transfer Build Files
Move the build output:
```bash
sudo mv /home/user/my-map-app/build /home/user/my-map-app/build_temp
sudo mkdir -p /home/user/my-map-app/build
sudo mv /home/user/my-map-app/build_temp/* /home/user/my-map-app/build/
sudo rm -rf /home/user/my-map-app/build_temp
```

Fix directory permissions:
```bash
sudo chown -R user:user /home/user/my-map-app/build
sudo chmod -R 775 /home/user/my-map-app/build
```

### 5. Configure Nginx
Set up Nginx to serve the frontend and proxy API requests.

#### Configure Nginx
```bash
sudo nano /etc/nginx/sites-enabled/default
```

Add:
```nginx
server {
    listen 8081;
    server_name _;
    location / {
        root /home/user/my-map-app/build;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    location /api/ {
        proxy_pass http://localhost:8080/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Save and exit. Remove conflicting files:
```bash
sudo rm -r /etc/nginx/sites-enabled/*
sudo ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
```

Fix Nginx PID permissions:
```bash
sudo touch /run/nginx.pid
sudo chown www-data:www-data /run/nginx.pid
sudo chmod 644 /run/nginx.pid
```

Test and restart Nginx:
```bash
sudo nginx -t
sudo systemctl restart nginx
```

#### Test Frontend
```bash
curl -I http://localhost:8081/index.html
curl http://localhost:8081
```

### 6. Deploy the Cron Job
Automate tasks with a cron job.

#### Create Script Directory
```bash
sudo mkdir -p /home/user/scripts
sudo mkdir -p /home/user/logs
sudo chmod -R 755 /home/user/scripts /home/user/logs
```

#### Move the Script
```bash
sudo mv /path/to/upload_json_to_postgis.py /home/user/scripts/upload_json_to_postgis.py
```

#### Set Execute Permissions
```bash
sudo chmod +x /home/user/scripts/upload_json_to_postgis.py
```

#### Open the Crontab
```bash
crontab -e
```

#### Add the Cron Job
Add a line to run every minute:
```
* * * * * /usr/bin/python3 /home/user/scripts/upload_json_to_postgis.py >> /home/user/logs/cron.log 2>&1
```
Save and exit (Ctrl + O, Enter, Ctrl + X).

#### Create the Log File
```bash
sudo touch /home/user/logs/cron.log
sudo chmod 644 /home/user/logs/cron.log
```

#### Verify the Cron Job
```bash
crontab -l
```
Wait one minute, then check the log:
```bash
cat /home/user/logs/cron.log
```

### 7. Verify Deployment
- **Backend**: Check logs (if implemented) or API responses.
- **Frontend**: Open `http://localhost:8081/` in a browser, log in with `user@gmail.com` and `password123`, and verify the map pulsating circle and battery chart (`Local Time` or `N/A`).
- **Cron Job**: Ensure `cron.log` shows script output.

### 8. Troubleshooting
- **SCP Permission Denied**:
  ```bash
  ls -ld /home/user/my-map-app/build
  sudo chown -R user:user /home/user/my-map-app/build
  sudo chmod -R 775 /home/user/my-map-app/build
  ```
- **Nginx Errors**:
  ```bash
  sudo systemctl status nginx
  sudo nginx -t
  tail -f /var/log/nginx/error.log
  sudo chown www-data:www-data /run/nginx.pid
  sudo chmod 644 /run/nginx.pid
  ```
- **Unexpected Token '<'**:
  ```bash
  ls -l /home/user/my-map-app/build/static/js/main.<hash>.js
  curl -I http://localhost:8081/static/js/main.<hash>.js
  ```
- **Incorrect `local_time`**:
  ```bash
  psql -h localhost -U postgres -d location_tracker -c "SELECT server_time, local_time, battery_level, google_account FROM location_data LIMIT 5;"
  ```

### 9. Maintenance
- **Update Project**:
  ```bash
  cd /home/user/my-map-app
  git pull
  npm run build
  sudo mv /home/user/my-map-app/build_temp/* /home/user/my-map-app/build/
  sudo rm -rf /home/user/my-map-app/build_temp
  sudo cp -r /home/user/my-map-app/build /var/www/Location_Trace/my-map-app/
  sudo systemctl restart nginx
  ```
- **Restart Services**:
  ```bash
  cd /home/user/my-map-app
  source venv/bin/activate
  pkill -f uvicorn
  uvicorn main:app --host 0.0.0.0 --port 8080 &
  ```
