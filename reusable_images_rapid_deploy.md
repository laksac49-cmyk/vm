# Reusable Images — Rapid Deployment Cheat-Sheet

**Purpose:** Create new instances in under 10 minutes.  
**Host:** ddserver14  
**Last updated:** 2026-10-19

Change `XXX` (IP), name, memory and CPU as needed.

---

## Prerequisites

```bash
sudo podman network ls | grep lan-macvlan
# Free IP from 192.168.220.0/16 — see ip_usage.md
```

---

## 1. Ubuntu SSH container (Podman)

```bash
NAME=ubuntu-ssh-NEW
IP=192.168.220.XXX
MEMORY=4294967296   # 4 GiB
CPUS=4

sudo mkdir -p /data/pod_disks/$NAME
sudo chmod 777 /data/pod_disks/$NAME

sudo podman run -d \
  --name $NAME \
  --systemd=always \
  --memory $MEMORY \
  --cpus $CPUS \
  --network lan-macvlan:ip=$IP \
  -v /data/pod_disks/$NAME:/data \
  --hostname $NAME \
  localhost/datadisca-ubuntu-ssh:26.04-2026-10-18

sudo ip route add $IP/32 dev macvlan-shim 2>/dev/null || true
ssh nma@$IP 'hostname; whoami'
```

---

## 2. Ubuntu desktop + XRDP container (Podman)

```bash
NAME=ubuntu-lxqt-NEW
IP=192.168.220.XXX
MEMORY=4294967296
CPUS=4

sudo mkdir -p /data/pod_disks/$NAME
sudo chmod 777 /data/pod_disks/$NAME

sudo podman run -d \
  --name $NAME \
  --systemd=always \
  --memory $MEMORY \
  --cpus $CPUS \
  --network lan-macvlan:ip=$IP \
  -v /data/pod_disks/$NAME:/data \
  --hostname $NAME \
  localhost/datadisca-ubuntu-lxqt-xrdp:26.04-2026-10-18

sudo ip route add $IP/32 dev macvlan-shim 2>/dev/null || true
ssh nma@$IP 'hostname; whoami'
```

**Note:** SSH OK. RDP may be limited in Podman; prefer KVM for reliable GUI.

---

## 3. Rocky SSH container (Podman)

```bash
NAME=rocky-ssh-NEW
IP=192.168.220.XXX
MEMORY=4294967296
CPUS=4

sudo mkdir -p /data/pod_disks/$NAME
sudo chmod 777 /data/pod_disks/$NAME

sudo podman run -d \
  --name $NAME \
  --systemd=always \
  --memory $MEMORY \
  --cpus $CPUS \
  --cap-add=AUDIT_WRITE \
  --network lan-macvlan:ip=$IP \
  -v /data/pod_disks/$NAME:/data \
  --hostname $NAME \
  localhost/datadisca-rocky-ssh:10.2-2026-10-18

sudo ip route add $IP/32 dev macvlan-shim 2>/dev/null || true
ssh nma@$IP 'hostname; whoami'
```

---

## 4. KVM Rocky clone (from rocky-ssh-template)

```bash
# Template must be shut off
sudo virsh shutdown rocky-ssh-template
while sudo virsh list --all | grep -q "rocky-ssh-template.*running"; do sleep 3; done

NEW=rocky-ssh-NEW
NEW_IP=192.168.220.XXX

sudo virt-clone --original rocky-ssh-template \
  --name "$NEW" \
  --file /data/vmdata/${NEW}.qcow2

sudo virsh start rocky-ssh-template
sudo virsh start "$NEW"
sleep 40

# Inside the clone (virsh console or temporary SSH):
# sudo hostnamectl set-hostname $NEW
# sudo nmcli con mod enp1s0 ipv4.addresses ${NEW_IP}/16
# sudo nmcli con mod enp1s0 ipv4.gateway 192.168.0.1
# sudo nmcli con mod enp1s0 ipv4.dns "192.168.0.1 8.8.8.8"
# sudo nmcli con mod enp1s0 ipv4.method manual
# sudo nmcli con up enp1s0
```

---

## 5. KVM Ubuntu LXQt clone (from ubuntu-lxqt-test01)

```bash
# Template must be shut off
sudo virsh shutdown ubuntu-lxqt-test01
while sudo virsh list --all | grep -q "ubuntu-lxqt-test01.*running"; do sleep 3; done

NEW=ubuntu-lxqt-NEW
NEW_IP=192.168.220.XXX

sudo virt-clone --original ubuntu-lxqt-test01 \
  --name "$NEW" \
  --file /data/vmdata/${NEW}.qcow2

sudo virsh start ubuntu-lxqt-test01
sudo virsh start "$NEW"
sleep 45

# Inside the clone:
# sudo hostnamectl set-hostname $NEW
# sudo tee /etc/netplan/99-static.yaml > /dev/null << EOF
# network:
#   version: 2
#   ethernets:
#     enp1s0:
#       dhcp4: false
#       addresses: [${NEW_IP}/16]
#       routes:
#         - to: default
#           via: 192.168.0.1
#       nameservers:
#         addresses: [8.8.8.8, 1.1.1.1]
# EOF
# sudo netplan apply
```

---

## Memory / CPU Reference

| RAM   | --memory (Podman) | virsh --memory | Cores |
|-------|-------------------|----------------|-------|
| 2 GiB | 2147483648        | 2048           | 2     |
| 4 GiB | 4294967296        | 4096           | 4     |
| 8 GiB | 8589934592        | 8192           | 8     |

---

## Available Images / Templates

| Name                                                  | Type   | Use                            |
|-------------------------------------------------------|--------|--------------------------------|
| localhost/datadisca-ubuntu-lxqt-xrdp:26.04-2026-10-18 | Podman | Ubuntu desktop + XRDP + SSH    |
| localhost/datadisca-ubuntu-ssh:26.04-2026-10-18       | Podman | Ubuntu SSH only                |
| localhost/datadisca-rocky-ssh:10.2-2026-10-18         | Podman | Rocky 10.2 SSH                 |
| rocky-ssh-template                                    | KVM    | Rocky 9.8 minimal SSH (clone)  |
| ubuntu-lxqt-test01                                    | KVM    | Ubuntu 26.04 LXQt + XRDP       |

---

**Related:** `ip_usage.md`, individual 01–05 guides  
**End of reusable_images_rapid_deploy.md**
