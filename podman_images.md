# Podman Images Archive

**Host:** ddserver11 (`192.168.10.101`)  
**Location:** `/data/podman_images/`  
**Created:** 2026-10-08  
**Format:** `podman save | gzip` → `.tar.gz`

---

## Archived Images

```
| Image Name                              | Service      | Created    | Archive File                                      | Size  |
| --------------------------------------- | ------------ | ---------- | ------------------------------------------------- | ----- |
| localhost/datadisca-nginx:2026-10-03    | nginx-web    | 2026-10-03 | localhost_datadisca-nginx_2026-10-03.tar.gz       | 68M   |
| localhost/datadisca-coredns:2026-10-03  | coredns      | 2026-10-03 | localhost_datadisca-coredns_2026-10-03.tar.gz     | 18M   |
| localhost/datadisca-postgres:2026-10-03 | postgres     | 2026-10-03 | localhost_datadisca-postgres_2026-10-03.tar.gz    | 150M  |
| localhost/datadisca-matchmaking:2026-10-03 | matchmaking | 2026-10-03 | localhost_datadisca-matchmaking_2026-10-03.tar.gz | 87M   |
```

**Total archive size:** ~322M

---

## Restore (load) commands

```bash
# Single image
podman load -i /data/podman_images/localhost_datadisca-nginx_2026-10-03.tar.gz

# Or via gunzip pipe
gunzip -c /data/podman_images/localhost_datadisca-nginx_2026-10-03.tar.gz | podman load

# All images
for f in /data/podman_images/*.tar.gz; do
  echo "Loading $f"
  podman load -i "$f"
done

# Verify
podman images | grep datadisca
```

---

## Original base images (not archived)

```
| Image                          | Tag        | Notes                          |
| ------------------------------ | ---------- | ------------------------------ |
| docker.io/library/nginx        | 1.26       | Base for datadisca-nginx       |
| docker.io/coredns/coredns      | 1.11.3     | Base for datadisca-coredns     |
| docker.io/library/postgres     | 16         | Base for datadisca-postgres    |
| docker.io/library/python       | 3.12-slim  | Base for datadisca-matchmaking |
| docker.io/certbot/certbot      | latest     | Certbot (not committed)        |
```

---

## Notes

- Archives created with: `podman save <image> | gzip > <file>.tar.gz`
- Only `localhost/datadisca-*:2026-10-03` committed images were archived
- Base upstream images remain in local store; re-pull if needed
- Path on disk: `/data/podman_images/` (same filesystem as `/`, 915G disk)
