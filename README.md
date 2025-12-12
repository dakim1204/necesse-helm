## 📦 Necesse Dedicated Server Helm Chart

This Helm chart deploys a Necesse Dedicated Server on Kubernetes, using the excellent [brammys/necesse-server](https://hub.docker.com/r/brammys/necesse-server) Docker image as its base.

A scheduled GitHub Actions workflow automatically fetches the latest Docker Hub tags and updates:

- Chart.yaml → appVersion
- values.yaml → image.tag

ensuring your chart always stays in sync with the latest Necesse server release.

## 🚀 Features

- Tracks and uses the latest BrammyS Necesse Docker image
- Automatic version updates via CI
- LoadBalancer (UDP) Service for game connectivity
- Persistent storage for world files and logs
- Clean and simple value overrides for server configuration
- Helm chart packaged and published to Harbor OCI Registry
- Mirror publishing to GitHub Pages for easy public consumption

## 🧱 Prerequisites

- Kubernetes 1.24+
- Helm 3.10+
- A LoadBalancer-enabled cluster (MetalLB or cloud LB)
- UDP port 14159 reachable from clients

## 📥 Installing the Chart


### Option 1: Add the GitHub-hosted Helm repo

1. Add the repo (served via GitHub Pages):

```sh
helm repo add necesse https://dakim1204.github.io/necesse-helm
helm repo update
```

2. Install the chart:

```sh
helm upgrade --install necesse-server \
  necesse/necesse-server \
  -f values.yaml
```

### Option 2: Clone the GitHub repo and install locally

If you prefer to inspect or modify the chart source:

```sh
git clone https://github.com/dakim1204/necesse-helm.git
cd necesse-server-helm
```

Install from the local directory:

```sh
helm install necesse-server ./ -f values.yaml
```

## ⚙️ Configuration (values.yaml)

Commonly used parameters:

| Key                       | Description                    | Default                                     |
| ------------------------- | ------------------------------ | ------------------------------------------- |
| `image.repository`        | BrammyS Docker repo            | `brammys/necesse-server`                    |
| `image.tag`               | Image tag (auto-updated by CI) | Latest available                            |
| `necesse.world`           | World name                     | `world`                                     |
| `necesse.password`        | Server password                | `""`                                        |
| `necesse.slots`           | Max player slots               | `10`                                        |
| `necesse.owner`           | Owner/admin name               | `""`                                        |
| `necesse.motd`            | Message of the day             | `"This server is made possible by Helm!"`   |
| `persistence.enabled`     | Enable persistent storage      | `true`                                      |
| `persistence.size`        | PVC size                       | `10Gi`                                      |
| `service.type`            | Kubernetes Service type        | `LoadBalancer`                              |
| `service.ports.game.port` | UDP port                       | `14159`                                     |

Full configuration is available inside `values.yaml`.

## 📡 Networking

The Necesse server exposes:

| Port    | Protocol | Purpose            |
| ------- | -------- | ------------------ |
| `14159` | UDP      | Game communication |

> Necesse does not support HTTP-based ingress.
> Use LoadBalancer or NodePort (UDP-enabled) instead.

💾 Persistence

The BrammyS Docker image stores data under:

```sh
/necesse/saves
/necesse/logs
```

This chart mounts a PVC at `/necesse`, ensuring world data and logs survive restarts or server upgrades.

🔄 Upgrading the Server

When the CI workflow detects a new Docker Hub release, it automatically updates:
- Chart.yaml → appVersion
- values.yaml → image.tag

After the update:

```sh
helm upgrade --install necesse-server \
  necesse/necesse-server \
  --reuse-values
```

❤️ Credits
---
- Docker image: [https://hub.docker.com/r/brammys/necesse-server](https://hub.docker.com/r/brammys/necesse-server)
  
  Special thanks to BrammyS for maintaining an excellent, frequently-updated image.
- Necesse is developed by [Fair Games ApS](https://necessegame.com/).
