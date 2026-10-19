# Rocky Linux 9.8 Minimal SSH — KVM Reusable Template

**Purpose:** Create a reusable KVM virtual machine template with Rocky Linux 9.8 minimal, SSH access, static IP, and the ability to clone new instances in under 10 minutes.  
**Tested:** 2026-10-18 / 2026-10-19 on ddserver14  
**Any-machine ready:** Yes (adjust bridge name, ISO path, IP range as needed)

---

## Requirements

- Host with KVM / libvirt / virt-install installed
- Root / sudo access
- Linux bridge (example: `br0`)
- Rocky Linux 9.8 minimal ISO
- Free static IP on the LAN (example range: 192.168.220.0/16)

---

## 1. Prepare directories and check ISO

```bash
sudo mkdir -p /data/vmdata /data/iso
ls -lh /data/iso/Rocky-9.8-x86_64-minimal.iso
```

If the ISO is missing, download it:

```bash
# sudo curl -L -o /data/iso/Rocky-9.8-x86_64-minimal.iso \
#   https://download.rockylinux.org/pub/rocky/9/isos/x86_64/Rocky-9.8-x86_64-minimal.iso
```

---

## 2. Create the template VM (virt-install)

```bash
sudo virt-install \
  --name rocky-ssh-template \
  --memory 4096 \
  --vcpus 4 \
  --disk path=/data/vmdata/rocky-ssh-template.qcow2,size=40,format=qcow2,bus=virtio \
  --cdrom /data/iso/Rocky-9.8-x86_64-minimal.iso \
  --network bridge=br0,model=virtio \
  --os-variant rocky9 \
  --graphics none \
  --console pty,target_type=serial \
  --noautoconsole
```

Connect to the installer console:

```bash
sudo virsh console rocky-ssh-template
```

(Escape from console later with `Ctrl + ]`)

---

## 3. Anaconda text installer steps (inside console)

1. Language → English (United States) → Continue  
2. Time settings → set timezone if needed  
3. Installation source → Local media  
4. Software selection → **Minimal Install**  
5. Installation Destination → Automatic partitioning  
6. Network configuration:
   - Device `enp1s0`
   - IPv4: Manual
   - Address: `192.168.220.109`
   - Netmask / Prefix: `16`
   - Gateway: `192.168.0.1`
   - DNS: `192.168.0.1,8.8.8.8`
   - Hostname: `rocky-ssh-template`
   - Enable “Apply configuration in installer” and “Connect automatically”
7. Root password → set a strong password  
8. User creation → create user `nma`, make Administrator, set password  
9. Begin Installation

After installation finishes, the system reboots. Exit console with `Ctrl + ]`.

---

## 4. Start and verify the template

```bash
sudo virsh start rocky-ssh-template
sleep 40

sudo virsh list --all | grep rocky-ssh
ping -c 3 192.168.220.109

ssh-keygen -R 192.168.220.109 2>/dev/null || true
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 nma@192.168.220.109 \
  'hostname; whoami; ip -br a; cat /etc/os-release | head -4; systemctl is-active sshd'
```

Enable autostart:

```bash
sudo virsh autostart rocky-ssh-template
sudo virsh dominfo rocky-ssh-template | grep -E 'State|CPU|memory|Autostart'
```

---

## 5. Clone a new instance (rapid deploy < 10 min)

```bash
# Template must be shut off
sudo virsh shutdown rocky-ssh-template
while sudo virsh list --all | grep -q "rocky-ssh-template.*running"; do sleep 3; done

NEW=rocky-ssh-02
NEW_IP=192.168.220.110

sudo virt-clone --original rocky-ssh-template \
  --name "$NEW" \
  --file /data/vmdata/${NEW}.qcow2

sudo virsh start rocky-ssh-template
sudo virsh start "$NEW"
sleep 40
```

### Change hostname + IP inside the clone

```bash
sudo virsh console rocky-ssh-02
```

Login as `nma`, then:

```bash
sudo hostnamectl set-hostname rocky-ssh-02
sudo nmcli con mod enp1s0 ipv4.addresses 192.168.220.110/16
sudo nmcli con mod enp1s0 ipv4.gateway 192.168.0.1
sudo nmcli con mod enp1s0 ipv4.dns "192.168.0.1 8.8.8.8"
sudo nmcli con mod enp1s0 ipv4.method manual
sudo nmcli con up enp1s0
hostname
ip -br a
exit
```

Exit console: `Ctrl + ]`

### Verify both VMs

```bash
ping -c 2 192.168.220.109
ping -c 2 192.168.220.110
ssh -o StrictHostKeyChecking=no nma@192.168.220.109 'hostname; ip -br a | grep enp'
ssh -o StrictHostKeyChecking=no nma@192.168.220.110 'hostname; ip -br a | grep enp'
sudo virsh list --all | grep rocky-ssh
sudo virsh autostart rocky-ssh-02
```

---

## 6. Memory / CPU reference

| RAM   | --memory | vCPUs |
|-------|----------|-------|
| 2 GiB | 2048     | 2     |
| 4 GiB | 4096     | 4     |
| 8 GiB | 8192     | 8     |

To change after creation (while shut off):

```bash
sudo virsh setmaxmem rocky-ssh-02 8192M --config
sudo virsh setmem rocky-ssh-02 8192M --config
sudo virsh setvcpus rocky-ssh-02 8 --config --maximum
sudo virsh setvcpus rocky-ssh-02 8 --config
```

---

## Notes

- Template IP: `192.168.220.109` — never change it after creation (clone source).
- Always shut the template off before cloning.
- After clone, **must** change hostname + IP inside the new VM to avoid conflict.
- User: `nma` (Administrator).

**Document created:** 2026-10-18  
**Updated:** 2026-10-19  
**Related:** reusable_images_rapid_deploy.md, ip_usage.md
