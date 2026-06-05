# Proxy Integration

Fast LiteLLM accelerates LiteLLM through import-time monkeypatching. When running the LiteLLM proxy server, the key requirement is ensuring `fast_litellm` is imported **before** the proxy server loads `litellm`.

## Gunicorn

### Wrapper Module (Recommended)

The simplest approach is a two-line wrapper module combined with gunicorn's `--preload` flag.

**Create `app.py`:**

```python
import fast_litellm  # Apply acceleration before litellm loads
from litellm.proxy.proxy_server import app
```

**Run with gunicorn:**

```bash
gunicorn app:app --preload -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:4000
```

The `--preload` flag loads the app in the master process before forking workers. This means:

- Fast LiteLLM patches LiteLLM once in the master process
- All workers inherit the accelerated components
- No redundant patching overhead per worker

### Gunicorn Config File

For more control, use a gunicorn configuration file.

**Create `gunicorn_conf.py`:**

```python
import fast_litellm  # Applied before workers fork

# Server socket
bind = "0.0.0.0:4000"

# Worker processes
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"

# Timeouts
timeout = 120
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

def on_starting(server):
    """Called before the master process is initialized."""
    print("Fast LiteLLM acceleration enabled")

def post_fork(server, worker):
    """Called after a worker has been forked."""
    import fast_litellm
    if fast_litellm.RUST_ACCELERATION_AVAILABLE:
        print(f"Worker {worker.pid}: Rust acceleration active")
```

**Run with:**

```bash
gunicorn litellm.proxy.proxy_server:app -c gunicorn_conf.py
```

## Docker

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY gunicorn_conf.py .

EXPOSE 4000

CMD ["gunicorn", "app:app", "-c", "gunicorn_conf.py"]
```

**requirements.txt:**

```
fast-litellm
litellm
gunicorn
uvicorn
```

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  litellm-proxy:
    build: .
    ports:
      - "4000:4000"
    environment:
      - FAST_LITELLM_RUST_ROUTING=enabled
      - FAST_LITELLM_RUST_RATE_LIMITING=enabled
      - LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
    volumes:
      - ./litellm_config.yaml:/app/litellm_config.yaml
    command: >
      gunicorn app:app
      --preload
      -w 4
      -k uvicorn.workers.UvicornWorker
      -b 0.0.0.0:4000
```

## systemd

Create `/etc/systemd/system/litellm-proxy.service`:

```ini
[Unit]
Description=LiteLLM Proxy with Fast LiteLLM Acceleration
After=network.target

[Service]
Type=notify
User=litellm
Group=litellm
WorkingDirectory=/opt/litellm
Environment="PATH=/opt/litellm/venv/bin"
Environment="FAST_LITELLM_RUST_ROUTING=enabled"
Environment="FAST_LITELLM_RUST_RATE_LIMITING=enabled"
ExecStart=/opt/litellm/venv/bin/gunicorn app:app \
    --preload \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:4000
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable litellm-proxy
sudo systemctl start litellm-proxy
```

## Verifying Acceleration

Add a custom health endpoint to confirm acceleration is active in each worker:

```python
import fast_litellm
from litellm.proxy.proxy_server import app

@app.get("/acceleration/health")
async def acceleration_health():
    return fast_litellm.health_check()

@app.get("/acceleration/stats")
async def acceleration_stats():
    return fast_litellm.get_performance_stats()
```

Then:

```bash
curl http://localhost:4000/acceleration/health
curl http://localhost:4000/acceleration/stats
```

## Common Issues

### Acceleration Not Applied

If `RUST_ACCELERATION_AVAILABLE` is `False`:

1. Ensure `fast_litellm` is imported before `litellm`.
2. Use `--preload` with gunicorn so patches apply once in the master.
3. Verify the Rust extension is installed: `python -c "import fast_litellm._rust"`.

### Worker Isolation

If different workers report different acceleration status, you forgot `--preload`. Always preload so all workers inherit the same patched modules.

## Next Steps

- [Configuration](configuration.md) - Feature flags and environment variables
- [Monitoring](monitoring.md) - Health checks, metrics, and alerts
- [Troubleshooting](troubleshooting.md) - Diagnose common runtime issues
