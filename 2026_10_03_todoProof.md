
# DataDisca Migration — 2026-10-05 Todo Proof

**Last updated:** 2026-10-07  
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

| Host | IP | Role |
| --- | --- | --- |
| ddserver11 | 192.168.10.101 | Main (Nginx, DNS, apps) |
| ddserver11_vm1 | 192.168.220.11 | New jump / test client |
| Dating (old jump) | 192.168.13.104 | SSH entry: `Sr.datadisca.com:3422` |

---

## Todo status

| # | Task | Status |
| --- | --- | --- |
| 1 | Point `mm.int` / `pinokio.int` / `fooocus.int.datadisca.com` → **115.186.215.191** (DNS pod + public) | Done |
| 2 | Valid certificate for int family (`mm` / `pinokio` / `fooocus`) | Done |
| 3 | Renew `datadisca.com` + `tmgpm.com.au`; auto-update on new Nginx | Done |

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
**Fail:** empty, NXDOMAIN, or `192.168.10.101`

### 1c. Public DNS (do not use host `127.0.0.53`)

```bash
dig @8.8.8.8 mm.int.datadisca.com +short
dig @1.1.1.1 pinokio.int.datadisca.com +short
dig @8.8.8.8 fooocus.int.datadisca.com +short
```

**Pass:** all three → `115.186.215.191`

### 1d. HTTPS from ddserver11 (local — avoid hairpin NAT)

Direct `curl https://mm.int...` from this host often returns **000** (hairpin). Use `--resolve`:

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
```

**Pass:** `mm` = 302 or 200; `pinokio` / `fooocus` = 200 or **401** (401 is OK if basic auth is enabled)

### 1e. Internet verification (browser / online tools)

| Check | Link / action | Expected |
| --- | --- | --- |
| Open site | https://mm.int.datadisca.com/ | Matchmaking loads |
| Open site | https://pinokio.int.datadisca.com/ | Login prompt, then Pinokio |
| Open site | https://fooocus.int.datadisca.com/ | Login prompt, then Fooocus |
| DNS global | https://dnschecker.org/#A/mm.int.datadisca.com | A = `115.186.215.191` |
| DNS global | https://dnschecker.org/#A/pinokio.int.datadisca.com | A = `115.186.215.191` |
| DNS global | https://dnschecker.org/#A/fooocus.int.datadisca.com | A = `115.186.215.191` |
| Google Dig | https://toolbox.googleapps.com/apps/dig/#A/mm.int.datadisca.com | A = `115.186.215.191` |

### Recorded proof (2026-10-06)

```text
DNS pod + public dig → 115.186.215.191 (all three)
HTTPS local: mm:302  pinokio/fooocus:200 or 401
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
issuer=... Let's Encrypt ...
notBefore=Oct  5 ... 2026
notAfter=Jan  3 ... 2027
SAN: DNS:fooocus.int.datadisca.com, DNS:mm.int.datadisca.com, DNS:pinokio.int.datadisca.com
```

### 2b. Cert files + Nginx config

```bash
ls /opt/podman-nginx/letsencrypt/live/
grep -R "mm.int.datadisca.com\|ssl_certificate" /opt/podman-nginx/nginx/sites-enabled/ 2>/dev/null | head -20
```

**Pass:** `live/` includes `mm.int.datadisca.com`; nginx uses that cert.

### Recorded proof (2026-10-06)

```text
LE cert, SAN all three, expires 2027-01-03
```

---

## Todo 3 — Renew datadisca.com and tmgpm.com.au; auto-update

**Server:** ddserver11

### 3a. Certbot installed

```bash
certbot --version
# → certbot 4.0.0

ls -la /etc/letsencrypt
# → symlink to /opt/podman-nginx/letsencrypt
```

### 3b. Cert dates (PEM)

```bash
sudo openssl x509 -in /opt/podman-nginx/letsencrypt/live/datadisca.com/fullchain.pem -noout -dates
sudo openssl x509 -in /opt/podman-nginx/letsencrypt/live/tmgpm.com.au/fullchain.pem -noout -dates
```

**Pass (recorded 2026-10-06):**

```text
datadisca.com  notBefore=Oct  6 2026  notAfter=Jan  4 2027   force-renewed
tmgpm.com.au   notBefore=Oct  5 2026  notAfter=Jan  3 2027   valid
```

### 3c. ACME webroot check

```bash
echo ok | sudo tee /opt/podman-nginx/www/.well-known/acme-challenge/ping

curl -s --resolve datadisca.com:80:127.0.0.1 \
  http://datadisca.com/.well-known/acme-challenge/ping
# → ok
```

### 3d. Auto-renew dry-run (all)

```bash
sudo certbot renew --dry-run
systemctl list-timers | grep certbot
ls -la /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
```

**Pass (recorded 2026-10-06):**

```text
all simulated renewals succeeded:
  ai.datadisca.com, datadisca.com, mm.int.datadisca.com,
  sr.datadisca.com, tmgpm.com.au, webtest.datadisca.com
certbot.timer enabled
deploy hook reloads nginx-web
```

### Recorded proof (2026-10-06)

```text
certbot installed; webroot /opt/podman-nginx/www
datadisca renewed → 2027-01-04
tmgpm valid → 2027-01-03
renew --dry-run → 6/6 success
```

---

## One-shot — all three todos (ddserver11)

```bash
echo "=== T1 DNS ==="
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

echo "=== T3 certbot ==="
certbot --version
sudo openssl x509 -in /opt/podman-nginx/letsencrypt/live/datadisca.com/fullchain.pem -noout -dates
sudo openssl x509 -in /opt/podman-nginx/letsencrypt/live/tmgpm.com.au/fullchain.pem -noout -dates
sudo certbot renew --dry-run
systemctl list-timers | grep certbot
```

---

## Notes

| Item | Detail |
| --- | --- |
| Hairpin NAT | From ddserver11, curl to public IP may return 000 — use `--resolve` or `127.0.0.1` |
| Host dig without `@server` | May timeout on `127.0.0.53` — use `@192.168.10.101` or `@8.8.8.8` |
| pinokio / fooocus auth | 401 without login is OK; users `tlk` / `nma` |
| ACME webroot | Host `/opt/podman-nginx/www` = container `/var/www` |
| Old 2026-10-03 expectation | `mm.int` → `192.168.10.101` is **superseded**; public target is now `115.186.215.191` |

---

**End of 2026_10_05_todoProof.md**
