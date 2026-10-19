# Ubuntu 26.04 SSH-only — Podman Reusable Image

**Purpose:** Create a reusable Podman container with Ubuntu 26.04 LTS, SSH only (no desktop), static IP, and configurable memory/CPU.  
**Tested:** 2026-10-18 / 2026-10-19 on ddserver14  
**Any-machine ready:** Yes

---

## Requirements

- Ubuntu host with Podman installed
- Root / sudo access
- Linux bridge (`br0`) for macvlan
- Free static IP
- Existing macvlan network `lan-macvlan` (or create it)

---

## 1. Clean previous instance (if exists)

```bash
sudo podman stop ubuntu-ssh-02 2>/dev/null || true
sudo podman rm -f ubuntu-ssh-02 2>/dev/null || true
```

---

## 2. Prepare directories

```bash
sudo mkdir -p /data/Containerfiles/ubuntu-ssh-02
sudo mkdir -p /data/pod_disks/ubuntu-ssh-02
sudo chmod 777 /data/pod_disks/ubuntu-ssh-02
cd /data/Containerfiles/ubuntu-ssh-02
```

---

## 3. Create Containerfile (SSH only)

```bash
sudo tee Containerfile > /dev/null << 'EOF'
FROM ubuntu:26.04
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        systemd systemd-sysv \
        sudo \
        openssh-server \
        iproute2 iputils-ping net-tools dnsutils \
        nano vim curl wget \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN useradd -m -s /bin/bash -G sudo nma && \
    echo "nma:Ux3@f=7x2" | chpasswd && \
    echo "nma ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/nma && \
    chmod 440 /etc/sudoers.d/nma
RUN useradd -m -s /bin/bash -G sudo tlk && \
    echo "tlk:Admin16308#\$%" | chpasswd && \
    echo "tlk ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/tlk && \
    chmod 440 /etc/sudoers.d/tlk
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/^session.*pam_loginuid.so/#&/' /etc/pam.d/sshd
RUN systemctl enable ssh
CMD ["/sbin/init"]
EXPOSE 22
EOF
```

---

## 4. Build the reusable image

```bash
sudo podman build -t localhost/datadisca-ubuntu-ssh:26.04-2026-10-18 -f Containerfile .
```

---

## 5. Run the container

```bash
NAME=ubuntu-ssh-02
IP=192.168.220.106
MEMORY=4294967296
CPUS=4

sudo podman run -d \
  --name $NAME \
  --systemd=always \
  --memory $MEMORY \
  --cpus $CPUS \
  --network lan-macvlan:ip=$IP \
  -v /data/pod_disks/$NAME:/data \
  --hostname $NAME \
  localhost/datadisca-ubuntu-ssh:26.04-2026-10-18
```

---

## 6. Host route

```bash
sudo ip route add 192.168.220.106/32 dev macvlan-shim 2>/dev/null || true
```

---

## 7. Verification

```bash
sudo podman ps --filter name=ubuntu-ssh-02
ping -c 3 192.168.220.106
sudo podman exec ubuntu-ssh-02 systemctl is-active ssh
ssh -o StrictHostKeyChecking=no nma@192.168.220.106 'hostname; whoami; cat /etc/os-release | head -3'
```

**SSH credentials**
- User: `nma` / Password: `Ux3@f=7x2`
- User: `tlk` / Password: `Admin16308#$%`

---

## 8. Rapid re-deploy

```bash
NAME=ubuntu-ssh-NEW
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
  localhost/datadisca-ubuntu-ssh:26.04-2026-10-18

sudo ip route add $IP/32 dev macvlan-shim 2>/dev/null || true
```

---

## Notes

- No desktop environment installed (SSH only).
- `--memory` and `--cpus` can be changed on every new instance.

**Document created:** 2026-10-18  
**Updated:** 2026-10-19  
**Related:** 01_ubuntu_lxqt_xrdp_podman.md, reusable_images_rapid_deploy.md, ip_usage.md
