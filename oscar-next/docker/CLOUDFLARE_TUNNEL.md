# Cloudflare Tunnel Setup

One-time setup in the Cloudflare dashboard. Takes ~5 minutes.

## Step 1 — Create the tunnel

1. Go to **Cloudflare dashboard → Zero Trust → Networks → Tunnels**
2. Click **Create a tunnel** → choose **Cloudflared**
3. Name it: `oscar-emr`
4. Copy the tunnel token — paste it into `docker/.env` as `CLOUDFLARE_TUNNEL_TOKEN`

## Step 2 — Configure routes (in the dashboard)

Add these public hostnames in the tunnel config:

| Subdomain | Domain | Service |
|---|---|---|
| `app` | `yourdomain.com` | `http://oscar-web:3000` |
| `api` | `yourdomain.com` | `http://oscar-api:8000` |
| `auth` | `yourdomain.com` | `http://keycloak:8080` |

The service names (`oscar-web`, `oscar-api`, `keycloak`) resolve via Docker's internal DNS
because `cloudflared` runs on the same `oscar_back-tier` network.

## Step 3 — Update .env

```
APP_DOMAIN=app.yourdomain.com
API_DOMAIN=api.yourdomain.com
KEYCLOAK_PUBLIC_HOST=auth.yourdomain.com
KEYCLOAK_PUBLIC_PORT=443
CLOUDFLARE_TUNNEL_TOKEN=<paste token here>
```

## Step 4 — Update Keycloak realm

After the tunnel is live, update the Keycloak `oscar` realm redirect URIs
to include your real domain:
- `https://app.yourdomain.com/*`

Do this in: Keycloak admin (`https://auth.yourdomain.com`) → Clients → oscar-web → Valid redirect URIs

## Step 5 — Start everything

```bash
cd oscar-next/docker
docker compose --env-file .env up -d
```

## Security notes

- Cloudflare handles TLS — all traffic to `*.yourdomain.com` is HTTPS
- Internal container-to-container traffic stays on `oscar_back-tier` network (never leaves the host)
- No ports need to be opened on your firewall — tunnel is outbound-only
- Enable Cloudflare Access policy on `api.*` and `auth.*` subdomains for extra protection
