# Todo Status – Reusable Images

**Last updated:** 2026-10-19  
**Primary host:** ddserver14 (`192.168.10.104`)

---

## Original Requirements (2026-10-10)

Target:
- Document all how-to steps for future use
- Create reusable images / rapid deployment code
- Ability to change memory and CPU cores when creating new instances
- Create a new pod or VM within 10 minutes of the request

---

## Completion Status

| # | Task | Status | Proof |
|---|------|--------|-------|
| 1 | Podman: Ubuntu 26.04 + LXQt + XRDP + SSH + Static IP + 4GB/4c + /data + reusable image | **Done** | `ubuntu-lxqt-01` @ 192.168.220.104 |
| 2 | Podman: Ubuntu 26.04 SSH-only + Static IP + 4GB/4c + /data + reusable image | **Done** | `ubuntu-ssh-02` @ 192.168.220.106 |
| 3 | Podman: Rocky Linux 10.2 minimal + SSH + Static IP + 4GB/4c + /data + reusable image | **Done** | `rocky-ssh-01` @ 192.168.220.107 |
| 4 | Reusable KVM image: Rocky Linux minimal + SSH | **Done** | `rocky-ssh-template` @ 192.168.220.109 + clone `rocky-ssh-02` @ .110 |
| 5 | Reusable KVM image: Ubuntu latest LTS + LXQt only + SSH | **Done** | `ubuntu-lxqt-test01` @ 192.168.220.108 + clone `ubuntu-lxqt-02` @ .111 |

---

## Verification Snapshot (2026-10-19)

```bash
sudo virsh list --all | grep -E 'ubuntu-lxqt|rocky-ssh'
#  rocky-ssh-template   running
#  rocky-ssh-02         running
#  ubuntu-lxqt-test01   running
#  ubuntu-lxqt-02       running

# SSH checks passed for:
# 192.168.220.108  ubuntu-lxqt-test01  (LXQt + XRDP + SSH)
# 192.168.220.111  ubuntu-lxqt-02      (clone)
# 192.168.220.109  rocky-ssh-template
# 192.168.220.110  rocky-ssh-02
```

All five todos are complete and verified.

---

**End of STATUS.md**
