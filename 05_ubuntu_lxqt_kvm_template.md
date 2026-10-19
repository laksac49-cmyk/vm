# Ubuntu 26.04 LXQt + XRDP + SSH — KVM Reusable Template

**Purpose:** Create a reusable KVM virtual machine with Ubuntu 26.04 LTS, LXQt desktop only, XRDP, SSH, static IP, and the ability to clone new instances in under 10 minutes.  
**Tested:** 2026-10-18 / 2026-10-19 on ddserver14  
**Any-machine ready:** Yes (adjust bridge name, ISO path, IP range as needed)

---

## Current Instances (verified 2026-10-19)

| VM                 | IP               | Role          | Specs  | Notes                  |
|--------------------|------------------|---------------|--------|------------------------|
| ubuntu-lxqt-test01 | 192.168.220.108  | Template      | 4G/4c  | LXQt + XRDP + SSH      |
| ubuntu-lxqt-02     | 192.168.220.111  | Clone example | 4G/4c  | Working clone          |

---

## Requirements

- Host with KVM / libvirt / virt-install installed
- Root / sudo access
- Linux bridge (example: `br0`)
- Ubuntu 26.04 desktop or server ISO (or existing working VM)
- Free static IP on the LAN

---

## 1. Existing template verification

```bash
sudo virsh list --all | grep ubuntu-lxqt
sudo virsh dominfo ubuntu-lxqt-test01 | grep -E 'State|CPU|memory|Autostart'
ping -c 2 192.168.220.108
ssh -o StrictHostKeyChecking=no nma@192.168.220.108 \
  'hostname; cat /etc/os-release | head -3; systemctl is-active ssh xrdp; ls /usr/share/xsessions/'
```

**Expected:**
- hostname = ubuntu-lxqt-test01
- Ubuntu 26.04.1 LTS
- ssh + xrdp = active
- xsessions contains `lxqt.desktop`

---

## 2. Clone a new instance (rapid deploy < 10 min)

```bash
# Template must be shut off
sudo virsh shutdown ubuntu-lxqt-test01
while sudo virsh list --all | grep -q "ubuntu-lxqt-test01.*running"; do sleep 3; done

NEW=ubuntu-lxqt-NEW
NEW_IP=192.168.220.XXX          # free IP from ip_usage.md

sudo virt-clone --original ubuntu-lxqt-test01 \
  --name "$NEW" \
  --file /data/vmdata/${NEW}.qcow2

sudo virsh start ubuntu-lxqt-test01
sudo virsh start "$NEW"
sleep 45
```

### Change hostname + IP inside the clone

```bash
sudo virsh console $NEW
```

Login as `nma`, then:

```bash
sudo hostnamectl set-hostname $NEW

sudo tee /etc/netplan/99-static.yaml > /dev/null << EOF
network:
  version: 2
  ethernets:
    enp1s0:
      dhcp4: false
      addresses: [${NEW_IP}/16]
      routes:
        - to: default
          via: 192.168.0.1
      nameservers:
        addresses: [8.8.8.8, 1.1.1.1]
EOF

sudo netplan apply
hostname
ip -br a
exit
```

Exit console: `Ctrl + ]`

### Verify

```bash
ping -c 2 192.168.220.108
ping -c 2 $NEW_IP
ssh -o StrictHostKeyChecking=no nma@192.168.220.108 'hostname'
ssh -o StrictHostKeyChecking=no nma@$NEW_IP 'hostname; ip -br a | grep enp; systemctl is-active ssh xrdp'
sudo virsh list --all | grep ubuntu-lxqt
```

---

## 3. Memory / CPU reference

| RAM   | virsh --memory | vCPUs |
|-------|----------------|-------|
| 2 GiB | 2048           | 2     |
| 4 GiB | 4096           | 4     |
| 8 GiB | 8192           | 8     |

To change after creation (while shut off):

```bash
sudo virsh setmaxmem ubuntu-lxqt-NEW 8192M --config
sudo virsh setmem ubuntu-lxqt-NEW 8192M --config
sudo virsh setvcpus ubuntu-lxqt-NEW 8 --config --maximum
sudo virsh setvcpus ubuntu-lxqt-NEW 8 --config
```

---

## 4. Access

- **SSH:** `ssh nma@<IP>`
- **RDP:** connect to `<IP>:3389` (user `nma` or `tlk`)

**Credentials** (same as Podman images):
- User: `nma` / Password: `Ux3@f=7x2`
- User: `tlk` / Password: `Admin16308#$%`

---

## 5. Notes

- Primary desktop is **LXQt only** (`lxqt.desktop` in `/usr/share/xsessions/`).
- Template IP `192.168.220.108` should not be changed.
- Always shut the template off before cloning.
- After clone you **must** change hostname + IP (via netplan) to avoid conflict.
- Disk location: `/data/vmdata/<name>.qcow2`

---

## Example already created

```text
ubuntu-lxqt-test01  → 192.168.220.108  (template)
ubuntu-lxqt-02      → 192.168.220.111  (clone, verified 2026-10-19)
```

**Document created:** 2026-10-19  
**Related:** 04_rocky_kvm_ssh_template.md, reusable_images_rapid_deploy.md, ip_usage.md
