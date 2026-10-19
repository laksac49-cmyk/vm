# DataDisca Reusable Images & Rapid Deployment

**Host:** ddserver14 (`192.168.10.104`)  
**Last updated:** 2026-10-19  
**Purpose:** Create new Podman containers or KVM virtual machines in under 10 minutes with configurable memory and CPU.

---

## Overview

This repository contains complete, tested guides for building and rapidly deploying reusable images on ddserver14.

| # | Type   | Name                          | OS                  | Features                  | Status |
|---|--------|-------------------------------|---------------------|---------------------------|--------|
| 1 | Podman | ubuntu-lxqt-01                | Ubuntu 26.04        | LXQt + XRDP + SSH         | Done   |
| 2 | Podman | ubuntu-ssh-02                 | Ubuntu 26.04        | SSH only                  | Done   |
| 3 | Podman | rocky-ssh-01                  | Rocky Linux 10.2    | SSH only                  | Done   |
| 4 | KVM    | rocky-ssh-template            | Rocky Linux 9.8     | Minimal SSH (cloneable)   | Done   |
| 5 | KVM    | ubuntu-lxqt-test01            | Ubuntu 26.04        | LXQt + XRDP + SSH (cloneable) | Done |

All images support changing **memory** and **CPU cores** at creation time.

---

## Quick Start

1. Read `ip_usage.md` to pick a free IP from `192.168.220.0/16`.
2. Choose the guide you need:
   - Podman Ubuntu desktop → `01_ubuntu_lxqt_xrdp_podman.md`
   - Podman Ubuntu SSH → `02_ubuntu_ssh_podman.md`
   - Podman Rocky SSH → `03_rocky_ssh_podman.md`
   - KVM Rocky template → `04_rocky_kvm_ssh_template.md`
   - KVM Ubuntu LXQt template → `05_ubuntu_lxqt_kvm_template.md`
3. Use the **Rapid re-deploy** section in each file (usually < 10 minutes).

See also: `reusable_images_rapid_deploy.md` for a one-page cheat-sheet.

---

## Network & Storage Conventions

| Item              | Value                                      |
|-------------------|--------------------------------------------|
| Network range     | 192.168.220.0/16                           |
| Podman network    | `lan-macvlan` (macvlan on `br0`)           |
| Volume mount      | `/data/pod_disks/<name>` → `/data`         |
| KVM disk location | `/data/vmdata/<name>.qcow2`                |
| Default user      | `nma` (sudo NOPASSWD)                      |
| Secondary user    | `tlk` (sudo NOPASSWD)                      |

---

## Current Running Instances (2026-10-19)

### Podman (ddserver14)

| Container       | IP               | Specs  | Image tag                          |
|-----------------|------------------|--------|------------------------------------|
| ubuntu-lxqt-01  | 192.168.220.104  | 4G/4c  | datadisca-ubuntu-lxqt-xrdp:26.04-2026-10-18 |
| ubuntu-ssh-02   | 192.168.220.106  | 4G/4c  | datadisca-ubuntu-ssh:26.04-2026-10-18       |
| rocky-ssh-01    | 192.168.220.107  | 4G/4c  | datadisca-rocky-ssh:10.2-2026-10-18         |

### KVM (ddserver14)

| VM                    | IP               | Specs  | Notes                        |
|-----------------------|------------------|--------|------------------------------|
| rocky-ssh-template    | 192.168.220.109  | 4G/4c  | Clone source, autostart      |
| rocky-ssh-02          | 192.168.220.110  | 4G/4c  | Clone of template            |
| ubuntu-lxqt-test01    | 192.168.220.108  | 4G/4c  | LXQt + XRDP, clone source    |
| ubuntu-lxqt-02        | 192.168.220.111  | 4G/4c  | Clone of ubuntu-lxqt-test01  |
| ocp_rocky1            | 192.168.220.102  | 8c/16G | Full-size Rocky 9.8          |

---

## Related Files

- `ip_usage.md` – Full IP allocation table
- `reusable_images_rapid_deploy.md` – One-page rapid deploy commands
- `STATUS.md` – Todo completion status

---

**Document generated:** 2026-10-19  
**Host:** ddserver14  
