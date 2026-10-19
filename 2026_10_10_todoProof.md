# DataDisca Migration — 2026-10-10 Todo Proof

**Last updated:** 2026-10-17  
**Primary server:** ddserver14 (`192.168.10.104`)  
**Purpose:** Practice spins — reusable images and rapid deployment (not production cutover).

---

## Todo status

| # | Task | Status |
|---|------|--------|
| 1 | Podman: Ubuntu 26.04 + desktop + XRDP + SSH + Static IP + 4GB/4c + /data + reusable image | Done |
| 2 | Podman: Ubuntu 26.04 SSH-only + Static IP + 4GB/4c + /data + reusable image | Done |
| 3 | Podman: Rocky Linux 10.2 minimal + SSH + Static IP + 4GB/4c + /data + reusable image | Done |
| 4 | Reusable KVM image: Rocky Linux minimal + SSH | Done (rocky-ssh-template) |
| 5 | Reusable KVM image: Ubuntu latest LTS + LXQt only + SSH | Done (ubuntu-lxqt-test01) |
| – | Documentation + rapid-deployment notes | Done |

---

## 1. ubuntu-lxqt-01 (Podman)

| Item | Value |
|------|-------|
| Container | ubuntu-lxqt-01 |
| Image | localhost/datadisca-ubuntu-lxqt-xrdp:26.04-2026-10-11 |
| IP | 192.168.220.104 |
| Specs | 4 GiB / 4 cores |
| Ports | 22, 3389 |
| Desktop | XFCE4 |
| User | nma |
| Status | running |

**Proof:**

```bash
sudo podman ps --filter name=ubuntu-lxqt-01
ping -c 1 192.168.220.104
ssh nma@192.168.220.104 'hostname; whoami'
nc -zv 192.168.220.104 3389
```

**GUI note:** SSH OK. XFCE session starts. RDP client attach limited in Podman. GUI via Xvnc:5920 + TightVNC (Bitvise tunnel). Prefer KVM for RDP GUI.

---

## 2. ubuntu-ssh-02 (Podman)

| Item | Value |
|------|-------|
| Container | ubuntu-ssh-02 |
| Image | localhost/datadisca-ubuntu-ssh:26.04-2026-10-10 |
| IP | 192.168.220.106 |
| Specs | 4 GiB / 4 cores |
| User | nma |

**Proof:**

```bash
sudo podman ps --filter name=ubuntu-ssh-02
ping -c 1 192.168.220.106
ssh nma@192.168.220.106 'hostname; whoami'
```

---

## 3. rocky-ssh-01 (Podman)

| Item | Value |
|------|-------|
| Container | rocky-ssh-01 |
| Image | localhost/datadisca-rocky-ssh:10.2-2026-10-11 |
| IP | 192.168.220.107 |
| Specs | 4 GiB / 4 cores |
| User | nma |

**Proof:**

```bash
sudo podman ps --filter name=rocky-ssh-01
ping -c 1 192.168.220.107
ssh nma@192.168.220.107 'hostname; whoami; cat /etc/os-release | head -3'
```

---

## 4. rocky-ssh-template (KVM)

| Item | Value |
|------|-------|
| VM | rocky-ssh-template |
| OS | Rocky Linux 9.8 |
| IP | 192.168.220.109/16 |
| Specs | 4 vCPU, 4 GB RAM |
| Disk | /data/vmdata/rocky-ssh-template.qcow2 |
| SSH | nma@192.168.220.109 |
| Autostart | enabled |
| Clone proof | rocky-ssh-02 @ 192.168.220.110 |

**Proof:**

```bash
sudo virsh list --all | grep rocky-ssh
sudo virsh dominfo rocky-ssh-template | grep -iE 'CPU|memory|Autostart|State'
ping -c 1 192.168.220.109
ssh nma@192.168.220.109 'hostname; whoami; cat /etc/os-release | head -3'
ping -c 1 192.168.220.110
ssh nma@192.168.220.110 'hostname; whoami'
```

**Clone (template must be shut off):**

```bash
sudo virsh shutdown rocky-ssh-template
sudo virt-clone --original rocky-ssh-template --name rocky-ssh-NEW \
  --file /data/vmdata/rocky-ssh-NEW.qcow2
sudo virsh start rocky-ssh-template
sudo virsh start rocky-ssh-NEW
# Inside clone: set hostname + new IP
```

---

## 5. ubuntu-lxqt-test01 (KVM)

| Item | Value |
|------|-------|
| VM | ubuntu-lxqt-test01 |
| OS | Ubuntu 26.04.1 LTS |
| IP | 192.168.220.108 |
| Specs | 4 GiB / 4 vCPU |
| Desktop | LXQt |
| Ports | 22, 3389 |
| Autostart | enabled |
| GUI | Working (Bitvise 13390 → mstsc) |

**Proof:**

```bash
sudo virsh list --all | grep ubuntu-lxqt-test01
sudo virsh dominfo ubuntu-lxqt-test01 | grep -iE 'CPU|memory|Autostart|State'
ping -c 1 192.168.220.108
ssh nma@192.168.220.108 'hostname; systemctl is-active xrdp'
nc -zv 192.168.220.108 3389
```

---

## Images

| Image | Tag | Purpose |
|-------|-----|---------|
| localhost/datadisca-ubuntu-lxqt-xrdp | 26.04-2026-10-11 | Ubuntu desktop + XRDP + SSH |
| localhost/datadisca-ubuntu-ssh | 26.04-2026-10-10 | Ubuntu SSH only |
| localhost/datadisca-rocky-ssh | 10.2-2026-10-11 | Rocky 10.2 SSH only |

---

## One-shot verify (ddserver14)

```bash
echo "=== Podman ==="
sudo podman ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'ubuntu-lxqt|ubuntu-ssh|rocky-ssh'

echo "=== IPs ==="
for ip in 192.168.220.104 192.168.220.106 192.168.220.107 192.168.220.108 192.168.220.109 192.168.220.110; do
  ping -c 1 -W 1 $ip >/dev/null && echo "$ip OK" || echo "$ip FAIL"
done

echo "=== KVM ==="
sudo virsh list --all | grep -E 'ubuntu-lxqt-test01|rocky-ssh|ocp_rocky1'
```

---

## Recorded proof (2026-10-17)

```text
ubuntu-lxqt-01       192.168.220.104  Podman  XFCE+XRDP+SSH
ubuntu-ssh-02        192.168.220.106  Podman  SSH
rocky-ssh-01         192.168.220.107  Podman  Rocky 10.2 SSH
ubuntu-lxqt-test01   192.168.220.108  KVM     LXQt+XRDP GUI OK
rocky-ssh-template   192.168.220.109  KVM     Rocky 9.8 minimal SSH, autostart, clone OK
rocky-ssh-02         192.168.220.110  KVM     clone of template
```

**Related:** `reusable_images_rapid_deploy.md`, `ip_usage.md`  
**End of 2026_10_10_todoproof.md**
