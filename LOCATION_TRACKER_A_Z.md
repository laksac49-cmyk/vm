# Location Tracker — A–Z Portable Deploy Guide

**Goal:** Copy-paste these steps on any Ubuntu machine (bare metal, KVM guest, or Podman GUI container) and end with a working Location Tracker: Edge extension → JSON files → PostgreSQL → FastAPI → React map, optionally behind DNS + TLS.

**Rules**

- Replace every `<PLACEHOLDER>` before running.
- **Do not** commit passwords, tokens, or real repo URLs with embedded credentials.
- **Do not** hardcode city timezones in application JS (`Asia/Colombo`, `Australia/Sydney`, etc.).
- `server_time` = **OS wall-clock** of the app machine (naive). `local_time` = Maps UI person time only.
- Edit files with **terminal only** (`python3`, `sed`, `tee`). Avoid interactive editors if your ops policy requires it.

---

## Placeholders

| Placeholder | Meaning | Example shape only |
|-------------|---------|---------------------|
| `<YOUR_GITHUB_REPO_URL>` | Git clone URL of this / app repo | `https://github.com/<org>/<repo>.git` |
| `<YOUR_LINUX_USER>` | Login user on the app machine | `nma`, `ubuntu` |
| `<YOUR_APP_HOME>` | Usually `/home/<YOUR_LINUX_USER>` | `/home/nma` |
| `<YOUR_DB_NAME>` | PostgreSQL database | `location_tracker` |
| `<YOUR_DB_USER>` | DB user | `postgres` |
| `<YOUR_DB_PASS>` | DB password | *(Cliq notebook only)* |
| `<YOUR_APP_USER_EMAIL>` | Map UI login username | `user@example.com` |
| `<YOUR_APP_USER_PASS>` | Map UI login password | *(Cliq notebook only)* |
| `<YOUR_SECRET_KEY>` | JWT / FastAPI secret | long random string |
| `<YOUR_PUBLIC_HOSTNAME>` | FQDN for the map | `location1.int.example.com` |
| `<YOUR_PUBLIC_IP>` | Internet-facing IP of TLS edge | `x.x.x.x` |
| `<YOUR_APP_LAN_IP>` | App machine LAN IP (map :80, API :8080) | `192.168.220.113` |
| `<YOUR_APP_HOST_IP>` | Host that can reach app LAN (socat) | may equal proxy host |
| `<YOUR_LETSENCRYPT_EMAIL>` | ACME email | `ops@example.com` |
| `<YOUR_OS_TIMEZONE>` | `timedatectl` zone | `Australia/Sydney`, `UTC`, … |
| `<YOUR_DISPLAY>` | X11 display for Edge | `:0` or `:10` (XRDP) |
| `<YOUR_SHARED_MAPS_URL>` | Google Maps share URL opened in Edge | Maps URL |
| `<YOUR_INTERNAL_DNS_IP>` | Optional internal DNS | LAN DNS IP |
| `<YOUR_VM_NAME>` | Libvirt domain name | `ubuntu-lxqt-loc15` |
| `<YOUR_STATIC_IP>` | Guest static IP | `192.168.220.113` |
| `<YOUR_GATEWAY>` | Guest default gateway | `192.168.0.1` or host bridge GW |
| `<YOUR_DNS>` | Guest DNS | LAN DNS or public |
| `<YOUR_BRIDGE>` | Libvirt / host bridge | `br0`, `virbr0`, … |
| `<YOUR_VCPUS>` | vCPU count | `4` |
| `<YOUR_RAM_MIB>` | RAM MiB | `6144` (6 GB) |
| `<YOUR_DISK_GB>` | Disk size GB | `40` |
| `<YOUR_ISO_PATH>` | Ubuntu 26.04 live/server ISO path | `/data/iso/ubuntu-26.04-….iso` |

**Secrets:** store `<YOUR_DB_PASS>`, `<YOUR_APP_USER_PASS>`, `<YOUR_SECRET_KEY>` only in Cliq notebook / password manager — never in git.

---

## Part A — VM on a KVM host (ddserver-style)

Run on the **KVM host** (example: ddserver15).

### A1. Packages and network

```bash
sudo apt update
sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virtinst genisoimage
sudo systemctl enable --now libvirtd
```

Confirm bridge `<YOUR_BRIDGE>` exists and carries LAN traffic.

### A2. Create guest (Ubuntu 26.04, LXQt-capable, 6GB / 4 cores)

```bash
sudo virt-install \
  --name "<YOUR_VM_NAME>" \
  --memory "<YOUR_RAM_MIB>" \
  --vcpus "<YOUR_VCPUS>" \
  --disk path=/var/lib/libvirt/images/<YOUR_VM_NAME>.qcow2,size=<YOUR_DISK_GB>,format=qcow2 \
  --cdrom "<YOUR_ISO_PATH>" \
  --network bridge=<YOUR_BRIDGE>,model=virtio \
  --graphics vnc,listen=0.0.0.0 \
  --os-variant ubuntu24.04 \
  --noautoconsole
```

(Adjust `--os-variant` to the closest supported ID on your host.)

Install **Ubuntu 26.04 LTS**. Prefer minimal + later LXQt, or a desktop ISO then strip other desktops.

### A3. Inside guest — static IP, SSH, LXQt only, XRDP, Edge

```bash
# Static IP (netplan example — adapt interface name from ip link)
ip link
sudo tee /etc/netplan/01-static.yaml << EOF
network:
  version: 2
  ethernets:
    <YOUR_IFACE>:
      dhcp4: false
      addresses: [<YOUR_STATIC_IP>/16]
      routes:
        - to: default
          via: <YOUR_GATEWAY>
      nameservers:
        addresses: [<YOUR_DNS>]
EOF
sudo chmod 600 /etc/netplan/01-static.yaml
sudo netplan apply
ip -br a

# SSH
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh

# Timezone (ops — not app hardcode)
sudo timedatectl set-timezone "<YOUR_OS_TIMEZONE>"
timedatectl
date
date -u

# LXQt only (no GNOME / KDE / XFCE stacks)
sudo apt install -y lxqt sddm xorg
# If LXQt packages unavailable, XFCE4 is the documented fallback — then remove other DEs
sudo apt install -y xrdp
sudo systemctl enable --now xrdp
# Ensure xrdp starts an LXQt session (session file under /etc/xrdp or ~/.xsession)
echo "startlxqt" | sudo tee /etc/xrdp/startwm.sh.lxqt-hint
# Configure startwm.sh / .xsession to run startlxqt only

# Edge
curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
  | sudo gpg --dearmor -o /usr/share/keyrings/microsoft-edge.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-edge.gpg] https://packages.microsoft.com/repos/edge stable main" \
  | sudo tee /etc/apt/sources.list.d/microsoft-edge.list
sudo apt update
sudo apt install -y microsoft-edge-stable
```

Document actual IP, hostname, and XRDP port in `ip_usage.md`.

### A4. From LAN / jump host

```bash
ssh <YOUR_LINUX_USER>@<YOUR_STATIC_IP>
# RDP client → <YOUR_STATIC_IP>:3389
```

---

## Part B — Location Tracker software (on the app VM)

Set variables once:

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

### B1. Base packages

```bash
sudo apt update
sudo apt install -y \
  git curl wget ca-certificates \
  python3 python3-pip python3-venv python3-psycopg2 \
  postgresql postgresql-contrib \
  nginx nodejs npm socat
```

### B2. Clone code

```bash
cd "${APP_HOME}"
git clone "<YOUR_GITHUB_REPO_URL>" vm
cd vm && git checkout main && git pull origin main

rm -rf "${EXT_DIR}"
cp -a "${APP_HOME}/vm/location_trace" "${EXT_DIR}"

mkdir -p "${APP_DIR}"
# Copy the tree that contains main.py + React package.json into APP_DIR
# Example: cp -a "${APP_HOME}/vm/<BACKEND_FRONTEND_FOLDER>/." "${APP_DIR}/"
ls "${EXT_DIR}/content.js" "${EXT_DIR}/manifest.json"
```

### B3. PostgreSQL

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

### B4. FastAPI backend

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
chmod 600 "${APP_DIR}/.env"
```

**API time filter (critical):** `server_time` is naive OS wall-clock. Defaults must use `datetime.now()`, not `datetime.utcnow()`. Parse incoming `from_time` / `to_time` into naive local:

```text
default_from = datetime.now() - timedelta(hours=48)
default_to   = datetime.now() + timedelta(minutes=5)
# Parse client strings; if tz-aware, convert to OS local then drop tzinfo
```

Patch `main.py` with terminal `python3` if the cloned file still uses `utcnow()`.

Create map login user (bcrypt) and start API:

```bash
# Insert user via short Python (see location_tracker_install.md pattern)
# Prefer systemd unit location-tracker.service → uvicorn main:app --host 0.0.0.0 --port 8080
sudo systemctl enable --now location-tracker.service
# Or: nohup uvicorn ... &
curl -s -o /dev/null -w "docs:%{http_code}\n" http://127.0.0.1:8080/docs
```

### B5. React map — time filter rules

**Wrong:** `filters.from/to = new Date().toISOString()` (UTC `Z`) while `server_time` is naive server wall-clock.

**Right:**

1. Format defaults with **local numeric components** (`YYYY-MM-DD HH:MM:SS`), not `toISOString()`.
2. Because **browser TZ ≠ server TZ**, pad default **`to` by +14 hours** (covers typical offsets without hardcoding a city).
3. `FilterBar`: send the datetime-local / formatted string **as-is** to the API (do not `toISOString()`).
4. `BatteryChart`: parse `fromDate` / `toDate` with the **same** naive parser as `server_time` (`parseServerTime`); optionally widen `to` by +14h again client-side.

Build and publish:

```bash
cd "${APP_DIR}"
npm install
npm run build
sudo mkdir -p /var/www/location-tracker
sudo rsync -a --delete build/ /var/www/location-tracker/
sudo chown -R www-data:www-data /var/www/location-tracker
```

### B6. Nginx on app machine (HTTP)

```bash
sudo tee /etc/nginx/sites-available/location-tracker << EOF
server {
    listen 80;
    server_name ${MAP_HOSTNAME} _;
    root /var/www/location-tracker;
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
sudo nginx -t && sudo systemctl restart nginx
curl -s -o /dev/null -w "map:%{http_code}\n" http://127.0.0.1/
```

### B7. Extension time model

Full procedure: **Part T** (public NTP `serverTime` + Maps person `localTime`, no city hardcode).

Reload extension in Edge after deploy.

### B8. Upload pipeline + cron

```bash
mkdir -p "${APP_HOME}/incoming" "${APP_HOME}/processed" "${APP_HOME}/logs" "${APP_HOME}/Downloads/done"

# auto_upload_watcher.sh: move LatLong_*.json from Downloads → incoming
# upload_json.py: insert into location_data (DB_* from env), move to processed

# Cron (example — inject real paths; DB env on upload line)
crontab -l > /tmp/cron.full 2>/dev/null || true
grep -v 'upload_json.py\|auto_upload_watcher' /tmp/cron.full > /tmp/cron.new || true
cat >> /tmp/cron.new << EOF
* * * * * ${APP_HOME}/auto_upload_watcher.sh >> ${APP_HOME}/logs/watcher.log 2>&1
* * * * * DB_NAME=${DB_NAME} DB_USER=${DB_USER} DB_PASS=${DB_PASS} ${APP_DIR}/venv/bin/python3 ${APP_HOME}/upload_json.py >> ${APP_HOME}/logs/upload_json.log 2>&1
EOF
crontab /tmp/cron.new
sudo systemctl enable --now cron
crontab -l
```

### B9. Edge launcher (GUI)

Use a script with `DISPLAY=<YOUR_DISPLAY>`, `--load-extension=${EXT_DIR}`, and `<YOUR_SHARED_MAPS_URL>`. Optional autostart `.desktop` under `~/.config/autostart`.

---

## Part T — Server time (public NTP) + local time (shared person) — no city hardcode

### T0. Two different clocks (do not mix them)

| Field | Meaning | Source | Forbidden |
|-------|---------|--------|-----------|
| **server_time** / `serverTime` | Reference time on the **app / capture machine** | Public NTP-style HTTP API returns a **UTC instant**; format it at runtime with the **OS timezone** of the machine running Edge (`Intl.DateTimeFormat().resolvedOptions().timeZone`) | Hardcoded `Asia/Colombo`, `Australia/Sydney`, fixed offsets, appending `Z` when storing wall-clock for filters |
| **local_time** / `localTime` | Time of the **person** whose location is shared | Scrape only from the Google Maps share UI | Inventing person time from server clock or from browser `Date` |

**Physical server OS clock** (for logs, `date`, cron): set with `timedatectl` + NTP (systemd-timesyncd / chrony). That is **ops**, not application source code.

**Application rule:** never bake a city name into JS/Python for these two fields.

---

### T1. Physical server / VM — sync OS clock to public NTP (ops)

Run on the **app machine** (the VM that runs Edge + upload).

```bash
# Show current state
timedatectl
date
date -u

# Set the zone operators want for wall-clock display on THIS machine
sudo timedatectl set-timezone "<YOUR_OS_TIMEZONE>"

# Enable NTP (Ubuntu typically uses systemd-timesyncd)
sudo timedatectl set-ntp true
timedatectl status

# Optional: chrony instead
# sudo apt install -y chrony
# sudo systemctl enable --now chrony
# chronyc tracking

# Confirm
date
date -u
timedatectl
```

Containers sometimes cannot run chronyd; that is OK. The **extension** still gets UTC from public HTTP time APIs and formats with the container/VM OS TZ via `Intl`.

---

### T2. Extension — public NTP to serverTime (system TZ) + Maps to localTime

Work in `${EXT_DIR}` (usually `~/Location_Trace`). Terminal-only edits.

#### T2.1 Manifest host permissions (Maps only)

```bash
cd "${EXT_DIR}"
cp -a manifest.json "manifest.json.bak_$(date +%Y%m%d%H%M%S)"
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
print("OK manifest maps matches")
PY
```

If the extension must call public time APIs from the content script and the browser blocks them, add those HTTPS origins to `host_permissions` as well (still no city TZ strings):

- `https://worldtimeapi.org/*`
- `https://timeapi.io/*`

#### T2.2 Replace the time block in content.js

Logic:

1. `scrapeLocalTime()` returns raw person time from Maps DOM.
2. Fetch UTC from public APIs (`worldtimeapi.org`, `timeapi.io`, ...).
3. `formatInstantInSystemTz(utcIso)` uses **runtime** `Intl` and `resolvedOptions().timeZone` (whatever the OS is set to in T1).
4. `localTimeFromPage(raw, serverTs)` builds person local date using clock time from Maps plus calendar day from serverTime when needed.
5. Fallback if NTP HTTP fails: `formatInstantInSystemTz(new Date().toISOString())` (still system TZ, not a city constant).

```bash
cd "${EXT_DIR}"
cp -a content.js "content.js.bak_time_$(date +%Y%m%d_%H%M%S)"
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
    raise SystemExit("Could not find time block in content.js — inspect fetchData() and adjust markers")

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

# Guard: no city timeZone: '...' hardcode left in content.js
grep -nE "timeZone:\s*['\"][A-Za-z]+/" "${EXT_DIR}/content.js" \
  && echo "WARN: possible city timeZone hardcode still present" \
  || echo "OK: no city timeZone hardcode pattern"
```

#### T2.3 After patch

1. Edge → `edge://extensions` → **Reload** the tracker extension.
2. Open the shared Maps URL; wait for a new `LatLong_*.json` download.
3. Inspect JSON:

```bash
NEW=$(ls -t ${APP_HOME}/Downloads/LatLong_*.json ${APP_HOME}/Downloads/done/LatLong_*.json 2>/dev/null | head -1)
python3 -m json.tool "$NEW" | head -50
# Expect: serverTime like "YYYY-MM-DD HH:MM:SS" (machine wall clock from NTP+Intl)
# Expect: localTime from the shared person UI (not identical to serverTime unless coincidence)
```

---

### T3. Database + upload path

- Column `server_time` = `TIMESTAMP WITHOUT TIME ZONE` (naive wall-clock from extension).
- Column `local_time` = text from Maps person time.
- `upload_json.py` must parse `serverTime` / `server_time` as naive local, **not** force UTC via `datetime.utcnow()` when a value is present.

---

### T4. API + React filters (same wall-clock)

- FastAPI defaults: `datetime.now()` (OS local), not `utcnow()`.
- React: send naive `YYYY-MM-DD HH:MM:SS`; do not use `toISOString()` for filter params.
- Browser TZ may differ from server TZ: pad default `to` by **+14 hours** (see Part B5).

---

### T5. Verify end-to-end

```bash
# OS
timedatectl; date; date -u

# Latest DB rows
PGPASSWORD="<YOUR_DB_PASS>" psql -h 127.0.0.1 -U "<YOUR_DB_USER>" -d "<YOUR_DB_NAME>" -c \
  "SELECT server_time, local_time, battery_level, google_account
   FROM location_data ORDER BY server_time DESC LIMIT 5;"

# server_time should track app-machine wall clock (NTP-based via extension)
# local_time should match what you see on the Maps share for that person
```

---

### T6. Common failures

| Problem | Fix |
|---------|-----|
| `serverTime` stuck or wrong zone | T1 `timedatectl`; reload extension; check NTP HTTP not blocked |
| City name still in `content.js` | Remove `timeZone: "Asia/..."`; use `resolvedOptions().timeZone` only |
| `localTime` always `N/A` | Maps DOM scrape selectors changed — fix `scrapeLocalTime()` only |
| Chart/API drop new rows | Part B5 / Part D filter TZ mismatch, not NTP itself |

---

'''

marker = "## Part C — DNS + reverse proxy + TLS"

## Part C — DNS + reverse proxy + TLS

### C1. Internal DNS (CoreDNS / hosts on LAN DNS host)

Add A/AAAA or hosts line:

```text
<YOUR_APP_LAN_IP>   <YOUR_PUBLIC_HOSTNAME>
```

Or point hostname at the **TLS proxy** host if Layout B.

```bash
dig @"<YOUR_INTERNAL_DNS_IP>" "<YOUR_PUBLIC_HOSTNAME>" +short
```

### C2. Public DNS

| Type | Name | Value |
|------|------|--------|
| A | `<YOUR_PUBLIC_HOSTNAME>` | `<YOUR_PUBLIC_IP>` |

```bash
dig +short "<YOUR_PUBLIC_HOSTNAME>"
```

### C3. Layout B — socat on proxy-adjacent host

Forward public/proxy ports to app LAN `:80` and `:8080` (example ports 18081/18080). Use systemd units with `Restart=always`.

### C4. TLS Nginx (on edge that holds the cert)

- `proxy_pass` to app map and `/api/`.
- Let’s Encrypt: `certbot --nginx` or webroot; enable `certbot.timer`.
- Do **not** expose PostgreSQL `5432` or Edge debug `9222` to the internet.

---

## Part D — Server time / local time / filter troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| API has new rows; chart stops yesterday | Browser TZ ≠ server TZ; `to` too early | +14h on default `to`; naive filter strings |
| API returns few rows with no query params | Backend used `utcnow()` vs naive `server_time` | `datetime.now()` defaults in `main.py` |
| Chart filters out valid points | Client parsed filters as UTC, `server_time` as local | Same `parseServerTime` for from/to/data |
| `toISOString()` in FilterBar | Forces UTC `Z` | Send local-format string only |

**Verify on app VM:**

```bash
date; timedatectl
PGPASSWORD="<YOUR_DB_PASS>" psql -h 127.0.0.1 -U "<YOUR_DB_USER>" -d "<YOUR_DB_NAME>" \
  -c "SELECT server_time, local_time, battery_level FROM location_data ORDER BY server_time DESC LIMIT 5;"

TOKEN=$(curl -s -X POST http://127.0.0.1:8080/api/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=<YOUR_APP_USER_EMAIL>&password=<YOUR_APP_USER_PASS>' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s "http://127.0.0.1:8080/api/location-data" -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d), d[-1].get('server_time') if d else None)"
```

Browser: hard refresh (Ctrl+Shift+R); Network tab → `location-data` → confirm `from_time` / `to_time` have **no** forced UTC skew.

---

## Part E — Cleanup (all machines)

```bash
# Each Podman host
podman container prune -f
podman image prune -a -f

# Each libvirt host
sudo virsh list --all
# Remove only confirmed unused domains/images
```

Update `ip_usage.md` when IPs change.

---

## Part F — What to commit to GitHub

| File | Action |
|------|--------|
| `ip_usage.md` | Add app VM row + hostname notes |
| `STATUS_2026_10_28_location_ddserver15.md` | Todo completion proof |
| `LOCATION_TRACKER_A_Z.md` | This portable guide |
| Application source | Time-filter fixes (no secrets) |
| **Never** | `.env`, real passwords, Cliq contents |

```bash
cd /path/to/vm-repo
# copy updated md files into repo root
git add ip_usage.md STATUS_2026_10_28_location_ddserver15.md LOCATION_TRACKER_A_Z.md
git status
git commit -m "docs: location tracker on ddserver15 + portable A-Z + ip_usage"
git push origin main
```

---

## Part G — Other Grok chats

Work done in **another** Grok conversation is not automatically visible here.

**What you can do:**

1. Download these artifact `.md` files and commit them to GitHub (source of truth).
2. In a new chat, paste the STATUS table or link the repo file.
3. Keep Cliq notebook for passwords only; keep runbooks in git with placeholders.
4. Prefer one `LOCATION_TRACKER_A_Z.md` as the install bible so any machine can be rebuilt without chat history.

---

## Quick inventory (reference deployment)

| Item | Reference value (this environment) |
|------|-------------------------------------|
| KVM host | ddserver15 `192.168.10.105` |
| Guest | `ubuntu-lxqt-loc15` `192.168.220.113` |
| Specs | 6GB / 4 cores, Ubuntu 26.04, LXQt, XRDP, Edge |
| URL | `https://location1.int.datadisca.com` |
| App dir | `/home/nma/my-map-app` |
| Static | `/var/www/location-tracker` |
| API | `127.0.0.1:8080` |

Replace with your placeholders on the next install.

---

**End of LOCATION_TRACKER_A_Z.md**
