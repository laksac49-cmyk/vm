## 2026-10-28
1. Install a virtual machine on ddserver15 with following features
   1. Static IP
   2. Ubuntu 26.04LTS
   3. LXQt (only if not possible XFCE4) desktop env. No other desk should be present (No GNome, No KDE, No XFCE etc etc)
   4. XRDP
   5. SSH Access
   6. Memory 6GB, CPU 4 Cores
   7. Edge browser
   8. Document how to do it
2. Install the location server on the machine. Document how to do it.
3. Put all passwords in the cliq-notebook
4. Clean all unused podman containers, images and virtual machines on all the machines.

## 2026-10-21
1. Server ddserver15 - 192.168.10.105.
    1. Add a RustDesk Podman Container. You can directly download a container. You do not have to install from scratch.
      -- Use the keys in ddserver13: 192.168.10.103, /data/rustdesk 
   

## 2026-10-20
1. Move Container/VM creation documents git markdown into a new branch called container_and_vm_scripts. 


## Extra Set
1. Find and document how to install edge browser on our ubuntu podman container with gui.
2. Create a podman container with fully functioning edge browser
3. Document how to do it

## 2026-10-10 Set 2.  
Server ddserver15 - 192.168.10.105.  
1. Add ddserver15 to your documentation
2. Use the podcontainer with GUI previously made.
3. Install location tracker in that. It should work with API and Browser MAP.
4. Test with your location.

## 2026-10-10

Target:
- Document all how to do. This is an exercise for future use.     
- Create reusuabe images or rapid deployment code.      
- We should be able to change the memory and cpu cores when we create new instances.   
- We should be able to create anew pod or a VM within 10 mins of the request.   

1. Create a podman container with the following featues
    1. Static IP
    2. Ubuntu 26.04LTS
    3. LXQt (only if not possible XFCE4) desktop env. No other desk should be present (No GNome, No KDE, No XFCE etc etc)
    4. XRDP
    5. SSH Access
    6. Memory 4GB, CPU 4 Cores
    7. /data/pod_disks/<container_name> mounted as /data
    8. Create a reusable image out of that.
2. Create a podman container with the following featues
    1. Static IP
    2. Ubuntu latest 26.04LTS    3. 
    4. SSH Access
    5. Memory 4GB, CPU 4 Cores
    6. /data/pod_disks/<container_name> mounted as /data
    7. Create a reusable image out of that.
 3. Create a podman container with the following featues
    1. Static IP
    2. Roky linux minimal 10.2
    3. SSH
    4. Memory 4GB, CPU 4 Cores
    5. /data/pod_disks/<container_name> mounted as /data
    5. Create a reusable image out of that.
 4. Create a reusable KVM Image of roky linux minimal with SSH access
 5. Create a reusable KVM Image of
    1. Ubuntu latest LTS
    2. LXQt desktop env. No other desk should be present (No GNome, No KDE, No XFCE etc etc)
    3. SSH Access
       



## 2026-10-09.     
1.I have to add rockey linux vm in ddserver14 which have same spects jfrog vm which is also in ddserver14 machine.Give a new static IP,     
It should be accessible via ssh from the outside (example : jumphost).     
install https://download.rockylinux.org/pub/rocky/9/isos/x86_64/Rocky-9.8-x86_64-minimal.i.  
vmname= ocp_rocky1. 


## 2026-10-07
1. Change the new jump host on ddserver11 to use static ip 192.168.220.11/16 gateway 192.168.0.1. Checkdirect  access from your home using port 2201
2.  Makesure everything persists restarts
3.  Copy podman images to /data/podman_images. Dodument the user of image. Image Name, service,created date 
   
## 2026-10-05
1. Point mm.int.datadisca.com pinokio.int.datadisca.com foocus.int.datadisca.com to 115.186.215.191 using the dns configuration on the dns pod
     - Use dig and tools on the internet to verify the new subdomain and the hosts are working.
2. Make the certificate valid
     - Get certificate for int.datadisca.com domain and add to the hosts of that
3. Renew the certificates of datadisca.com and tmgpm.com.au make sure they are automatically updated on the new nginx pod.

## 2026-10-03

| # | Task | Status | Proof / notes |
|---|------|--------|----------------|
| 1 | DNS pod listen on default DNS port **53** (ddserver11) | ✅ Done | CoreDNS on `192.168.10.101:53` (not 5353). `dig @192.168.10.101 mm.int.datadisca.com +short` → 192.168.10.101 |
| 2 | ddserver11 restart → all pods, VMs, services auto-start (no manual intervention) | ✅ Done | After reboot: nginx-web, coredns, matchmaking, postgres Up; tunnel active; vm1 running; HTTP 200 |
| 3 | `mm.int.datadisca.com` from new jump host (ddserver11_vm1) → matchmaking site | ✅ Done | DNS + Nginx; `http://mm.int.datadisca.com` → **200** from vm1 (portless) |
| 4 | `pinokio.int.datadisca.com` from new jump host → Pinokio | ✅ Done | Reverse proxy → :14200 tunnel; **200** from vm1 |
| 5 | `fooocus.int.datadisca.com` from new jump host → Fooocus | ✅ Done | Reverse proxy → :17860 tunnel; **200** from vm1 |
| 6 | Other sites from original webserver still work on new Nginx | ✅ Done | datadisca/www/ai/webtest/tmgpm **200**; sr **302**; matchmaking path **200**; old web still 200 until format |
| 7 | Remove unnecessary pods/images; document required in `podman_containers.md` | ✅ Done | Removed nginx:alpine, alpine, certbot. Table-only `podman_containers.md` |
| 8 | Create images of running pods (deploy on another machine) | ✅ Done | commit + save in `~/podman-exports/` (~1.8G); tags `localhost/datadisca-*:2026-10-03` |



## 2026-09-24
1. Show that the new jump host on ddserver11 can be accessed from matchmaking jumphost with GUI
2. Show new nginx and reverse proxy is working
    1. Configure www.datadisca.com and the other site /etc/hosts and show website loading on the jump host
    2. Show reverse proxies for matchmaking, video analysis, travel news are also working with new nginx
3.Create a virtual machine that we can use as another jump host. It should have ubuntu 26.04 LTS latest stable version, 4 cores 8gb memery 100GB HDD

# DataDisca Migration — TODO Tracker

**Last updated:** 2026-09-27  
**Related:** `DataDisca-Migration-README.md`

---

## Completed

### 2026-09-24

| # | Task | Status | Proof / notes |
|---|------|--------|----------------|
| 1 | Show that the new jump host on **ddserver11** can be accessed from matchmaking jumphost **with GUI** | ✅ Done | SSH: dating → `ssh nma@192.168.10.101`. GUI: Cockpit `https://192.168.10.101:9090/` |
| 2 | Show new **Nginx and reverse proxy** is working | ✅ Done | `podman ps`; curl root/mm/docs/api-direct all **200** on ddserver11 |
| 2.1 | Configure **www.datadisca.com** and other sites in **`/etc/hosts`** and show website loading on the jump/test host | ✅ Done | On **ddserver11_vm1**: hosts → 192.168.10.101; curl :8443 → **200** for root, www, ai, mm, tmgpm, webtest |
| 2.2 | Show reverse proxies for **matchmaking**, video analysis, **travel news** with new Nginx | ✅ Partial / by design | **Matchmaking** ✅ 200 + `host.containers.internal:8001`. **Travel (tmgpm.com.au)** ✅ 200. **Video analysis API** ⏭ **Skipped** (502; not migrated). Pinokio/Fooocus ✅ via tunnel |
| 3 | Create a virtual machine as another jump host: **Ubuntu 26.04 LTS**, 4 cores, 8 GB memory, 100 GB HDD | ✅ Done | **ddserver11_vm1** — Ubuntu 26.04, IP `192.168.220.11`, used for `/etc/hosts` verification and jump-style access from ddserver11 |

### 2026-09-25

| # | Task | Status | Proof / notes |
|---|------|--------|----------------|
| 4 | Pinokio + Fooocus permanent SSH tunnel | ✅ Done | systemd user service `pinokio-fooocus-tunnel`; ports 14200/17860; linger=yes |
| 5 | Fix **sr.datadisca.com** (404 → working) | ✅ Done | Root 302 → /pinokio/; pinokio/fooocus via tunnel **200** |
| 6 | Stakeholder verification path documented (SSH, Cockpit, hosts, access.log) | ✅ Done | See README §11, §14 |

### 2026-09-27

| # | Task | Status | Proof / notes |
|---|------|--------|----------------|
| 7 | Add **internal DNS** name **`int.datadisca.com`** to Podman CoreDNS on ddserver11 | ✅ Done | Corefile hosts: `192.168.10.101 int.datadisca.com`. Verify: `dig @192.168.10.101 -p 5353 int.datadisca.com +short` → **192.168.10.101**. Head-end IP (when assigned) → one-line Corefile update + `podman restart coredns` |
| 8 | Ensure **ddserver11** remains in internal DNS map | ✅ Done | Already present; re-verified with dig |

---

## Pending (production cutover)

| # | Task | Owner / notes |
|---|------|----------------|
| P1 | Router: public **80** → `192.168.10.101:8080` | Keep SSH 22/2222 unchanged |
| P2 | Router: public **443** → `192.168.10.101:8443` | |
| P3 | Public test from **mobile data** (all main sites + matchmaking + fooocus/sr) | |
| P4 | Confirm nginx access.log shows real public client IPs | `podman exec nginx-web tail -f /var/log/nginx/access.log` |
| P5 | Certbot renew dry-run after port 80 hits ddserver11 | |
| P6 | **Format old web server** (`192.168.20.101`) | Only after P1–P4 OK |
| P7 | **Format dating server** (`192.168.13.104`) | Safe anytime (matchmaking migrated; video skipped) |
| P8 | Assign **head-end IP** for `int.datadisca.com` | Update Corefile + restart coredns when IP is confirmed |

---

## Skipped (by design)

| Item | Reason |
|------|--------|
| hikkainfo.com / `/loc/` / related APIs | Not required; will break after old web format |
| video-call backend / video_clasifier API | Not migrated; static page only |

---

## Verification commands (for demonstration)

```bash
# Access + GUI
ssh -p 3422 lahiru@Sr.datadisca.com
ssh nma@192.168.10.101
# Browser: https://192.168.10.101:9090/

# Nginx + matchmaking
podman ps
curl -sk -o /dev/null -w "mm:%{http_code}\n" -H "Host: datadisca.com" https://127.0.0.1:8443/matchmaking/

# /etc/hosts sites (from ddserver11 → vm1)
sudo ip route replace 192.168.220.11/32 dev br0
ssh nma@192.168.220.11
grep datadisca /etc/hosts
curl -sk -o /dev/null -w "www:%{http_code}\n" https://www.datadisca.com:8443/

# Internal DNS (int.datadisca.com) — 2026-09-27
dig @192.168.10.101 -p 5353 int.datadisca.com +short
# → 192.168.10.101
grep int.datadisca ~/podman-dns/config/Corefile
podman ps | grep coredns
```

---

## Config snapshot — CoreDNS hosts (2026-09-27)

```text
192.168.10.101  ddserver11
192.168.10.101  datadisca.com www.datadisca.com ai.datadisca.com
192.168.10.101  webtest.datadisca.com sr.datadisca.com
192.168.10.101  tmgpm.com.au
192.168.10.101  int.datadisca.com
192.168.220.11  ddserver11-vm1
```

File: `~/podman-dns/config/Corefile` on **ddserver11**  
Query port: **5353**

---

**End of todo.md**
