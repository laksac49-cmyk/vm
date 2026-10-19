# Cleanup: Ubuntu 26.04 LXQt + XRDP + SSH Container (Podman)

Complete cleanup of the `ubuntu_gui_staticip` container, network, shim, images, and data.

## Stop and remove the container

```bash
sudo podman stop ubuntu_gui_staticip 2>/dev/null || true
sudo podman rm -f ubuntu_gui_staticip 2>/dev/null || true
```

## Remove all containers (optional, if you want a full wipe)

```bash
sudo podman stop -a 2>/dev/null || true
sudo podman rm -af
```

## Remove the macvlan network

```bash
sudo podman network rm mynet 2>/dev/null || true
```

## Remove the host macvlan shim

```bash
sudo ip link del macvlan-shim 2>/dev/null || true
```

## Remove the image

```bash
sudo podman rmi ubuntu-lxqt-xrdp:26.04 2>/dev/null || true
sudo podman rmi localhost/ubuntu-lxqt-xrdp:26.04 2>/dev/null || true
sudo podman image prune -f
```

## Remove the data directory

```bash
sudo rm -rf /data/pod_disks/ubuntu_gui_staticip
```

## Optional: full system prune

```bash
sudo podman system prune -af --volumes
```

## Verify cleanup

```bash
sudo podman ps -a
sudo podman network ls
sudo podman images
ip link show | grep macvlan || echo "No macvlan shim"
ls /data/pod_disks/ubuntu_gui_staticip 2>/dev/null || echo "Data directory removed"
```

## Notes

- The host route (`ip route add 192.168.221.51/32 dev macvlan-shim`) is removed automatically when the shim interface is deleted.
- If you only want to remove this specific container and keep other Podman resources, run only the first few sections.
- The data directory removal is irreversible — back up anything important first.
