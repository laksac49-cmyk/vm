# Ubuntu 26.04 LXQt + XRDP + SSH Container (Podman)

Complete guide to build and run an Ubuntu 26.04 LTS container with LXQt desktop, XRDP, and SSH, using a static IP on the host LAN via macvlan.

## Features

- Ubuntu 26.04 LTS (Resolute Raccoon)
- LXQt desktop environment only (no GNOME, KDE, or XFCE)
- XRDP remote desktop
- SSH access
- Static IP: `192.168.221.51`
- Gateway: `192.168.0.1`
- DNS: `192.168.0.1`
- 4 GB RAM, 4 CPU cores
- Persistent volume: `/data/pod_disks/ubuntu_gui_staticip` mounted as `/data`
- Default user: `nma` / Password: `datadisca`

## Containerfile

Save as `Containerfile`:

```dockerfile
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
    echo "nma:datadisca" | chpasswd && \
    echo "nma ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/nma && \
    chmod 440 /etc/sudoers.d/nma

RUN echo 'exec dbus-run-session -- startlxqt' > /etc/skel/.xsession && \
    cp /etc/skel/.xsession /home/nma/.xsession && \
    chown nma:nma /home/nma/.xsession && \
    chmod +x /home/nma/.xsession && \
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
    'export XDG_RUNTIME_DIR=/tmp/runtime-nma' \
    'mkdir -p "$XDG_RUNTIME_DIR"' \
    'chmod 700 "$XDG_RUNTIME_DIR"' \
    'exec dbus-run-session -- startlxqt' \
    > /etc/xrdp/startwm.sh && \
    chmod +x /etc/xrdp/startwm.sh

RUN systemctl enable ssh xrdp

CMD ["/sbin/init"]
EXPOSE 22 3389
```

## Build

```bash
cd /data/Containerfiles/ubuntu_gui_staticip
sudo podman build -t ubuntu-lxqt-xrdp:26.04 -f Containerfile .
```

## Create macvlan network

```bash
sudo podman network create \
  -d macvlan \
  -o parent=eno1 \
  --subnet 192.168.0.0/16 \
  --gateway 192.168.0.1 \
  mynet
```

> **Note:** Confirm the parent interface with `ip route show default`. Replace `eno1` if your host uses a different interface.

## Prepare data directory

```bash
sudo mkdir -p /data/pod_disks/ubuntu_gui_staticip
#sudo chown -R $USER:$USER /data/pod_disks/ubuntu_gui_staticip
sudo chmod -R 777 /data/pod_disks/ubuntu_gui_staticip
```

## Run the container

```bash
sudo podman run -d \
  --name ubuntu_gui_staticip \
  --systemd=always \
  --memory=4g \
  --cpus=4 \
  --network mynet \
  --ip 192.168.221.51 \
  --dns 192.168.0.1 \
  -v /data/pod_disks/ubuntu_gui_staticip:/data \
  --hostname ubuntu_gui_staticip \
  ubuntu-lxqt-xrdp:26.04
```

## Host shim (so the host can reach the container)

```bash
sudo ip link add macvlan-shim link eno1 type macvlan mode bridge
sudo ip addr add 192.168.221.254/32 dev macvlan-shim
sudo ip link set macvlan-shim up

# Required route so the host can reach the container
sudo ip route add 192.168.221.51/32 dev macvlan-shim
```

## Access

- **SSH**: `ssh nma@192.168.221.51`  
  Password: `datadisca`
- **XRDP**: Connect to `192.168.221.51:3389`  
  User: `nma` / Password: `datadisca`

## Appearance

After first login via RDP:

1. Open **LXQt Configuration Center** → **Appearance**.
2. Set **Icons Theme** to `Papirus`.
3. Set **Widget Style** to `Arc` (or `Fusion` if Arc is not listed).
4. Click Apply.

Alternatively, set it from the command line:

```bash
sudo podman exec -u nma ubuntu_gui_staticip bash -c '
mkdir -p ~/.config/lxqt
cat > ~/.config/lxqt/session.conf << "EOF"
[General]
icon_theme=Papirus
EOF
'
```

## Verify

```bash
sudo podman ps --filter name=ubuntu_gui_staticip
sudo podman exec ubuntu_gui_staticip ip addr show
sudo podman exec ubuntu_gui_staticip systemctl status ssh xrdp
```

## Notes

- Includes the `pam_loginuid` fix (prevents SSH session drops in containers).
- `GLYCIN_DISABLE_SANDBOX=1` avoids the glycin/bubblewrap icon loader crash.
- Only LXQt is installed (no GNOME, KDE, or XFCE), with Papirus icons and Arc theme available.
- Macvlan makes the container appear as an independent host on `192.168.221.51`.
- The host needs the shim **and** an explicit route (`ip route add 192.168.221.51/32 dev macvlan-shim`) to reach the container; other machines on the LAN can reach it directly.
- Port publishing (`-p`) is not used with macvlan — connect directly to the container IP.
