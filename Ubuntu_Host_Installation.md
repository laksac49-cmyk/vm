# Ubuntu Host Preparation Guide

**Server:** ddserver16  
**Date:** 11 October 2026  
**Purpose:** Prepare an Ubuntu host for container workloads (Podman), virtualization (KVM), and web-based management (Cockpit).

This document records the steps performed to prepare the host, including package installation, user management, and configuration of core services.

---

## Table of Contents

1. [System Updates](#system-updates)
2. [Basic Tools](#basic-tools)
3. [User Management](#user-management)
4. [Passwordless Sudo](#passwordless-sudo)
5. [Podman Installation](#podman-installation)
6. [Cockpit Installation](#cockpit-installation)
7. [KVM / Libvirt Installation](#kvm--libvirt-installation)
8. [Static IP with Bridge](#static-ip-with-bridge)
9. [Verification Summary](#verification-summary)
10. [Useful References](#useful-references)

---

## System Updates

Always start by refreshing package indexes:

```bash
sudo apt update
```

---

## Basic Tools

Install essential command-line tools:

```bash
sudo apt install -y vim nano iputils-ping
```

| Package         | Provides          |
|-----------------|-------------------|
| `vim`           | `vi` / Vim editor |
| `nano`          | Nano editor       |
| `iputils-ping`  | `ping` command    |

---

## User Management

### Create admin user `nma`

```bash
sudo adduser nma
sudo usermod -aG sudo nma
```

### Verify

```bash
id nma
groups nma
```

The existing user `tlk` was already configured with sudo access.

---

## Passwordless Sudo

Configure passwordless sudo for **all** members of the `sudo` group using a drop-in file:

```bash
sudo tee /etc/sudoers.d/sudo-nopasswd << 'EOF'
# Passwordless sudo for all members of the sudo group
%sudo ALL=(ALL) NOPASSWD:ALL
EOF

sudo chmod 0440 /etc/sudoers.d/sudo-nopasswd
sudo visudo -c
```

**Verification:**

```bash
sudo -u tlk sudo -n true && echo "OK for tlk"
sudo -u nma sudo -n true && echo "OK for nma"
```

> **Security note:** Passwordless sudo removes an important safety layer. Use only on trusted systems.

To revert later:

```bash
sudo rm /etc/sudoers.d/sudo-nopasswd
```

---

## Podman Installation

Install Podman (daemonless container engine):

```bash
sudo apt install -y podman
```

### Optional packages

```bash
sudo apt install -y buildah skopeo podman-docker cockpit-podman
```

### Verify

```bash
podman --version
podman info
podman run --rm docker.io/library/alpine echo "Podman works"
```

---

## Cockpit Installation

Install the Cockpit web console and useful plugins:

```bash
sudo apt install -y cockpit cockpit-podman cockpit-machines \
  cockpit-storaged cockpit-networkmanager cockpit-packagekit

sudo systemctl enable --now cockpit.socket
```

### Firewall (if UFW is active)

```bash
sudo ufw allow 9090/tcp
sudo ufw reload
```

### Access

Open a browser and navigate to:

```text
https://<SERVER_IP>:9090
```

Log in with any user that has sudo privileges (`tlk` or `nma`). Administrative access is available via the top-bar indicator.

---

## KVM / Libvirt Installation

### Check CPU virtualization support

```bash
egrep -c '(vmx|svm)' /proc/cpuinfo
```

A non-zero result means the CPU supports virtualization (ensure it is enabled in BIOS/UEFI).

### Install packages

On modern Ubuntu, `qemu-kvm` is a virtual package. Install the concrete package instead:

```bash
# Standard
sudo apt install -y qemu-system-x86 libvirt-daemon-system \
  libvirt-clients bridge-utils virtinst

# Or HWE (Hardware Enablement) variant for newer kernel/hardware support
# sudo apt install -y qemu-system-x86-hwe libvirt-daemon-system \
#   libvirt-clients bridge-utils virtinst
```

> **HWE note:** The Hardware Enablement variant tracks a newer kernel and is preferred on recent hardware. Check your kernel with `uname -r`.

### Enable libvirt and add user to groups

```bash
sudo systemctl enable --now libvirtd
sudo usermod -aG libvirt,kvm $USER
```

Log out and log back in for group membership to take effect.

### Start the default network

```bash
sudo virsh net-start default
sudo virsh net-autostart default
```

### Verify

```bash
lsmod | grep kvm
virsh list --all
virsh net-list --all
```

Expected network status:

```text
 Name      State    Autostart   Persistent
--------------------------------------------
 default   active   yes         yes
```

---

## Static IP with Bridge

Configure a Linux bridge so the host uses a static IP and virtual machines can attach directly to the physical network (bridged networking).

> **Important:** Replace the example values (`enp1s0`, IP addresses, gateway, DNS) with your actual interface name and network details. Identify your interface with `ip link` or `ip -br a`.

### 1. Install bridge utilities (if not already present)

```bash
sudo apt install -y bridge-utils
```

### 2. Create the Netplan configuration

```bash
sudo nano /etc/netplan/01-netcfg.yaml
```

Example configuration (bridge named `br0`):

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enp1s0:
      dhcp4: false
      dhcp6: false
  bridges:
    br0:
      interfaces: [enp1s0]
      dhcp4: false
      dhcp6: false
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses:
          - 1.1.1.1
          - 8.8.8.8
      parameters:
        stp: false
        forward-delay: 0
```

### 3. Apply the configuration

```bash
sudo netplan generate
sudo netplan apply
```

### 4. Verify

```bash
ip -br a
ip route
ping -c 3 1.1.1.1
```

The bridge `br0` should show your static IP, and the physical interface should be a slave of the bridge.

### 5. Attach VMs to the bridge

When creating a VM with `virt-install` or Cockpit, select the bridge network (or create a libvirt network that uses `br0`).

Example libvirt bridge network definition:

```bash
sudo tee /tmp/br0-network.xml << 'EOF'
<network>
  <name>br0</name>
  <forward mode='bridge'/>
  <bridge name='br0'/>
</network>
EOF

sudo virsh net-define /tmp/br0-network.xml
sudo virsh net-start br0
sudo virsh net-autostart br0
```

---

## Verification Summary

| Component          | Status / Command                          |
|--------------------|-------------------------------------------|
| Basic tools        | `vi --version`, `nano --version`, `ping -V` |
| Users              | `id tlk`, `id nma`, `groups`              |
| Passwordless sudo  | `sudo -n true`                            |
| Podman             | `podman --version`, `podman run ...`      |
| Cockpit            | `systemctl status cockpit.socket`         |
| KVM modules        | `lsmod \| grep kvm`                       |
| Libvirt            | `virsh list --all`                        |
| Default network    | `virsh net-list --all`                    |
| Bridge / Static IP | `ip -br a` (look for `br0`)               |

---

## Useful References

- [Podman Installation](https://podman.io/docs/installation)
- [Cockpit Project](https://cockpit-project.org/)
- [Ubuntu KVM / Libvirt documentation](https://ubuntu.com/server/docs/virtualization-introduction)
- [Libvirt networking](https://libvirt.org/formatnetwork.html)

---

**Document generated:** 11 October 2026  
**Host:** ddserver16
