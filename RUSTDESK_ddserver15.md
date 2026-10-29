# RustDesk OSS on ddserver15 (Podman)

**Host:** 192.168.10.105 (ddserver15)  
**Updated:** 2026-10-29  
**Keys dir:** `/data/rustdesk`  
**Image:** `docker.io/rustdesk/rustdesk-server:latest` (pre-built; do not build from source)

---

## Containers

| Name | Role | Command | Network |
|------|------|---------|---------|
| rustdesk-hbbr | Relay | `hbbr` | host |
| rustdesk-hbbs | ID / rendezvous | `hbbs -r 192.168.10.105:21117` | host |

Volume (both): `/data/rustdesk:/root`

---

## One-shot create (rootful)

Run on ddserver15. Does **not** remove unrelated containers.

```bash
sudo mkdir -p /data/rustdesk
sudo ls -la /data/rustdesk

sudo podman pull docker.io/rustdesk/rustdesk-server:latest

sudo podman run -d \
  --name rustdesk-hbbr \
  --net=host \
  --restart=always \
  -v /data/rustdesk:/root:Z \
  docker.io/rustdesk/rustdesk-server:latest \
  hbbr

sudo podman run -d \
  --name rustdesk-hbbs \
  --net=host \
  --restart=always \
  -v /data/rustdesk:/root:Z \
  docker.io/rustdesk/rustdesk-server:latest \
  hbbs -r 192.168.10.105:21117
```

If `:Z` fails on non-SELinux hosts, use `-v /data/rustdesk:/root` only.

For **public** clients, replace `192.168.10.105` in `-r` with the public IP or DNS name.

---

## Verify

```bash
sudo podman ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
sudo podman logs --tail 30 rustdesk-hbbs
sudo podman logs --tail 30 rustdesk-hbbr
sudo ss -luntp | grep -E '21115|21116|21117'
sudo cat /data/rustdesk/id_ed25519.pub
```

---

## systemd (optional auto-start)

```bash
cd /tmp
sudo podman generate systemd --new --name rustdesk-hbbr --files
sudo podman generate systemd --new --name rustdesk-hbbs --files
sudo cp -v container-rustdesk-*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now container-rustdesk-hbbr.service container-rustdesk-hbbs.service
```

(Podman may print that `generate systemd` is deprecated in favour of Quadlets; units still work.)

---

## Client

| Field | Value |
|--------|--------|
| ID Server | `192.168.10.105` |
| Relay | empty or same host `:21117` |
| Key | public key only (`id_ed25519.pub`) |

Never put `id_ed25519` (private) in git or client config docs beyond secure storage.

---

## Firewall (if needed)

```bash
sudo firewall-cmd --permanent --add-port=21115/tcp
sudo firewall-cmd --permanent --add-port=21116/tcp
sudo firewall-cmd --permanent --add-port=21116/udp
sudo firewall-cmd --permanent --add-port=21117/tcp
sudo firewall-cmd --reload
```

---

**Related:** `ip_usage.md`, `podman_containers.md`, `STATUS_2026_10_21_rustdesk_ddserver15.md`
