# Ubuntu 26.04 LXQt + XRDP + SSH — Podman Reusable Image

**Purpose:** Create a reusable Podman container with Ubuntu 26.04 LTS, LXQt desktop only, XRDP, SSH, static IP, and configurable memory/CPU.  
**Tested:** 2026-10-18 / 2026-10-19 on ddserver14  
**Any-machine ready:** Yes (adjust parent interface, IP, and network name if needed)

---

## Requirements

- Ubuntu host with Podman installed
- Root / sudo access
- A Linux bridge (example: `br0`) for macvlan
- Free static IP on the LAN

---

## 1. Prepare directories

```bash
sudo mkdir -p /data/Containerfiles/ubuntu-lxqt-01
sudo mkdir -p /data/pod_disks/ubuntu-lxqt-01
sudo chmod 777 /data/pod_disks/ubuntu-lxqt-01
cd /data/Containerfiles/ubuntu-lxqt-01
```

---

## 2. Create Containerfile (LXQt only)

```bash
sudo tee Containerfile > /dev/null << 'EOF'
FROM ubuntu:26.04
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    GLYCIN_DISABLE_SANDBOX=1
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        systemd systemd-sysv \
        sudo \
        openssh-server \
        xrdp xorgxrdp \
        dbus-x11 \
        lxqt lxqt-core \
        pcmanfm-qt qterminal \
        papirus-icon-theme \
        breeze-icon-theme \
        arc-theme \
        numix-icon-theme \
        qt5ct \
        qt6ct \
        lxqt-config \
        fonts-noto \
        fonts-liberation \
        xorg xserver-xorg-core \
        iproute2 iputils-ping net-tools dnsutils \
        nano vim curl wget \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN useradd -m -s /bin/bash -G sudo,ssl-cert nma && \
    echo "nma:Ux3@f=7x2" | chpasswd && \
    echo "nma ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/nma && \
    chmod 440 /etc/sudoers.d/nma
RUN useradd -m -s /bin/bash -G sudo,ssl-cert tlk && \
    echo "tlk:Admin16308#\$%" | chpasswd && \
    echo "tlk ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/tlk && \
    chmod 440 /etc/sudoers.d/tlk
RUN echo 'exec dbus-run-session -- startlxqt' > /etc/skel/.xsession && \
    cp /etc/skel/.xsession /home/nma/.xsession && \
    cp /etc/skel/.xsession /home/tlk/.xsession && \
    chown nma:nma /home/nma/.xsession && \
    chown tlk:tlk /home/tlk/.xsession && \
    chmod +x /home/nma/.xsession /home/tlk/.xsession && \
    usermod -aG ssl-cert xrdp && \
    sed -i 's/console/anybody/g' /etc/X11/Xwrapper.config || true
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config && \
    sed -i 's/#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/^session.*pam_loginuid.so/#&/' /etc/pam.d/sshd
RUN printf '%s\n' \
    '#!/bin/sh' \
    'export LANG=C.UTF-8' \
    'export GLYCIN_DISABLE_SANDBOX=1' \
    'unset SESSION_MANAGER' \
    'unset DBUS_SESSION_BUS_ADDRESS' \
    'export XDG_RUNTIME_DIR=/tmp/runtime-$USER' \
    'mkdir -p "$XDG_RUNTIME_DIR"' \
    'chmod 700 "$XDG_RUNTIME_DIR"' \
    'exec dbus-run-session -- startlxqt' \
    > /etc/xrdp/startwm.sh && \
    chmod +x /etc/xrdp/startwm.sh
RUN systemctl enable ssh xrdp
CMD ["/sbin/init"]
EXPOSE 22 3389
EOF
```

---

## 3. Build the reusable image

```bash
sudo podman build -t localhost/datadisca-ubuntu-lxqt-xrdp:26.04-2026-10-18 -f Containerfile .
```

---

## 4. Create / verify macvlan network (one-time)

```bash
sudo podman network ls
# Create only if missing (adjust parent interface if needed)
sudo podman network create \
  -d macvlan \
  -o parent=br0 \
  --subnet 192.168.0.0/16 \
  --gateway 192.168.0.1 \
  lan-macvlan
```

---

## 5. Run the container (change MEMORY / CPUS as needed)

```bash
NAME=ubuntu-lxqt-01
IP=192.168.220.104
MEMORY=4294967296   # 4 GiB
CPUS=4

sudo podman run -d \
  --name $NAME \
  --systemd=always \
  --memory $MEMORY \
  --cpus $CPUS \
  --network lan-macvlan:ip=$IP \
  -v /data/pod_disks/$NAME:/data \
  --hostname $NAME \
  localhost/datadisca-ubuntu-lxqt-xrdp:26.04-2026-10-18
```

---

## 6. Host shim (so the host can reach the container)

```bash
sudo ip link add macvlan-shim link br0 type macvlan mode bridge 2>/dev/null || true
sudo ip addr add 192.168.220.254/32 dev macvlan-shim 2>/dev/null || true
sudo ip link set macvlan-shim up
sudo ip route add 192.168.220.104/32 dev macvlan-shim 2>/dev/null || true
```

---

## 7. Verification

```bash
sudo podman ps --filter name=ubuntu-lxqt-01
ping -c 3 192.168.220.104
sudo podman exec ubuntu-lxqt-01 systemctl is-active ssh xrdp
ssh nma@192.168.220.104 'hostname; whoami; systemctl is-active ssh xrdp'
nc -zv 192.168.220.104 3389
```

**SSH credentials**
- User: `nma` / Password: `Ux3@f=7x2`
- User: `tlk` / Password: `Admin16308#$%`

**RDP:** `192.168.220.104:3389` (same users)

---

## 8. Rapid re-deploy (new instance in < 10 minutes)

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
```

---

## Notes

- Only LXQt is installed (no GNOME, KDE, XFCE as primary desktop).
- `--memory` and `--cpus` can be changed on every new instance.
- macvlan makes the container appear as a real host on the LAN.
- Host needs the shim + route to reach the container IP.

**Document created:** 2026-10-18  
**Updated:** 2026-10-19  
**Related:** reusable_images_rapid_deploy.md, ip_usage.md
