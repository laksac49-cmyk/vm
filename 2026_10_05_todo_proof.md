# DataDisca Migration — 2026-10-05 Todo Proof

**Last updated:** 2026-10-06  
**Purpose:** Correct commands only — prove each 2026-10-05 todo is done.  
**Run on:** server named in each section.

---

## Login path

```bash
# From office PC → dating jump host
ssh -p 3422 lahiru@Sr.datadisca.com

# → ddserver11
ssh nma@192.168.10.101

# → ddserver11_vm1 (from ddserver11)
sudo ip route replace 192.168.220.11/32 dev br0
ssh nma@192.168.220.11
```

| Host              | IP             | Role                               |
| ----------------- | -------------- | ---------------------------------- |
| ddserver11        | 192.168.10.101 | Main (Nginx, DNS, apps)            |
| ddserver11_vm1    | 192.168.220.11 | New jump / test client             |
| Dating (old jump) | 192.168.13.104 | SSH entry: `Sr.datadisca.com:3422` |

---

## Todo status

| # | Task | Status |
| --- | --- | --- |
| 1 | Point `mm.int` / `pinokio.int` / `fooocus.int.datadisca.com` → **115.186.215.191** (DNS pod + public) | ✅ Done |
| 2 | Valid certificate for int family (`mm` / `pinokio` / `fooocus`) | ✅ Done |
| 3 | Renew `datadisca.com` + `tmgpm.com.au`; auto-update on new Nginx | ✅ **Done** |

---

## Todo 1 — Point mm / pinokio / fooocus.int → 115.186.215.191

**Server:** ddserver11 (`192.168.10.101`)

### 1a. DNS pod listening on port 53

```bash
podman ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep -E 'coredns|dns'
ss -tulnp | grep '192.168.10.101:53'
```

**Pass:**
```text
coredns ... 192.168.10.101:53->53/udp, 192.168.10.101:53->53/tcp
udp/tcp LISTEN on 192.168.10.101:53
```

### 1b. DNS pod answers

```bash
dig @192.168.10.101 mm.int.datadisca.com +short
dig @192.168.10.101 pinokio.int.datadisca.com +short
dig @192.168.10.101 fooocus.int.datadisca.com +short
```

**Pass:** all three → `115.186.215.191`

### 1c. Public DNS (do **not** use `127.0.0.53`)

```bash
dig @8.8.8.8 mm.int.datadisca.com +short
dig @1.1.1.1 pinokio.int.datadisca.com +short
dig @8.8.8.8 fooocus.int.datadisca.com +short
```

**Pass:** all three → `115.186.215.191`

### 1d. HTTPS from ddserver11 (local — avoid hairpin NAT)

Direct `curl https://mm.int...` → **000** (hairpin). Use `--resolve`:

```bash
curl -sk -o /dev/null -w "mm:%{http_code}\n" \
  --resolve mm.int.datadisca.com:443:127.0.0.1 \
  https://mm.int.datadisca.com/

curl -sk -o /dev/null -w "pinokio:%{http_code}\n" \
  --resolve pinokio.int.datadisca.com:443:127.0.0.1 \
  https://pinokio.int.datadisca.com/

curl -sk -o /dev/null -w "fooocus:%{http_code}\n" \
  --resolve fooocus.int.datadisca.com:443:127.0.0.1 \
  https://fooocus.int.datadisca.com/

curl -sk -o /dev/null -w "mm-lan:%{http_code}\n" \
  --resolve mm.int.datadisca.com:443:192.168.10.101 \
  https://mm.int.datadisca.com/
```

**Pass:** `mm:302` (or 200); `pinokio`/`fooocus` = **200** or **401** (401 OK if basic auth); `mm-lan:302` (or 200)

> pinokio/fooocus basic auth: 401 without login proves Nginx is up. For 200 use `-u 'tlk:...'` or `-u 'nma:...'`.

### Recorded proof (2026-10-06)

```text
DNS pod + public dig → 115.186.215.191 (all three)
HTTPS local: mm:302  pinokio/fooocus:200 (or 401 with auth)
```

---

## Todo 2 — Certificate valid for int family

**Server:** ddserver11

### 2a. TLS inspect (local — avoid hairpin)

```bash
echo | openssl s_client -connect 127.0.0.1:443 \
  -servername mm.int.datadisca.com 2>/dev/null \
  | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

**Pass:**
```text
subject=CN=mm.int.datadisca.com
issuer=C=US, O=Let's Encrypt, CN=YE2
notBefore=Oct  5 08:52:18 2026 GMT
notAfter=Jan  3 08:52:17 2027 GMT
SAN: DNS:fooocus.int.datadisca.com, DNS:mm.int.datadisca.com, DNS:pinokio.int.datadisca.com
```

### 2b. Cert files + Nginx config

```bash
ls /opt/podman-nginx/letsencrypt/live/
grep -R "mm.int.datadisca.com\|ssl_certificate" /opt/podman-nginx/nginx/sites-enabled/ 2>/dev/null | head -20
```

**Pass:**
```text
live/ includes: mm.int.datadisca.com
int.datadisca.com.conf uses:
  ssl_certificate     .../live/mm.int.datadisca.com/fullchain.pem
  ssl_certificate_key .../live/mm.int.datadisca.com/privkey.pem
```

### Recorded proof (2026-10-06, ddserver11)

```text
openssl (127.0.0.1:443 + SNI) → LE cert, SAN all three, expires 2027-01-03
ls live/ → mm.int.datadisca.com present
nginx → int.datadisca.com.conf points at that cert
```

---

## Todo 3 — Renew datadisca.com & tmgpm.com.au; auto-update on new Nginx

**Server:** ddserver11

### 3a. Certbot installed + linked to Podman cert tree

```bash
certbot --version
# → certbot 4.0.0

ls -la /etc/letsencrypt
# → symlink → /opt/podman-nginx/letsencrypt

sudo certbot certificates
```

**Pass:** certbot present; live certs listed under linked tree.

### 3b. ACME webroot works (HTTP-01)

Webroot: `/opt/podman-nginx/www` (container path `/var/www`).  
Nginx `location ^~ /.well-known/acme-challenge/` uses `root /var/www;` (not `/var/www/html`).

```bash
echo ok | sudo tee /opt/podman-nginx/www/.well-known/acme-challenge/ping

for h in datadisca.com www.datadisca.com tmgpm.com.au webtest.datadisca.com \
         ai.datadisca.com mm.int.datadisca.com pinokio.int.datadisca.com \
         fooocus.int.datadisca.com sr.datadisca.com; do
  code=$(curl -s -o /tmp/acme_body -w "%{http_code}" --resolve "${h}:80:127.0.0.1" \
    "http://${h}/.well-known/acme-challenge/ping")
  body=$(cat /tmp/acme_body 2>/dev/null | tr -d '\n')
  echo "$h → $code body=$body"
done
```

**Pass:** all → **200** body=`ok`  
(pinokio/fooocus: `auth_basic off` inside acme location)

### 3c. Cert dates (PEM)

```bash
sudo openssl x509 -in /opt/podman-nginx/letsencrypt/live/datadisca.com/fullchain.pem -noout -dates
sudo openssl x509 -in /opt/podman-nginx/letsencrypt/live/tmgpm.com.au/fullchain.pem -noout -dates
```

**Pass (recorded 2026-10-06):**
```text
datadisca.com  notBefore=Oct  6 02:33:05 2026 GMT  notAfter=Jan  4 02:33:04 2027 GMT  ✅ force-renewed
tmgpm.com.au   notBefore=Oct  5 09:43:07 2026 GMT  notAfter=Jan  3 09:43:06 2027 GMT  ✅
```

### 3d. Auto-renew dry-run (all active certs)

```bash
sudo certbot renew --cert-name datadisca.com --dry-run
sudo certbot renew --cert-name tmgpm.com.au --dry-run
sudo certbot renew --dry-run
```

**Pass (recorded 2026-10-06):**
```text
Congratulations, all simulated renewals succeeded:
  /etc/letsencrypt/live/ai.datadisca.com/fullchain.pem (success)
  /etc/letsencrypt/live/datadisca.com/fullchain.pem (success)
  /etc/letsencrypt/live/mm.int.datadisca.com/fullchain.pem (success)
  /etc/letsencrypt/live/sr.datadisca.com/fullchain.pem (success)
  /etc/letsencrypt/live/tmgpm.com.au/fullchain.pem (success)
  /etc/letsencrypt/live/webtest.datadisca.com/fullchain.pem (success)
```

### 3e. Timer + deploy hook

```bash
systemctl list-timers | grep certbot
ls -la /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
# contents: podman exec nginx-web nginx -s reload || true
```

**Pass:** `certbot.timer` enabled; deploy hook executable; reloads nginx-web after renew.

### Renewal config notes

| Cert | authenticator | webroot_path |
| ---- | ------------- | ------------ |
| datadisca.com | webroot | `/opt/podman-nginx/www` |
| tmgpm.com.au | webroot | `/opt/podman-nginx/www` |
| ai / webtest / mm.int / sr | webroot | `/opt/podman-nginx/www` |

`/etc/letsencrypt` → symlink to `/opt/podman-nginx/letsencrypt` (same volume nginx-web mounts).

### Recorded proof (2026-10-06)

```text
certbot 4.0.0 installed; /etc/letsencrypt → /opt/podman-nginx/letsencrypt
datadisca.com force-renewed → expires 2027-01-04
tmgpm.com.au valid → expires 2027-01-03
ACME challenge 200/ok for all listed hosts (incl. sr, pinokio, fooocus)
certbot renew --dry-run → 6/6 success
certbot.timer + reload-nginx.sh deploy hook in place
```

---

## One-shot — all three todos (ddserver11)

```bash
echo "=== T1 DNS pod ==="
podman ps --format 'table {{.Names}}\t{{.Ports}}' | grep -E 'coredns|dns'
ss -tulnp | grep '192.168.10.101:53' | head -2
for h in mm pinokio fooocus; do
  echo -n "$h.int: "
  dig @192.168.10.101 ${h}.int.datadisca.com +short
done
dig @8.8.8.8 mm.int.datadisca.com +short
dig @1.1.1.1 pinokio.int.datadisca.com +short
dig @8.8.8.8 fooocus.int.datadisca.com +short

echo "=== T1 HTTPS local ==="
curl -sk -o /dev/null -w "mm:%{http_code}\n" \
  --resolve mm.int.datadisca.com:443:127.0.0.1 https://mm.int.datadisca.com/
curl -sk -o /dev/null -w "pinokio:%{http_code}\n" \
  --resolve pinokio.int.datadisca.com:443:127.0.0.1 https://pinokio.int.datadisca.com/
curl -sk -o /dev/null -w "fooocus:%{http_code}\n" \
  --resolve fooocus.int.datadisca.com:443:127.0.0.1 https://fooocus.int.datadisca.com/

echo "=== T2 cert ==="
echo | openssl s_client -connect 127.0.0.1:443 \
  -servername mm.int.datadisca.com 2>/dev/null \
  | openssl x509 -noout -subject -dates -ext subjectAltName
ls /opt/podman-nginx/letsencrypt/live/

echo "=== T3 certbot + dates + renew dry-run ==="
certbot --version
sudo openssl x509 -in /opt/podman-nginx/letsencrypt/live/datadisca.com/fullchain.pem -noout -dates
sudo openssl x509 -in /opt/podman-nginx/letsencrypt/live/tmgpm.com.au/fullchain.pem -noout -dates
sudo certbot renew --dry-run
systemctl list-timers | grep certbot
```

---

## Notes

| Item | Detail |
| ---- | ------ |
| Direct connect to public IP from ddserver11 → fail / 000 | Hairpin NAT — use `127.0.0.1` or `--resolve` |
| `dig` without `@server` times out on `127.0.0.53` | Host resolver issue — ignore |
| pinokio/fooocus basic auth | 401 without login OK; users `tlk` / `nma`; ACME uses `auth_basic off` |
| ACME webroot | Host `/opt/podman-nginx/www` = container `/var/www` |
| `int.datadisca.com` / `datadisca.com` via DNS pod → `192.168.10.101` | LAN map — not Todo 1 |
| hikkainfo.com | Skipped / renewal disabled by design |

---

**End of 2026_10_05_todoProof.md**
