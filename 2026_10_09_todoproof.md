# DataDisca Migration — 2026-10-09 Todo Proof

**Last updated:** 2026-10-09  
**Server:** ddserver14 (`192.168.10.104`)

---

## Todo

| # | Task | Status |
|---|------|--------|
| 1 | Add Rocky Linux 9 VM on ddserver14 (same specs as jfrog): name `ocp_rocky1`, static IP, SSH from jump host, ISO Rocky-9.8-x86_64-minimal | ✅ Done |

---

## Specs (matched to jfrog)

| Item | jfrog | ocp_rocky1 |
|------|-------|------------|
| Host | ddserver14 | ddserver14 |
| vCPU | 8 | 8 |
| RAM | 16 GB | 16 GB |
| Disk | /data/vmdata/jfrog.qcow2 | /data/vmdata/ocp_rocky1.qcow2 (100G) |
| Primary IP | 192.168.220.100/16 | **192.168.220.102/16** |
| Secondary IP | 192.168.122.38/24 | **192.168.122.102/24** |
| Gateway | 192.168.0.1 | 192.168.0.1 |
| Networks | br0 + virbr0 | br0 + virbr0 |
| Autostart | enable | enable |
| OS | Ubuntu 24.04 | Rocky Linux 9.8 |

---

## Proof commands (run on ddserver14)

### 1. VM running + autostart

```bash
sudo virsh list --all | grep ocp
sudo virsh dominfo ocp_rocky1 | grep -iE 'CPU|memory|Autostart'
```

**Pass:**
```text
7    ocp_rocky1           running
CPU(s):         8
Max memory:     16777216 KiB
Autostart:      enable
```

### 2. Static IPs

```bash
ping -c 2 192.168.220.102
ping -c 2 192.168.122.102
ssh tlk@192.168.220.102 'hostname; ip -br a; cat /etc/rocky-release'
```

**Pass:**
```text
enp1s0  UP  192.168.220.102/16
enp2s0  UP  192.168.122.102/24
Rocky Linux release 9.8
```

### 3. Existing VMs untouched

```bash
ping -c 1 192.168.220.100
ping -c 1 192.168.220.101
sudo virsh list --all
```

**Pass:**
```text
jfrog                running
ubuntu-voice-clone   running
ocp_rocky1           running
```

### 4. SSH from jump host path

```bash
# Office → dating → ddserver14 → ocp_rocky1
ssh -p 3422 lahiru@Sr.datadisca.com
ssh nma@192.168.10.104
ssh tlk@192.168.220.102
```

**Pass:** login OK as `tlk`

### 5. Disk path

```bash
sudo virsh domblklist ocp_rocky1
ls -lh /data/vmdata/ocp_rocky1.qcow2
```

**Pass:**
```text
vda  /data/vmdata/ocp_rocky1.qcow2
```

---

## Recorded proof (2026-10-09)

```text
VM ocp_rocky1 running on ddserver14
8 vCPU, 16 GB RAM, 100G qcow2 on /data/vmdata/
Primary 192.168.220.102/16 gateway 192.168.0.1
Secondary 192.168.122.102/24
SSH tlk@192.168.220.102 OK
Autostart enabled
jfrog + ubuntu-voice-clone still running (untouched)
ISO: Rocky-9.8-x86_64-minimal.iso
```

---

## One-shot verify (ddserver14)

```bash
echo "=== ocp_rocky1 ==="
sudo virsh list --all | grep -E 'ocp|jfrog|voice'
sudo virsh dominfo ocp_rocky1 | grep -iE 'CPU|Max memory|Autostart'
ping -c 1 192.168.220.102
ping -c 1 192.168.122.102
ssh -o BatchMode=no tlk@192.168.220.102 'hostname; ip -br a | grep -v lo; cat /etc/rocky-release'
ping -c 1 192.168.220.100
ping -c 1 192.168.220.101
```

---

**End of 2026_10_09_todoproof.md**
