# Todo Status – 2026-10-21 RustDesk on ddserver15

**Last updated:** 2026-10-29  
**Host:** ddserver15 (`192.168.10.105`)  
**Todo:** Add a RustDesk Podman container (pre-built image, not from scratch). Use keys at `/data/rustdesk`.

---

## Requirement

1. Server ddserver15 – 192.168.10.105  
2. Add RustDesk Podman container(s)  
3. Download container image (no compile-from-scratch)  
4. Use existing keys under `/data/rustdesk`

---

## Status: Done

| # | Item | Status | Notes |
|---|------|--------|--------|
| 1 | Keys present | Done | `/data/rustdesk/id_ed25519`, `id_ed25519.pub` |
| 2 | Image pull | Done | `docker.io/rustdesk/rustdesk-server:latest` |
| 3 | `rustdesk-hbbr` | Done | Relay, listen `:21117` |
| 4 | `rustdesk-hbbs` | Done | Rendezvous, listen `:21115` / `:21116`, key loaded from `id_ed25519` |
| 5 | Host networking | Done | `--net=host` |
| 6 | Data mount | Done | `-v /data/rustdesk:/root` |
| 7 | systemd enable | Done | `container-rustdesk-hbbr.service`, `container-rustdesk-hbbs.service` |
| 8 | Existing pods left alone | Done | e.g. `ubuntu-lxqt-edge` not removed |

---

## Runtime proof (2026-10-29)

```text
NAMES             STATUS    IMAGE
ubuntu-lxqt-edge  Up ...    localhost/datadisca-ubuntu-lxqt-xrdp:26.04-edge
rustdesk-hbbr     Up ...    docker.io/rustdesk/rustdesk-server:latest
rustdesk-hbbs     Up ...    docker.io/rustdesk/rustdesk-server:latest
```

hbbs log excerpt:

- Private key comes from `id_ed25519`
- Key: (public key from `/data/rustdesk/id_ed25519.pub`)
- Listening on tcp/udp `:21116`, tcp `:21115`
- relay-servers=`["192.168.10.105:21117"]`
- Start

hbbr log excerpt:

- Listening on tcp `:21117`
- Start

Ports observed: `21115/tcp`, `21116/tcp`, `21116/udp`, `21117/tcp`.

---

## Client configuration

| Field | Value |
|--------|--------|
| ID Server | `192.168.10.105` |
| Relay Server | empty or `192.168.10.105:21117` |
| Key | output of `cat /data/rustdesk/id_ed25519.pub` |

---

## Related docs

- `ip_usage.md` — host + service line  
- `podman_containers.md` — inventory rows  
- Official image docs: https://rustdesk.com/docs/en/self-host/rustdesk-server-oss/docker/

---

**End of STATUS_2026_10_21_rustdesk_ddserver15.md**
