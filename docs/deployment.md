# Deployment Guide

**Last updated:** 2026-06-07 (rev 2)

---

## Production URLs

| Service | URL |
|---------|-----|
| Frontend (HTTPS) | https://d2ttyqgmp7bw35.cloudfront.net |
| Backend health | https://d2ttyqgmp7bw35.cloudfront.net/api/health |
| API base | https://d2ttyqgmp7bw35.cloudfront.net/api |

---

## Deploy via GitHub Actions (normal flow)

Push to the `dev` branch — CI does everything automatically:

```bash
git push origin dev
```

Watch progress at: **GitHub → Actions → Deploy to AWS (dev)**

---

## Manual ECS Deployment

Use when you need to redeploy without a code change (e.g. after infra fix).

```bash
# Provide fresh credentials first
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."

aws ecs update-service \
  --region us-east-1 \
  --cluster bohu \
  --service bnpl-backend-service \
  --force-new-deployment
```

---

## Update Task Definition (CPU/Memory)

Edit `ecs-task-definition.json`, then:

```bash
# Register new revision
aws ecs register-task-definition \
  --region us-east-1 \
  --cli-input-json file://ecs-task-definition.json

# Update service to new revision
aws ecs update-service \
  --region us-east-1 \
  --cluster bohu \
  --service bnpl-backend-service \
  --task-definition bnpl-backend:<revision> \
  --force-new-deployment
```

Current spec: **2 vCPU / 4 GB RAM** (task revision 4+)

---

## Update Secrets

```bash
# Update DATABASE_URL
aws ssm put-parameter \
  --region us-east-1 \
  --name /bnpl/prod/DATABASE_URL \
  --value "postgresql+asyncpg://user:pass@host:5432/db" \
  --type SecureString \
  --overwrite

# Update local LLM auth token
aws ssm put-parameter \
  --region us-east-1 \
  --name /bnpl/prod/LOCAL_LLM_AUTH \
  --value "Bearer <token>" \
  --type SecureString \
  --overwrite

# Update OpenRouter API key
aws ssm put-parameter \
  --region us-east-1 \
  --name /bnpl/prod/OPENROUTER_API_KEY \
  --value "sk-or-v1-..." \
  --type SecureString \
  --overwrite
```

Then force a new ECS deployment to pick up the new values.

---

## Invalidate CloudFront Cache

After a manual S3 upload (not via CI):

```bash
aws cloudfront create-invalidation \
  --distribution-id E254OK1RKJMEXA \
  --paths "/*"
```

---

## Check ECS Task Logs

```bash
# Latest log stream
aws logs describe-log-streams \
  --region us-east-1 \
  --log-group-name /ecs/bnpl-backend \
  --order-by LastEventTime --descending \
  --limit 1

# Tail logs (replace stream name)
aws logs get-log-events \
  --region us-east-1 \
  --log-group-name /ecs/bnpl-backend \
  --log-stream-name ecs/bnpl-backend/<task-id> \
  --limit 50
```

---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `ResourceInitializationError: unable to pull secrets from SSM` | VPC endpoint SG missing inbound 443 | SG `sg-0a7250901e8ad525c` needs self-referencing inbound TCP 443 |
| `AccessDeniedException: logs:CreateLogGroup` | Missing IAM policy on execution role | Add `logs:CreateLogGroup` to `ecsTaskExecutionRole` |
| `ValueError: invalid interpolation syntax` (alembic) | `%` in DATABASE_URL password | `alembic/env.py` escapes `%` → `%%` for configparser |
| `Connection refused` to RDS | RDS SG not allowing ECS | Add ECS SG to RDS SG inbound 5432 |
| `RuntimeError: Form data requires python-multipart` | Missing dependency | `python-multipart` in `requirements.txt` |
| `UniqueViolationError` on demo profile seed | Two workers race on startup | `IntegrityError` caught in `_seed_demo_profile()` |
| ECR tag already exists | Immutable tag + re-run same commit | ECR set to `MUTABLE` |

---

## Local Development

```bash
# Backend
cp .env.example .env       # set PERSISTENCE=sqlite for local
uv sync
alembic upgrade head
uvicorn app.main:create_app --factory --reload

# Frontend (no build step needed)
cd frontend
python -m http.server 8080  # or any static file server
# open http://localhost:8080
```

Or with Docker Compose:

```bash
docker compose up --build
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
```
