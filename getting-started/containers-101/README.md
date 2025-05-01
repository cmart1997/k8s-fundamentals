# Containers 101 – Images, Layers, and **Todo‑API** Demo

## Why Containers?

### Containers vs. Virtual Machines

![Containers vs Virtual Machines](https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Dockervsvm.jpg/1024px-Dockervsvm.jpg)

|               | **Virtual Machine (VM)** | **Container** |
|---------------|--------------------------|---------------|
| **Isolation unit** | Entire guest OS (kernel + userland) | Process group sharing host kernel |
| **Image size** | > 500 MB typical (OS + apps) | 5‑200 MB; only user‑space bits |
| **Boot time**  | 10‑120 s (BIOS, kernel, init) | < 1 s; only start *your* process |
| **Density** | Dozens per host (limited by RAM) | Hundreds–thousands per host |
| **Dev→Prod parity** | Tend to drift (different hypervisors, images) | Identical OCI image everywhere |
| **Update surface** | Guest OS **and** host OS | Host OS only |
| **Security blast‑radius** | Hypervisor boundary | Namespaces + cgroups (smaller) |

---

A VM ships an entire operating system; a container ships just **your app** and its user‑space dependencies. Less to download, less to patch, less to start. 

Containers bundle application code and its user‑space dependencies—not a full OS—yielding an order‑of‑magnitude better start‑up latency and host utilization. That efficiency underpins Kubernetes’ scheduling model.

---

## Anatomy of the Dockerfile (line‑by‑line)

```dockerfile
# syntax=docker/dockerfile:1.6
FROM python:3.12-alpine              # 1. Base layer: 5 MB Alpine + CPython
WORKDIR /app                         # 2. Working directory inside image
COPY requirements.txt .              # 3. Add dependency list (cacheable layer)
RUN pip install --no-cache-dir -r requirements.txt   # 4. Install deps once
COPY app.py .                        # 5. Add application code (changes often)
EXPOSE 8080                          # 6. Document port for humans/orchestration
ENTRYPOINT ["python", "app.py"]       # 7. The process that becomes PID 1
```

> 🔍 **Why order matters**: Changing anything above line 3 busts the cache for all later steps. Keep the fickle parts (your code) near the bottom for faster rebuilds.

---

## Quick Pre‑Flight Check – Is Docker ready?

```bash
docker --version        # Docker version 25.x
docker info | head -n 10
```

If that fails, install **Docker Desktop** (macOS/Windows) or `docker-ce` packages on Linux.

---

## Set your Docker Hub username

```bash
export DOCKER_USER=<your‑dockerhub‑id>
```

This variable keeps all subsequent commands copy‑paste friendly. Replace `<your‑dockerhub‑id>` once and forget about it.

---

## Building the `todo-api` Image

A five‑minute Flask API that keeps an **in‑memory** list—no database needed.

### 1 . Clone this directory

```bash
git clone https://github.com/cmart1997/k8s-fundamentals.git \
  && cd k8s-fundamentals/00-getting-started/containers-101
```

### 2 . Minimal project tree

```text
containers-101/
├─ app.py            # Flask API
├─ requirements.txt  # Python deps
└─ Dockerfile        # 8 lines
```

### 3 . `requirements.txt` 

```text
flask==3.0.*
```

*Why include it?* Pinning dependencies gives reproducible images and a separate layer the build cache can reuse across code‑only changes.

### 4 . Dockerfile

```dockerfile
# syntax=docker/dockerfile:1.6
FROM python:3.12-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8080
ENTRYPOINT ["python", "app.py"]
```

### 5 . app.py

```python
from flask import Flask, request, jsonify
app = Flask(__name__)
todos = []

@app.route("/todos", methods=["GET"])
def list_todos():
    return jsonify(todos)

@app.route("/todos", methods=["POST"])
def add_todo():
    todos.append(request.json["task"])
    return jsonify({"result": "added"}), 201

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

### 6 . Build, run, test

```bash
# build
docker build -t ${DOCKER_USER}/todo-api:v0.1 .

# run detached
docker run -d --name todo -p 8080:8080 ${DOCKER_USER}/todo-api:v0.1

# test endpoint
curl -X POST -H "Content-Type: application/json" \
     -d '{"task":"learn K8s"}' http://localhost:8080/todos
curl http://localhost:8080/todos   # → ["learn K8s"]
```

### 7 . Push to a registry (Docker Hub example)

```bash
docker push ${DOCKER_USER}/todo-api:v0.1
```

> 📚 **Tip:** Subsequent chapters will pull `${DOCKER_USER}/todo-api:v0.1`. Push now so your future demos "just work."

---

## Digging into Layers

```
+--------------------+  ← Layer 4  (COPY app.py)
| sha256:caf…        |
+--------------------+  ← Layer 3  (pip install flask)
| sha256:beef…       |
+--------------------+  ← Layer 2  (COPY requirements.txt)
| sha256:feed…       |
+--------------------+  ← Layer 1  (python:3.12-alpine)
```

Each Dockerfile directive after `FROM` creates a layer. Shared instructions = shared cache.

---

## CMD vs ENTRYPOINT 

|          | **CMD**                  | **ENTRYPOINT**                      |
| -------- | ------------------------ | ----------------------------------- |
| Purpose  | Default *args*           | Default *command*                   |
| Override | `docker run image args…` | `docker run --entrypoint cmd image` |

---

## 16 Docker Power‑User Commands

| #  | Command                                                                             | Why it’s cool                                                         |                                                |                           |
| -- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------- | ------------------------- |
| 1  | `docker image history ${DOCKER_USER}/todo-api`                                      | Visualize each layer & size delta.                                    |                                                |                           |
| 2  | `docker inspect ${DOCKER_USER}/todo-api:v0.1 --format '{{.RootFS.Layers}}'`         | Print layer digests.                                                  |                                                |                           |
| 3  | `docker diff $(docker create ${DOCKER_USER}/todo-api:v0.1)`                         | See filesystem changes a container makes.                             |                                                |                           |
| 4  | \`docker run --rm -it alpine:3.19 sh -c 'mount                                      | head'\`                                                               | Peek at overlayfs mounts inside the container. |                           |
| 5  | `docker run --rm --pid=host alpine:3.19 ps -e -o pid,comm,ppid`                     | Share the host PID namespace.                                         |                                                |                           |
| 6  | \`docker run --rm --network=host alpine:3.19 netstat -tulpn                         | head\`                                                                | Use host networking for quick port debugging.  |                           |
| 7  | `docker run --rm -it --privileged alpine:3.19 nsenter -t 1 -m -u -i -n sh`          | Jump from a container into the host namespaces.                       |                                                |                           |
| 8  | `docker run --rm --cgroups ns /bin/sh`                                              | Experiment with cgroup v2 nesting (Docker 24+).                       |                                                |                           |
| 9  | \`docker run --rm --read-only -v tmpfs\:/tmp alpine touch /test                     |                                                                       | echo "read-only root OK"\`                     | Enforce immutable rootfs. |
| 10 | `docker buildx bake --print`                                                        | See how BuildKit translates a `docker-compose.yml` into bake targets. |                                                |                           |
| 11 | `docker build --progress=plain .`                                                   | Show detailed build steps & cache keys.                               |                                                |                           |
| 12 | `docker exec -it $(docker ps -q --filter ancestor=${DOCKER_USER}/todo-api:v0.1) sh` | Shell into a running container without its ID.                        |                                                |                           |
| 13 | `docker events --filter 'event=resize'`                                             | Stream real-time Docker daemon events.                                |                                                |                           |
| 14 | `docker system df`                                                                  | Disk usage by images, containers, volumes, build cache.               |                                                |                           |
| 15 | `docker volume create data && docker run -v data:/data alpine du -sh /data`         | Touch a persistent volume.                                            |                                                |                           |
| 16 | `docker build --target builder -f Dockerfile.multi -t tmp .`                        | Stop a multi-stage build mid-pipeline.                                |                                                |                           |

---

## How containers really start up 🛠️ 

1. **CLI** — `docker run python:3.12-alpine echo hi` parses flags & POSTs JSON to **dockerd** via REST/Unix socket.  
2. **dockerd → containerd** — The daemon hands the request to **containerd**, the lower‑level runtime manager.  
3. **containerd → runc** — containerd forks a **shim** per container then execs **runc** (the OCI runtime).  
4. **runc** — Generates an OCI spec, `pivot_root`‑s into the image rootfs, configuring:
   * **Namespaces:** `pid`, `net`, `mnt`, `uts`, `ipc`, optionally `user` & `cgroup`.  
   * **cgroups v2:** sets CPU, memory, and I/O limits.  
   * **Capabilities:** drops everything except a minimal set (unless `--privileged`).  
5. **OverlayFS** — Layers are mounted `upperdir + lowerdir → merged`. The container sees a unified root.  
6. **Init process (PID 1)** — Your `ENTRYPOINT` becomes PID 1, inheriting signal quirks (hence `tini` or `dumb-init` in prod images).  
7. **dockerd events** — Emits `create → start → attach`. Your command runs, exits 0, shim captures exit code, containerd updates status, Docker CLI returns.  

---

## Where this is headed → microservices!

* **Workloads ▶️ Pods & Deployments:** turn `todo-api` into a ReplicaSet and watch rolling updates.
* **Networking ▶️ Services & Ingress:** expose the API to the cluster and the internet.
* **Storage ▶️ PVCs:** swap in a proper database pod and mount persistent volume claims.
* **Observability ▶️ Metrics & Logging:** scrape Flask metrics, ship JSON logs to Loki.
* **Security ▶️ RBAC & PSP/PSA:** confine the container, drop capabilities, enforce read‑only root.

---

We’ll split the Todo‑API into front‑end, auth, worker, and DB layers—each showcasing Deployments, Services, ConfigMaps, Secrets, Ingress, Autoscaling, and more.

