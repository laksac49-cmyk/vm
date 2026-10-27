# Location Tracker — A–Z Install Guide (Any PC / Podman / Server)

**Goal:** Copy-paste these commands (after filling placeholders) and have a working Location Tracker (Edge extension + JSON upload + PostgreSQL + FastAPI + React map) in about **30 minutes** on any Ubuntu machine or Podman GUI container.

**Public URL:** Section **12** covers DNS, Let’s Encrypt, and reverse proxy so **anyone on the internet** can open your HTTPS hostname (not only localhost).

**Repo layout (expected in your clone):**

| Path | Use |
|------|-----|
| `location_trace/` | Browser extension |
| Backend/frontend reference folder in repo | FastAPI + React (name may vary; adjust after clone) |
| Do not use abandoned / alternate dev trees unless you intend to | — |

**Edit rule:** Use only terminal (`tee`, `sed`, `python3`, `cat`). Do not require nano/vim.

---

## Placeholders (fill before running)

Replace every `<...>` value with yours:

| Placeholder | Meaning | Example shape only |
|-------------|---------|---------------------|
| `<YOUR_GITHUB_REPO_URL>` | Git clone URL | `https://github.com/<org-or-user>/<repo>.git` |
| `<YOUR_LINUX_USER>` | Login user on the app machine | `ubuntu`, `nma`, … |
| `<YOUR_APP_HOME>` | Usually `/home/<YOUR_LINUX_USER>` | `/home/ubuntu` |
| `<YOUR_DB_NAME>` | PostgreSQL database name | `location_tracker` |
| `<YOUR_DB_USER>` | DB user | `postgres` |
| `<YOUR_DB_PASS>` | DB password | *(set a strong secret)* |
| `<YOUR_APP_USER_EMAIL>` | Map app login username | `admin@example.com` |
| `<YOUR_APP_USER_PASS>` | Map app login password | *(set a strong secret)* |
| `<YOUR_SECRET_KEY>` | JWT / app secret | *(long random string)* |
| `<YOUR_PUBLIC_HOSTNAME>` | Public FQDN for the site | `location.example.com` |
| `<YOUR_PUBLIC_IP>` | Internet-facing IP of TLS proxy | `x.x.x.x` |
| `<YOUR_APP_LAN_IP>` | IP where map listens on :80 | container/VM LAN IP |
| `<YOUR_APP_HOST_IP>` | Host that can reach `<YOUR_APP_LAN_IP>` (socat host; may equal proxy) | LAN IP |
| `<YOUR_LETSENCRYPT_EMAIL>` | Email for Let’s Encrypt | `ops@example.com` |
| `<YOUR_OS_TIMEZONE>` | Physical server TZ for `timedatectl` | `UTC`, `Asia/Colombo`, … |
| `<YOUR_DISPLAY>` | X11 display for Edge | `:0` or `:10` (XRDP) |
| `<YOUR_SHARED_MAPS_URL>` | Google Maps share / maps URL to open in Edge | Maps URL |
| `<YOUR_INTERNAL_DNS_IP>` | Optional internal DNS | LAN DNS IP |

**Time rules (NO hardcoded timezone in application code)**

| Field | Meaning | Source |
|--------|---------|--------|
| **serverTime** | Physical server reference time | Public NTP-style HTTP API (UTC instant), then displayed in **this machine’s OS timezone** via `Intl` at **runtime** |
| **localTime** | Location-share **person** time | Scraped from Google Maps page |

Forbidden in app source: fixed city TZ strings, fixed UTC offsets.  
OS timezone is set once with `timedatectl` (ops), not baked into JS as a city name.  
Containers often cannot run `chronyd` — expected; use public time APIs for `serverTime`.

---

## 0) Variables (set once per machine)

```bash
export APP_USER="<YOUR_LINUX_USER>"
export APP_HOME="/home/${APP_USER}"
export EXT_DIR="${APP_HOME}/Location_Trace"
export APP_DIR="${APP_HOME}/my-map-app"
export DB_NAME="<YOUR_DB_NAME>"
export DB_USER="<YOUR_DB_USER>"
export DB_PASS="<YOUR_DB_PASS>"
export MAP_HOSTNAME="<YOUR_PUBLIC_HOSTNAME>"
export GITHUB_REPO="<YOUR_GITHUB_REPO_URL>"
```

Or derive home from current user:

```bash
export APP_USER="${USER}"
export APP_HOME="/home/${APP_USER}"
# still set DB_*, MAP_HOSTNAME, GITHUB_REPO explicitly
```

---

## 1) Base packages

```bash
sudo apt update
sudo apt install -y \
  git curl wget ca-certificates \
  python3 python3-pip python3-venv python3-psycopg2 \
  postgresql postgresql-contrib \
  nginx nodejs npm socat
```

Microsoft Edge:

```bash
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
  | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-edge.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-edge.gpg] https://packages.microsoft.com/repos/edge stable main" \
  | sudo tee /etc/apt/sources.list.d/microsoft-edge.list
sudo apt update
sudo apt install -y microsoft-edge-stable
```

**OS timezone (physical server ops — not JS hardcode):**

```bash
sudo timedatectl set-timezone "<YOUR_OS_TIMEZONE>"
timedatectl
date
date -u
```

---

## 2) Clone code

```bash
cd "${APP_HOME}"
tar -czf "vm_backup_$(date +%Y%m%d_%H%M%S).tar.gz" vm 2>/dev/null || true
rm -rf vm
git clone "<YOUR_GITHUB_REPO_URL>" vm
cd vm
git checkout main
git pull origin main
```

Extension + app dirs (adjust source folder names if your repo differs):

```bash
rm -rf "${EXT_DIR}"
# Typical: extension lives under location_trace/
cp -a "${APP_HOME}/vm/location_trace" "${EXT_DIR}"

mkdir -p "${APP_DIR}"
# Copy backend/frontend tree from repo (pick the folder that contains main.py + React app)
# Example pattern — list and copy the correct tree:
ls "${APP_HOME}/vm"
# Then, for example:
# cp -a "${APP_HOME}/vm/<BACKEND_FRONTEND_FOLDER>/." "${APP_DIR}/"

ls "${EXT_DIR}/content.js" "${EXT_DIR}/manifest.json"
# Ensure main.py exists under APP_DIR after copy
```

---

## 3) PostgreSQL

```bash
sudo systemctl enable --now postgresql
sudo -u postgres psql -c "ALTER USER ${DB_USER} PASSWORD '${DB_PASS}';"
sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME};" 2>/dev/null || true

sudo -u postgres psql -d "${DB_NAME}" << SQL
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL
);
CREATE TABLE IF NOT EXISTS location_data (
    latitude TEXT,
    longitude TEXT,
    address TEXT,
    lat_long TEXT,
    local_time TEXT,
    battery_level TEXT,
    google_account TEXT NOT NULL,
    last_update TEXT,
    server_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    PRIMARY KEY (server_time, google_account)
);
CREATE INDEX IF NOT EXISTS idx_location_google ON location_data (google_account);
CREATE INDEX IF NOT EXISTS idx_location_server_time ON location_data (server_time);
SQL
```

---

## 4) FastAPI backend

```bash
cd "${APP_DIR}"
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install fastapi "uvicorn[standard]" psycopg2-binary python-jose bcrypt python-dotenv python-multipart pydantic
[ -f requirements.txt ] && pip install -r requirements.txt || true

cat > "${APP_DIR}/.env" << EOF
SECRET_KEY=<YOUR_SECRET_KEY>
DB_HOST=localhost
DB_PORT=5432
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASS}
EOF
```

**bcrypt login helper (Python 3.14-safe if passlib breaks):**

```bash
cd "${APP_DIR}"
python3 - << 'PY'
from pathlib import Path
import re
p = Path("main.py")
t = p.read_text()
t = t.replace("from passlib.context import CryptContext", "import bcrypt")
t = re.sub(r"^pwd_context\s*=\s*CryptContext\([^\n]*\n", "", t, flags=re.M)
new = '''def verify_password(plain_password: str, hashed_password: str):
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8") if isinstance(hashed_password, str) else hashed_password
        )
    except Exception:
        return False
'''
if "bcrypt.checkpw" not in t:
    t = re.sub(r"def verify_password\([^)]*\):\n(?:    .*\n)+?", new + "\n", t, count=1)
# Optional: align default env fallback password name only if present
p.write_text(t)
print("main.py auth patch done")
PY
```

Create map login user (replace placeholders in the Python strings):

```bash
cd "${APP_DIR}"
source venv/bin/activate
python3 - << PY
import os, psycopg2, bcrypt
from dotenv import load_dotenv
load_dotenv("${APP_DIR}/.env")
DB = dict(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 5432)),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)
username = "<YOUR_APP_USER_EMAIL>"
password = "<YOUR_APP_USER_PASS>"
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
conn = psycopg2.connect(**DB)
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY, username VARCHAR(255) UNIQUE NOT NULL, hashed_password VARCHAR(255) NOT NULL)""")
cur.execute(
  "INSERT INTO users (username, hashed_password) VALUES (%s,%s) "
  "ON CONFLICT (username) DO UPDATE SET hashed_password = EXCLUDED.hashed_password",
  (username, hashed),
)
conn.commit()
print("OK users ready")
cur.close(); conn.close()
PY

pkill -f "uvicorn main:app" 2>/dev/null || true
nohup uvicorn main:app --host 0.0.0.0 --port 8080 >> "${APP_HOME}/uvicorn.log" 2>&1 &
sleep 2
curl -s -o /dev/null -w "docs:%{http_code}\n" http://127.0.0.1:8080/docs
curl -s -X POST http://127.0.0.1:8080/api/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=<YOUR_APP_USER_EMAIL>&password=<YOUR_APP_USER_PASS>"
```

---

## 5) React map build

```bash
cd "${APP_DIR}"
PKG=$(find "${APP_DIR}" -name package.json -not -path '*/node_modules/*' | head -1)
echo "package.json at: $PKG"
cd "$(dirname "$PKG")"
npm install
npm run build
BUILD_DIR="$(pwd)/build"
echo "BUILD_DIR=$BUILD_DIR"
ls "$BUILD_DIR" | head
```

---

## 6) Nginx on the app machine (HTTP)

```bash
BUILD_DIR=$(find "${APP_DIR}" -type d -name build | head -1)
sudo tee /etc/nginx/sites-available/location-tracker << EOF
server {
    listen 80;
    server_name ${MAP_HOSTNAME} _;
    root ${BUILD_DIR};
    index index.html;
    location / { try_files \$uri \$uri/ /index.html; }
    location /api/ {
        proxy_pass http://127.0.0.1:8080/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
sudo ln -sf /etc/nginx/sites-available/location-tracker /etc/nginx/sites-enabled/location-tracker
sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
sudo chmod -R a+rX "${BUILD_DIR}"
sudo nginx -t && sudo systemctl restart nginx
curl -s -o /dev/null -w "map:%{http_code}\n" http://127.0.0.1/
```

---

## 7) Extension — public NTP serverTime + person localTime

### 7.1 Manifest matches

```bash
cd "${EXT_DIR}"
cp manifest.json "manifest.json.bak_$(date +%Y%m%d%H%M%S)"
python3 - << 'PY'
from pathlib import Path
import json
p = Path("manifest.json")
data = json.loads(p.read_text().strip())
m = [
  "https://www.google.com/maps/*",
  "https://maps.google.com/*",
  "https://maps.app.goo.gl/*",
]
data["host_permissions"] = m
for cs in data.get("content_scripts", []):
    cs["matches"] = m
p.write_text(json.dumps(data, indent=2) + "\n")
print("OK")
PY
```

### 7.2 content.js time block (no city hardcode)

```bash
cd "${EXT_DIR}"
cp content.js "content.js.bak_time_$(date +%Y%m%d_%H%M%S)"
python3 - << 'PY'
from pathlib import Path
import re
p = Path("content.js")
lines = p.read_text().splitlines(keepends=True)
start = end = None
for i, line in enumerate(lines):
    if re.search(r"locationData\.localTime\s*=\s*await scrapeLocalTime\(\)", line) or \
       "const localTimeRaw = await scrapeLocalTime()" in line:
        if start is None:
            start = i
    if start is not None and end is None and i > start:
        if "console.log" in line and "Captured Location Data" in line:
            end = i
            break
if start is None or end is None:
    raise SystemExit("Could not find time block in content.js — inspect fetchData()")

new_block = r'''        const localTimeRaw = await scrapeLocalTime();
        locationData.batteryLevel = await getBatteryLevel();
        locationData.googleAccount = await getGoogleAccount();
        locationData.lastUpdate = await getLastUpdateFromPage();

        // serverTime = public NTP-equivalent UTC INSTANT, displayed in THIS machine OS TZ.
        // localTime  = shared PERSON time from Maps page only.
        // NO hardcoded city / offset in source code.
        function pad(n) { return String(n).padStart(2, "0"); }
        function formatTs24(y, m, d, h, mi, s) {
            return y + "-" + pad(m) + "-" + pad(d) + " " + pad(h) + ":" + pad(mi) + ":" + pad(s);
        }
        function formatInstantInSystemTz(utcIso) {
            const dt = new Date(utcIso);
            if (isNaN(dt.getTime())) return null;
            const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
            const parts = new Intl.DateTimeFormat("en-GB", {
                timeZone: tz, hour12: false,
                year: "numeric", month: "2-digit", day: "2-digit",
                hour: "2-digit", minute: "2-digit", second: "2-digit"
            }).formatToParts(dt);
            const get = (t) => (parts.find((p) => p.type === t) || {}).value;
            let h = get("hour");
            if (h === "24") h = "00";
            return get("year") + "-" + get("month") + "-" + get("day") + " " + h + ":" + get("minute") + ":" + get("second");
        }
        function parseNtpToIso(raw) {
            if (!raw) return null;
            let s = String(raw).trim();
            if (/^\d{4}-\d{2}-\d{2}T/.test(s)) {
                if (!/[Zz]$/.test(s) && !/[+-]\d{2}:?\d{2}$/.test(s)) s += "Z";
                const dt = new Date(s);
                if (isNaN(dt.getTime())) return null;
                return dt.toISOString();
            }
            return null;
        }
        function localTimeFromPage(raw, serverTs) {
            const fallback = (raw && String(raw).trim()) || "N/A";
            if (!raw || raw === "N/A") return fallback;
            const m = String(raw).trim().match(/(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?/);
            if (!m) return fallback;
            let h = parseInt(m[1], 10);
            const mi = parseInt(m[2], 10);
            const ap = (m[3] || "").toUpperCase();
            if (ap === "PM" && h < 12) h += 12;
            if (ap === "AM" && h === 12) h = 0;
            let y, mo, d;
            const nm = serverTs && String(serverTs).match(/^(\d{4})-(\d{2})-(\d{2})/);
            if (nm) {
                y = parseInt(nm[1], 10); mo = parseInt(nm[2], 10); d = parseInt(nm[3], 10);
            } else {
                const now = new Date();
                y = now.getFullYear(); mo = now.getMonth() + 1; d = now.getDate();
            }
            return formatTs24(y, mo, d, h, mi, 0);
        }

        let serverTime = null;
        try {
            const sources = [
                "https://worldtimeapi.org/api/timezone/Etc/UTC",
                "https://timeapi.io/api/Time/current/zone?timeZone=UTC"
            ];
            for (const url of sources) {
                try {
                    const tRes = await fetch(url, { cache: "no-store" });
                    if (!tRes.ok) continue;
                    const tJson = await tRes.json();
                    const iso = parseNtpToIso(
                        tJson.utc_datetime || tJson.dateTime || tJson.datetime || null
                    );
                    if (iso) {
                        serverTime = formatInstantInSystemTz(iso);
                        if (serverTime) break;
                    }
                } catch (e1) {}
            }
        } catch (e) {}
        if (!serverTime) {
            serverTime = formatInstantInSystemTz(new Date().toISOString());
        }

        locationData.serverTime = serverTime;
        locationData.localTime = localTimeFromPage(localTimeRaw, serverTime);

'''
p.write_text("".join(lines[:start] + [new_block] + lines[end:]))
print("OK: public NTP serverTime + Maps localTime")
PY

# Should not list hardcoded city TZ strings you care about removing
grep -nE "timeZone:\s*['\"][A-Za-z]+/" "${EXT_DIR}/content.js" || echo "OK: no city timeZone hardcode pattern"
```

---

## 8) Upload pipeline

```bash
mkdir -p "${APP_HOME}/incoming" "${APP_HOME}/processed" "${APP_HOME}/logs" "${APP_HOME}/Downloads/done"

# Prefer repo upload_json.py if present; else minimal script below
if [ ! -f "${APP_HOME}/upload_json.py" ]; then
tee "${APP_HOME}/upload_json.py" << PY
import os, json, glob, shutil
from datetime import datetime
import psycopg2
DATA_FOLDER = os.path.expanduser("~/incoming")
PROCESSED = os.path.expanduser("~/processed")
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(PROCESSED, exist_ok=True)
DB = dict(
    host="localhost", port=5432,
    dbname=os.environ.get("DB_NAME", "<YOUR_DB_NAME>"),
    user=os.environ.get("DB_USER", "<YOUR_DB_USER>"),
    password=os.environ.get("DB_PASS", "<YOUR_DB_PASS>"),
)

def parse_row(item):
    def g(*keys, default=None):
        for k in keys:
            if k in item and item[k] not in (None, ""):
                return item[k]
        return default
    return dict(
        latitude=str(g("latitude", default="")),
        longitude=str(g("longitude", default="")),
        address=str(g("address", default="")),
        lat_long=str(g("lat,long", "lat_long", default="")),
        local_time=str(g("localTime", "local_time", default="")),
        battery_level=str(g("batteryLevel", "battery_level", default="")),
        google_account=str(g("googleAccount", "google_account", default="unknown")),
        last_update=str(g("lastUpdate", "last_update", default="")),
        server_time=g("serverTime", "server_time", default=None),
    )

def to_ts(v):
    if v is None:
        return datetime.utcnow()
    s = str(v).strip().replace("Z", "")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s[:26], fmt)
        except Exception:
            pass
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return datetime.utcnow()

files = sorted(glob.glob(os.path.join(DATA_FOLDER, "LatLong_*.json")))
print("incoming files:", len(files))
if not files:
    print("Done"); raise SystemExit(0)
conn = psycopg2.connect(**DB)
cur = conn.cursor()
for path in files:
    try:
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
        for item in data:
            r = parse_row(item)
            st = to_ts(r["server_time"])
            cur.execute(
                """INSERT INTO location_data
                (latitude, longitude, address, lat_long, local_time, battery_level,
                 google_account, last_update, server_time)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                (r["latitude"], r["longitude"], r["address"], r["lat_long"], r["local_time"],
                 r["battery_level"], r["google_account"], r["last_update"], st),
            )
        conn.commit()
        shutil.move(path, os.path.join(PROCESSED, os.path.basename(path)))
        print("OK", path)
    except Exception as e:
        conn.rollback()
        print("FAIL", path, e)
cur.close(); conn.close()
print("Done")
PY
fi

# If existing script has a literal DB password, set it to match DB_PASS via sed yourself, e.g.:
# sed -i 's/password=".*"/password="<YOUR_DB_PASS>"/' "${APP_HOME}/upload_json.py"

tee "${APP_HOME}/auto_upload_watcher.sh" << EOF
#!/bin/bash
HOME_DIR="${APP_HOME}"
mkdir -p "\$HOME_DIR/incoming" "\$HOME_DIR/Downloads/done"
for dir in "\$HOME_DIR/Downloads" "\$HOME_DIR/chrome-headless-profile/Default/Downloads"
do
  [ -d "\$dir" ] || continue
  find "\$dir" -maxdepth 1 -type f -name 'LatLong_*.json' -print0 2>/dev/null \
    | while IFS= read -r -d '' f; do
        cp -n "\$f" "\$HOME_DIR/incoming/" 2>/dev/null || true
        mv "\$f" "\$HOME_DIR/Downloads/done/" 2>/dev/null || true
      done
done
EOF
chmod +x "${APP_HOME}/auto_upload_watcher.sh"
```

---

## 9) Edge launcher (GUI / Podman desktop)

```bash
tee "${APP_HOME}/start-edge-maps.sh" << EOF
#!/bin/bash
export DISPLAY="\${DISPLAY:-<YOUR_DISPLAY>}"
export GLYCIN_DISABLE_SANDBOX=1
export HOME="${APP_HOME}"
pkill -f "user-data-dir=${APP_HOME}/chrome-headless-profile" 2>/dev/null || true
sleep 1
mkdir -p "${APP_HOME}/chrome-headless-profile" "${APP_HOME}/logs" "${APP_HOME}/Downloads"
exec /usr/bin/microsoft-edge-stable \\
  --no-sandbox --disable-gpu --disable-dev-shm-usage --disable-software-rasterizer \\
  --remote-debugging-port=9222 \\
  --user-data-dir="${APP_HOME}/chrome-headless-profile" \\
  --load-extension="${EXT_DIR}" \\
  --disable-extensions-except="${EXT_DIR}" \\
  --no-first-run --no-default-browser-check \\
  --disable-features=RendererCodeIntegrity --password-store=basic \\
  "<YOUR_SHARED_MAPS_URL>"
EOF
chmod +x "${APP_HOME}/start-edge-maps.sh"

mkdir -p "${APP_HOME}/Desktop" "${APP_HOME}/.config/autostart"
tee "${APP_HOME}/Desktop/edge-maps-tracker.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Microsoft Edge Maps Tracker
Exec=${APP_HOME}/start-edge-maps.sh
Icon=microsoft-edge
Terminal=false
Categories=Network;WebBrowser;
EOF
chmod +x "${APP_HOME}/Desktop/edge-maps-tracker.desktop"
cp "${APP_HOME}/Desktop/edge-maps-tracker.desktop" "${APP_HOME}/.config/autostart/"

export DISPLAY="<YOUR_DISPLAY>"
export GLYCIN_DISABLE_SANDBOX=1
nohup "${APP_HOME}/start-edge-maps.sh" >> "${APP_HOME}/logs/edge-maps.log" 2>&1 &
```

**Once in GUI:** Sign in to the Google account that receives shared location → open shared Maps link → `edge://extensions` → Reload the tracker extension.

---

## 10) Cron

```bash
crontab -l > /tmp/cron.full 2>/dev/null || true
grep -v 'upload_json.py\|auto_upload_watcher\|start-edge-maps\|uvicorn main:app' /tmp/cron.full > /tmp/cron.new || true
cat >> /tmp/cron.new << EOF
* * * * * ${APP_DIR}/venv/bin/python3 ${APP_HOME}/upload_json.py >> ${APP_HOME}/logs/upload_json.log 2>&1
* * * * * ${APP_HOME}/auto_upload_watcher.sh >> ${APP_HOME}/logs/watcher.log 2>&1
*/5 * * * * pgrep -f 'microsoft-edge.*load-extension' >/dev/null || (export DISPLAY=<YOUR_DISPLAY> GLYCIN_DISABLE_SANDBOX=1; nohup ${APP_HOME}/start-edge-maps.sh >> ${APP_HOME}/logs/edge-maps.log 2>&1 &)
@reboot sleep 20 && cd ${APP_DIR} && ${APP_DIR}/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8080 >> ${APP_HOME}/uvicorn.log 2>&1
EOF
crontab /tmp/cron.new
crontab -l
```

---

## 11) Local verify

```bash
curl -s -o /dev/null -w "docs:%{http_code} map:%{http_code}\n" http://127.0.0.1:8080/docs http://127.0.0.1/
NEW=$(ls -t ${APP_HOME}/Downloads/LatLong_*.json ${APP_HOME}/Downloads/done/LatLong_*.json 2>/dev/null | head -1)
[ -n "$NEW" ] && python3 -m json.tool "$NEW" | head -40
DB_NAME="${DB_NAME}" DB_USER="${DB_USER}" DB_PASS="${DB_PASS}" \
  ${APP_DIR}/venv/bin/python3 ${APP_HOME}/upload_json.py
sudo -u postgres psql -d "${DB_NAME}" -c \
  "SELECT server_time, local_time, latitude, longitude FROM location_data ORDER BY server_time DESC LIMIT 5;"
```

---

## 12) Public internet access (DNS + certificate + HTTPS URL)

**Goal:** Anyone on the internet opens:

```text
https://<YOUR_PUBLIC_HOSTNAME>
```

with a **valid Let’s Encrypt certificate**.

### 12.0 Architecture

**Layout A — single public server**

```text
Internet → DNS A → <YOUR_PUBLIC_IP>
        → Nginx :443 (TLS) on same host as app
        → 127.0.0.1:80 (map) + 127.0.0.1:8080 (API)
```

**Layout B — internal app + edge proxy**

```text
Internet → DNS A → <YOUR_PUBLIC_IP>
        → TLS proxy host Nginx :443
        → <YOUR_APP_HOST_IP>:18081 / :18080 (socat)
        → <YOUR_APP_LAN_IP>:80 / :8080
```

```bash
export PUBLIC_HOSTNAME="<YOUR_PUBLIC_HOSTNAME>"
export PUBLIC_IP="<YOUR_PUBLIC_IP>"
export APP_LAN_IP="<YOUR_APP_LAN_IP>"
export APP_HOST_IP="<YOUR_APP_HOST_IP>"
export EMAIL_FOR_LETSENCRYPT="<YOUR_LETSENCRYPT_EMAIL>"
```

### 12.1 DNS point

**Public DNS (authoritative)**

| Type | Name | Value |
|------|------|--------|
| A | hostname for `<YOUR_PUBLIC_HOSTNAME>` | `<YOUR_PUBLIC_IP>` |

```bash
dig +short "<YOUR_PUBLIC_HOSTNAME>"
# Expect: <YOUR_PUBLIC_IP>
nslookup "<YOUR_PUBLIC_HOSTNAME>"
```

**Optional internal DNS**

```bash
dig @"<YOUR_INTERNAL_DNS_IP>" "<YOUR_PUBLIC_HOSTNAME>" +short
```

**Firewall:** Publish **80/443** on the TLS host only. Do not expose DB (`5432`) or browser debug ports publicly.

### 12.2 Let’s Encrypt certificate

On the host that answers public **port 80** for the hostname:

```bash
sudo apt update
sudo apt install -y certbot python3-certbot-nginx
```

**HTTP-01 (common):**

```bash
sudo mkdir -p /var/www/.well-known/acme-challenge
# Ensure Nginx has:
#   location ^~ /.well-known/acme-challenge/ { root /var/www; default_type text/plain; }

sudo certbot --nginx -d "<YOUR_PUBLIC_HOSTNAME>" \
  --email "<YOUR_LETSENCRYPT_EMAIL>" --agree-tos --non-interactive

# Or webroot-only:
# sudo certbot certonly --webroot -w /var/www \
#   -d "<YOUR_PUBLIC_HOSTNAME>" \
#   --email "<YOUR_LETSENCRYPT_EMAIL>" --agree-tos --non-interactive
```

**Expand an existing multi-SAN cert** (list only names you control):

```bash
sudo certbot certonly --webroot -w /var/www --expand \
  -d "<EXISTING_NAME_1>" \
  -d "<EXISTING_NAME_2>" \
  -d "<YOUR_PUBLIC_HOSTNAME>" \
  --email "<YOUR_LETSENCRYPT_EMAIL>" --agree-tos --non-interactive
```

**DNS-01** when HTTP-01 is impossible (use your DNS provider’s certbot plugin).

Cert files (typical):

```text
/etc/letsencrypt/live/<YOUR_PUBLIC_HOSTNAME>/fullchain.pem
/etc/letsencrypt/live/<YOUR_PUBLIC_HOSTNAME>/privkey.pem
```

If Nginx runs in a container, mount or copy the same PEMs to the path your container config uses.

```bash
sudo openssl x509 -in "/etc/letsencrypt/live/<YOUR_PUBLIC_HOSTNAME>/fullchain.pem" \
  -noout -subject -issuer -dates -ext subjectAltName
sudo systemctl enable --now certbot.timer
sudo certbot renew --dry-run
```

### 12.3 LAN forward (Layout B only)

On **`<YOUR_APP_HOST_IP>`** host (must reach `<YOUR_APP_LAN_IP>`):

```bash
sudo apt-get install -y socat

sudo tee /etc/systemd/system/loc-fwd-map.service << EOF
[Unit]
Description=Forward map to app :80
After=network.target
[Service]
ExecStart=/usr/bin/socat TCP-LISTEN:18081,bind=0.0.0.0,fork,reuseaddr TCP:<YOUR_APP_LAN_IP>:80
Restart=always
RestartSec=3
[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/loc-fwd-api.service << EOF
[Unit]
Description=Forward API to app :8080
After=network.target
[Service]
ExecStart=/usr/bin/socat TCP-LISTEN:18080,bind=0.0.0.0,fork,reuseaddr TCP:<YOUR_APP_LAN_IP>:8080
Restart=always
RestartSec=3
[Install]
WantedBy=multi-user.target
EOF

sudo pkill -f 'socat TCP-LISTEN:18081' 2>/dev/null || true
sudo pkill -f 'socat TCP-LISTEN:18080' 2>/dev/null || true
sudo systemctl daemon-reload
sudo systemctl enable --now loc-fwd-map.service loc-fwd-api.service

curl -s -o /dev/null -w "map:%{http_code}\n" http://127.0.0.1:18081/
curl -s -o /dev/null -w "api:%{http_code}\n" http://127.0.0.1:18080/docs
```

**Map target port is 80, not 8081.**

From proxy host:

```bash
curl -s -o /dev/null -w "via-host-map:%{http_code}\n" http://<YOUR_APP_HOST_IP>:18081/
curl -s -o /dev/null -w "via-host-api:%{http_code}\n" http://<YOUR_APP_HOST_IP>:18080/docs
```

### 12.4 Nginx TLS site

```bash
CERT_DIR="/etc/letsencrypt/live/<YOUR_PUBLIC_HOSTNAME>"
# Layout B:
BACKEND_MAP="http://<YOUR_APP_HOST_IP>:18081"
BACKEND_API="http://<YOUR_APP_HOST_IP>:18080"
# Layout A (same machine):
# BACKEND_MAP="http://127.0.0.1:80"
# BACKEND_API="http://127.0.0.1:8080"

sudo tee /etc/nginx/sites-available/"${PUBLIC_HOSTNAME}.conf" << EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${PUBLIC_HOSTNAME};
    location ^~ /.well-known/acme-challenge/ {
        root /var/www;
        default_type text/plain;
    }
    location / { return 301 https://\$host\$request_uri; }
}
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name ${PUBLIC_HOSTNAME};
    ssl_certificate     ${CERT_DIR}/fullchain.pem;
    ssl_certificate_key ${CERT_DIR}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    client_max_body_size 50m;

    location / {
        proxy_pass ${BACKEND_MAP};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 60;
    }
    location /api/ {
        proxy_pass ${BACKEND_API}/api/;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/"${PUBLIC_HOSTNAME}.conf" /etc/nginx/sites-enabled/
sudo mkdir -p /etc/nginx/sites-available/bak
sudo mv /etc/nginx/sites-enabled/*.bak* /etc/nginx/sites-available/bak/ 2>/dev/null || true
sudo nginx -t && sudo systemctl reload nginx
# If Nginx is in a container, reload inside that container instead.
```

### 12.5 Public URL checklist

| Step | Pass when |
|------|-----------|
| DNS A | `dig +short <YOUR_PUBLIC_HOSTNAME>` = `<YOUR_PUBLIC_IP>` |
| LE cert | issuer Let’s Encrypt; SAN includes hostname |
| App local | `curl` map :80 and API docs :8080 → 200 |
| Forward (B) | `curl` APP_HOST :18081/:18080 → 200 |
| HTTPS | `curl -sk https://<YOUR_PUBLIC_HOSTNAME>/` → 200 |
| Browser | Padlock; login; map loads for any internet user |

```bash
curl -sk -o /dev/null -w "https_root:%{http_code}\n" "https://<YOUR_PUBLIC_HOSTNAME>/"
echo | openssl s_client -connect "<YOUR_PUBLIC_HOSTNAME>:443" \
  -servername "<YOUR_PUBLIC_HOSTNAME>" 2>/dev/null \
  | openssl x509 -noout -issuer -dates -subject
```

`GET /api/login` → **405** is normal; use **POST** for login.

### 12.6 Security

- Use strong `<YOUR_DB_PASS>`, `<YOUR_APP_USER_PASS>`, `<YOUR_SECRET_KEY>`.  
- Do not publish DB or debug ports.  
- Restrict socat to the proxy IP if possible.  
- Keep certbot renewal enabled.

---

## 13) Podman notes

- Prefer an existing GUI container (desktop + RDP/SSH); do not spawn an extra container unless required.  
- `chronyd` may fail without time capabilities — use public NTP HTTP APIs in the extension.  
- Prefer Edge with a real `DISPLAY`, not headless.  
- macvlan app IPs may need socat on the Podman host for other machines.

---

## 14) ~30-minute path

| Min | Task |
|-----|------|
| 0–5 | Fill placeholders; apt; Edge; timezone; `git clone <YOUR_GITHUB_REPO_URL>` |
| 5–10 | PostgreSQL; venv; uvicorn; login test |
| 10–15 | npm build; Nginx :80 |
| 15–20 | Extension time patch; Edge; Google login |
| 20–25 | Watcher; cron; first JSON |
| 25–30 | Upload to DB; local map UI |
| +DNS/TLS | Section 12 → `https://<YOUR_PUBLIC_HOSTNAME>` for the internet |

---

## 15) Troubleshooting

| Problem | Fix |
|---------|-----|
| serverTime vs person clock | Compare serverTime to host `date`, not to localTime |
| Old extension used fixed city TZ | Re-run section 7.2 |
| cron missing psycopg2 | Use venv python in crontab |
| Login bcrypt errors | Section 4 patch |
| HTTP 500 via tunnel | Forward map to **:80** |
| No JSON downloads | Edge GUI, Google login, reload extension |
| HTTPS not trusted | Finish DNS + certbot; check SAN matches hostname |
| dig wrong IP | Fix public A record / TTL |

---

## 16) Time summary (not hardcoded)

| Field | Source |
|--------|--------|
| **serverTime** | Public NTP-class HTTP API → format with **runtime OS timezone** |
| **localTime** | Location-share person time from **Google Maps page** |

---

**End.**  
1. Replace all `<YOUR_...>` placeholders.  
2. Run sections 0–11 for local install.  
3. Run section 12 for public `https://<YOUR_PUBLIC_HOSTNAME>`.  
4. Commit this file to your repo as `LOCATION_TRACKER_DEPLOYMENT.md` if desired.
