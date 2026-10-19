# Podman Containers

| Host | Host IP | Container | Image | Services / Notes | Image Tag |
|------|---------|-----------|-------|------------------|-----------|
| ddserver11 | 192.168.10.101 | nginx-web | nginx:1.26 | HTTP/HTTPS 8080,8443 | localhost/datadisca-nginx:2026-10-03 |
| ddserver11 | 192.168.10.101 | coredns | coredns:1.11.3 | DNS 53 | localhost/datadisca-coredns:2026-10-03 |
| ddserver11 | 192.168.10.101 | postgres | postgres:16 | DB via apps-pod | localhost/datadisca-postgres:2026-10-03 |
| ddserver11 | 192.168.10.101 | matchmaking | python:3.12-slim | API 8001 | localhost/datadisca-matchmaking:2026-10-03 |
| ddserver14 | 192.168.10.104 | ubuntu-lxqt-01 | datadisca-ubuntu-lxqt-xrdp:26.04-2026-10-11 | XFCE+XRDP+SSH 192.168.220.104 4G/4c | 26.04-2026-10-11 |
| ddserver14 | 192.168.10.104 | ubuntu-ssh-02 | datadisca-ubuntu-ssh:26.04-2026-10-10 | SSH 192.168.220.106 4G/4c | 26.04-2026-10-10 |
| ddserver14 | 192.168.10.104 | rocky-ssh-01 | datadisca-rocky-ssh:10.2-2026-10-11 | SSH 192.168.220.107 4G/4c | 10.2-2026-10-11 |

## Notes (ddserver14)

- Network: macvlan `lan-macvlan` on br0
- Volume: `/data/pod_disks/<name>` → `/data`
- User: nma (sudo NOPASSWD)
- ubuntu-lxqt-01: SSH OK; RDP attach limited in Podman; GUI via Xvnc:5920 or use KVM

**Document updated:** 2026-10-17  
**Related:** `2026_10_10_todoproof.md`, `reusable_images_rapid_deploy.md`
