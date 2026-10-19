# IP Usage

**IP Range (test / service VMs & containers):** 192.168.220.1 – 192.168.220.120  
**Last updated:** 2026-10-19

---

## Allocation Table

| IP              | Name                     | Host        | SSH Port | Service / Notes                              |
|-----------------|--------------------------|-------------|----------|----------------------------------------------|
| 192.168.10.101  | ddserver11               | ddserver11  | 22       | Main – Podman Nginx, apps, DNS               |
| 192.168.10.104  | ddserver14               | ddserver14  | 22       | libvirt + reusable pods/VMs                  |
| 192.168.10.105  | ddserver15               | ddserver15  | 22       | Pending location tracker                     |
| 192.168.122.1   | –                        | ddserver14  | –        | libvirt virbr0 gateway                       |
| 192.168.13.104  | ddserver3v4-dating       | Sr.datadisca.com | 3422 | Jump host / dating                        |
| 192.168.20.101  | Old Web Server           | –           | 2222     | Live until cutover                           |
| 192.168.220.11  | ddserver11_vm1           | ddserver11  | 22011    | Jump / test VM + RDP                         |
| 192.168.220.100 | jfrog                    | ddserver14  | 22       | JFrog Artifactory                            |
| 192.168.220.101 | ubuntu-voice-clone       | ddserver14  | 22       | Pinokio + Fooocus                            |
| 192.168.220.102 | ocp_rocky1               | ddserver14  | 22       | Rocky Linux 9.8 (8c/16G)                     |
| 192.168.220.104 | ubuntu-lxqt-01 (podman)  | ddserver14  | 22       | Ubuntu LXQt + XRDP reusable                  |
| 192.168.220.106 | ubuntu-ssh-02 (podman)   | ddserver14  | 22       | Ubuntu SSH reusable                          |
| 192.168.220.107 | rocky-ssh-01 (podman)    | ddserver14  | 22       | Rocky 10.2 SSH reusable                      |
| 192.168.220.108 | ubuntu-lxqt-test01 (KVM) | ddserver14  | 22       | Ubuntu 26.04 LXQt + XRDP (template)          |
| 192.168.220.109 | rocky-ssh-template (KVM) | ddserver14  | 22       | Rocky 9.8 minimal SSH template               |
| 192.168.220.110 | rocky-ssh-02 (KVM)       | ddserver14  | 22       | Clone of rocky-ssh-template                  |
| 192.168.220.111 | ubuntu-lxqt-02 (KVM)     | ddserver14  | 22       | Clone of ubuntu-lxqt-test01                  |
| 115.186.215.191 | –                        | datadisca.com | –      | Public NAT                                   |

---

## Network Summary

| Network         | Purpose                                      |
|-----------------|----------------------------------------------|
| 192.168.10.0/16 | Main LAN (ddserver11 / ddserver14)           |
| 192.168.122.0/24| libvirt virbr0 secondary                     |
| 192.168.220.0/16| Test / service VMs + reusable containers     |
| 192.168.13.0/24 | Dating / jump                                |
| 192.168.20.0/24 | Old web (until cutover)                      |

---

## Free IPs (suggested for new instances)

Use any unused address in `192.168.220.112` – `192.168.220.120` (or higher) after checking the table above.

---

**Document updated:** 2026-10-19
