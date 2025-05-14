````markdown
# Local Dev Clusters — kind, k3d, Minikube & k3s Playgrounds

Welcome to **Local Dev Clusters**—a zero‑cost, laptop‑friendly Kubernetes sandbox.  
In < 30 minutes you will:

* Compare **kind**, **k3d**, **Minikube**, and **k3s** and know when to reach for each  
* Spin up a single‑node cluster on macOS, Linux, or Windows (WSL / Git Bash)  
* Deploy and reach a *Hello‑Kubernetes* web app  
* Explore 18 must‑know `kubectl` commands  
* Understand the control‑plane & data‑plane pieces running under the hood  
* Scrap everything with one command—fearless experimentation encouraged!

Everything below is **copy‑paste ready**.  
Prerequisites: **Docker Engine ≥ 20.10** (except k3s bare‑metal), **kubectl**, and a POSIX‑ish shell (Bash, Zsh, Git Bash, PowerShell ≥ 7).

---

## Laptop Sandbox vs Cloud Cluster

|                    | **Cloud‑Hosted Cluster** | **Local Dev Cluster** |
|--------------------|--------------------------|-----------------------|
| **Spin‑up time**   | 5 – 15 min (API + nodes) | 20 – 120 s total |
| **Cost**           | $0.10 – $3 / hr (managed)| **Free** |
| **Offline travel** | ❌ Requires internet     | ✅ Works on a plane |
| **IAM & quotas**   | Cloud roles & limits     | None – full admin |
| **Tear‑down**      | Minutes, risk zombie $$  | `./cleanup.sh` in < 5 s |
| **Use cases**      | Load test, staging, prod | Daily dev loop, CI smoke tests |

![Kubernetes high‑level architecture](https://upload.wikimedia.org/wikipedia/commons/thumb/b/be/Kubernetes.png/800px-Kubernetes.png)

---

## 📁 Repo Layout

```text
local-dev-clusters/
├── kind/
│   ├── cluster.yaml
│   └── deploy-example.sh
├── k3d/
│   └── create-cluster.sh
├── minikube/
│   └── start.sh
├── cleanup.sh
└── README.md
````

> **Tip 🧹** — `./cleanup.sh` nukes *all* clusters so you can break things fearlessly.

---

## Quick Pre‑Flight Check

```bash
docker --version            # Docker version ≥ 20.x
kubectl version --client --short
```

macOS: Docker Desktop **or** `colima`, plus `brew install kubectl`.
Windows: enable WSL 2 + Docker Desktop; use Git Bash or PowerShell 7+.
k3s bare‑metal (below) works without Docker.

---

## Environment Variable (handy for copy‑paste)

```bash
export CLUSTER=kind-playground
```

---

## 🚀  Four Ways to Spin Up Kubernetes Locally

### 1 . kind — Docker‑native (\~30 s)

`kind/cluster.yaml` (NodePort pre‑mapped):

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 30007
        hostPort: 30007
```

```bash
cd kind
kind create cluster --name ${CLUSTER} --config cluster.yaml
./deploy-example.sh          # prints http://localhost:30007
```

*Why kind?* Pure Docker containers → super‑fast; ideal for CI.

---

### 2 . k3d — K3s in Docker (\~20 s)

```bash
cd k3d
./create-cluster.sh          # exposes demo on http://localhost:8080
```

*Why k3d?* Half the RAM of kind; great for low‑spec laptops.

---

### 3 . Minikube — Add‑on buffet (\~2 min)

```bash
cd minikube
./start.sh                   # auto‑tunnels LoadBalancer Service
```

| Driver     | OS                  | Prerequisites           |
| ---------- | ------------------- | ----------------------- |
| `docker`   | macOS / Linux / WSL | Docker Engine/Desktop   |
| `hyperkit` | macOS               | `brew install hyperkit` |
| `hyperv`   | Windows Pro         | Hyper‑V feature enabled |
| `podman`   | Fedora / RHEL       | podman ≥ 4.x            |

Switch drivers:

```bash
minikube start --driver=<driver> --cpus=2 --memory=4g
```

*Why Minikube?* Ships dashboard, Ingress, CSI, metrics‑server—closest to managed cloud.

---

### 4 . k3s bare‑metal — tiny binary (no Docker)

```bash
# install (root)
curl -sfL https://get.k3s.io | sh -

# verify
sudo kubectl get nodes
sudo k3s kubectl get pods -A

# uninstall
sudo /usr/local/bin/k3s-uninstall.sh
```

*Why k3s?* < 100 MB, zero Docker daemon—perfect for Raspberry Pi or an old laptop.

---

## 🧪  Smoke Test

```bash
kubectl get nodes -o wide
kubectl get pods -A
curl http://localhost:30007 || curl http://localhost:8080   # depending on tool
```

You should see **Hello, Kubernetes!** 🎉

---

## 🌳  Object Lineage

```
Deployment → ReplicaSet → Pod → Container
```

`kubectl apply` → **etcd** → controllers create ReplicaSet → scheduler binds Pods → kubelet pulls images → **kube‑proxy** wires Service to Pod IPs.

---

## 18 Must‑Know `kubectl` Commands

| #  | Command                                                                     | Why it’s cool                  |                |
| -- | --------------------------------------------------------------------------- | ------------------------------ | -------------- |
| 1  | `kubectl get all -A`                                                        | Snapshot everything.           |                |
| 2  | `kubectl top nodes,pods`                                                    | Live CPU/MEM (metrics‑server). |                |
| 3  | `kubectl describe node $(kubectl get nodes -o name)`                        | Capacity & events.             |                |
| 4  | `kubectl logs deploy/hello-kubernetes`                                      | Tail logs from all Pods.       |                |
| 5  | `kubectl exec deploy/hello-kubernetes -- curl -s localhost`                 | Run cmd inside Pod.            |                |
| 6  | `kubectl rollout history deploy/hello-kubernetes`                           | View RS revisions.             |                |
| 7  | `kubectl set image deploy/hello-kubernetes hello-kubernetes=nginx:alpine`   | Rolling update.                |                |
| 8  | `kubectl rollout undo deploy/hello-kubernetes`                              | Instant rollback.              |                |
| 9  | \`kubectl get events --sort-by=.metadata.creationTimestamp                  | tail\`                         | Latest events. |
| 10 | `kubectl auth can-i delete pods --as system:serviceaccount:default:default` | RBAC yes/no.                   |                |
| 11 | `kubectl explain pod.spec.containers`                                       | Field man page.                |                |
| 12 | `kubectl api-resources --verbs=list --namespaced -o name`                   | All namespaced kinds.          |                |
| 13 | `kubectl port-forward svc/hello-kubernetes 9999:80`                         | Local tunnel.                  |                |
| 14 | `kubectl label ns default env=playground --overwrite`                       | Tag namespace.                 |                |
| 15 | `kubectl taint nodes $(kubectl get nodes -o name) key=value:NoSchedule`     | Drain node.                    |                |
| 16 | `kubectl diff -f hello.yaml`                                                | Preview changes.               |                |
| 17 | `kubectl convert -f hello.yaml --local -o json`                             | Migrate API version.           |                |
| 18 | `watch -n1 kubectl get pods -o wide`                                        | Real‑time Pod watch.           |                |

---

## 🧹  Universal Cleanup

```bash
./cleanup.sh                # purges kind, k3d, Minikube clusters
```

k3s: run its uninstall script shown earlier.

---

## 🔬  How a Local Cluster Boots

1. **CLI** (`kind|k3d|minikube|k3s`) orchestrates containers or a tiny VM.
2. Control‑plane process(es): `kube‑apiserver`, `etcd`, `controller‑manager`, `scheduler`.
3. **kubelet** on each node registers via TLS bootstrap.
4. **CNI** plugin (kindnet, flannel, or Cilium) lays an overlay network; every Pod gets an IP.
5. **CoreDNS** Deployment watches Endpoints → cluster DNS.
6. **kube‑proxy** programs iptables for Services/NodePorts.
7. `kubectl apply` stores desired state in **etcd**; controllers reconcile → Pods run → Service reachable.

Everything runs **locally** yet acts exactly like EKS, GKE, or AKS—skills transfer 1‑to‑1.

---

## ➡️  Next Chapters

* **03‑workloads/pods** — probes, autoscaling, rolling updates
* **05‑networking/ingress** — NGINX, cert‑manager, HTTPS local dev
* **06‑storage/pvc‑pv** — hostPath vs CSI, snapshots
* **09‑observability/metrics** — scrape cAdvisor, Grafana dashboards

Deploy, scale, break, and roll back—all **locally** and instantly.
Happy hacking! ✌️
