# Rocky Linux 10.2 SSH-only — Podman Reusable Image

**Purpose:** Create a reusable Podman container with Rocky Linux 10.2 minimal, SSH only, static IP, and configurable memory/CPU.  
**Tested:** 2026-10-18 / 2026-10-19 on ddserver14  
**Any-machine ready:** Yes

---

## Requirements

- Host with Podman installed
- Root / sudo access
- Linux bridge (`br0`) for macvlan
- Free static IP
- Existing macvlan network `lan-macvlan`

---

## 1. Clean previous instance (if exists)

```bash
sudo podman stop rocky-ssh-01 2>/dev/null || true
sudo podman rm -f rocky-ssh-01 2>/dev/null || true
```

---

## 2. Prepare directories

```bash
sudo mkdir -p /data/Containerfiles/rocky-ssh-01
sudo mkdir -p /data/pod_disks/rocky-ssh-01
sudo chmod 777 /data/pod_disks/rocky-ssh-01
cd /data/Containerfiles/rocky-ssh-01
```

---

## 3. Create Containerfile (Rocky 10 minimal + SSH)

```bash
sudo tee Containerfile > /dev/null << 'EOF'
FROM rockylinux/rockylinux:10
ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8
RUN dnf -y update && \
    dnf -y install \
        systemd systemd-sysv \
        sudo \
        openssh-server \
        iproute iputils net-tools bind-utils \
        nano vim-minimal curl wget \
        passwd \
    && dnf clean all
RUN useradd -m -s /bin/bash -G wheel nma && \
    echo "nma:Ux3@f=7x2" | chpasswd && \
    echo "nma ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/nma && \
    chmod 440 /etc/sudoers.d/nma
RUN useradd -m -s /bin/bash -G wheel tlk && \
    echo "tlk:Admin16308#\$%" | chpasswd && \
    echo "tlk ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/tlk && \
    chmod 440 /etc/sudoers.d/tlk
RUN mkdir -p /var/run/sshd && \
    ssh-keygen -A && \
    sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/^session.*pam_loginuid.so/#&/' /etc/pam.d/sshd || true
RUN systemctl enable sshd
CMD ["/sbin/init"]
EXPOSE 22
EOF
```

---

## 4. Build the reusable image

```bash
sudo podman build -t localhost/datadisca-rocky-ssh:10.2-2026-10-18 -f Containerfile .
```

---

## 5. Run the container (IMPORTANT: --cap-add=AUDIT_WRITE)

```bash
NAME=rocky-ssh-01
IP=192.168.220.107
MEMORY=4294967296
CPUS=4

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
```

> **Note:** `--cap-add=AUDIT_WRITE` is required on Rocky/RHEL containers. Without it SSH sessions fail with `linux_audit_write_entry failed: Operation not permitted`.

---

## 6. Host shim + route

```bash
sudo ip link add macvlan-shim link br0 type macvlan mode bridge 2>/dev/null || true
sudo ip addr add 192.168.220.254/32 dev macvlan-shim 2>/dev/null || true
sudo ip link set macvlan-shim up
sudo ip route add 192.168.220.107/32 dev macvlan-shim 2>/dev/null || true
```

---

## 7. Verification

```bash
sudo podman ps --filter name=rocky-ssh-01
ping -c 3 192.168.220.107
sudo podman exec rocky-ssh-01 systemctl is-active sshd
ssh -o StrictHostKeyChecking=no nma@192.168.220.107 'hostname; whoami; cat /etc/os-release | head -3; systemctl is-active sshd'
```

**SSH credentials**
- User: `nma` / Password: `Ux3@f=7x2`
- User: `tlk` / Password: `Admin16308#$%`

---

## 8. Rapid re-deploy

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
```

---

## Notes

- Minimal Rocky Linux 10.2 (no desktop).
- `--cap-add=AUDIT_WRITE` is mandatory for SSH to work.
- `--memory` and `--cpus` can be changed on every new instance.

**Document created:** 2026-10-18  
**Updated:** 2026-10-19  
**Related:** 01_ubuntu_lxqt_xrdp_podman.md, 02_ubuntu_ssh_podman.md, reusable_images_rapid_deploy.md, ip_usage.md
