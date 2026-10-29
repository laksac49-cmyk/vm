# Podman Containers

| Host | Host IP | Container | Image | Services / Notes | Image Tag / Source |
|------|---------|-----------|-------|------------------|--------------------|
| ddserver11 | 192.168.10.101 | nginx-web | nginx:1.26 | HTTP/HTTPS 8080,8443 | localhost/datadisca-nginx:2026-10-03 |
| ddserver11 | 192.168.10.101 | coredns | coredns:1.11.3 | DNS 53 | localhost/datadisca-coredns:2026-10-03 |
| ddserver11 | 192.168.10.101 | postgres | postgres:16 | DB via apps-pod | localhost/datadisca-postgres:2026-10-03 |
| ddserver11 | 192.168.10.101 | matchmaking | python:3.12-slim | API 8001 | localhost/datadisca-matchmaking:2026-10-03 |
| ddserver14 | 192.168.10.104 | ubuntu-lxqt-01 | datadisca-ubuntu-lxqt-xrdp:26.04-2026-10-11 | LXQt/XRDP/SSH 192.168.220.104 4G/4c | 26.04-2026-10-11 |
| ddserver14 | 192.168.10.104 | ubuntu-ssh-02 | datadisca-ubuntu-ssh:26.04-2026-10-10 | SSH 192.168.220.106 4G/4c | 26.04-2026-10-10 |
| ddserver14 | 192.168.10.104 | rocky-ssh-01 | datadisca-rocky-ssh:10.2-2026-10-11 | SSH 192.168.220.107 4G/4c | 10.2-2026-10-11 |
| ddserver15 | 192.168.10.105 | ubuntu-lxqt-edge | datadisca-ubuntu-lxqt-xrdp:26.04-edge | SSH 22 + RDP 3389 | localhost/datadisca-ubuntu-lxqt-xrdp:26.04-edge |
| ddserver15 | 192.168.10.105 | rustdesk-hbbs | rustdesk/rustdesk-server:latest | ID/rendezvous 21115, 21116 tcp/udp, ws 21118; keys `/data/rustdesk` | docker.io/rustdesk/rustdesk-server:latest |
| ddserver15 | 192.168.10.105 | rustdesk-hbbr | rustdesk/rustdesk-server:latest | Relay 21117, ws 21119; keys `/data/rustdesk` | docker.io/rustdesk/rustdesk-server:latest |

## Notes (ddserver14)

- Network: macvlan `lan-macvlan` on br0
- Volume: `/data/pod_disks/<name>` → `/data`
- User: nma (sudo NOPASSWD)
- ubuntu-lxqt-01: SSH OK; RDP attach limited in Podman; GUI via Xvnc:5920 or use KVM

## Notes (ddserver15 – RustDesk, 2026-10-29)

- Rootful Podman (`sudo podman`), `--net=host`, `--restart=always`
- Volume: `/data/rustdesk` → `/root` (contains `id_ed25519` + `id_ed25519.pub`)
- hbbs command: `hbbs -r 192.168.10.105:21117`
- systemd units (enabled): `container-rustdesk-hbbs.service`, `container-rustdesk-hbbr.service`
- Client: ID server `192.168.10.105`, Key = public key file only
- Do not commit `id_ed25519` (private) to git

**Document updated:** 2026-10-29  
**Related:** `ip_usage.md`, `STATUS_2026_10_21_rustdesk_ddserver15.md`, `reusable_images_rapid_deploy.md`
