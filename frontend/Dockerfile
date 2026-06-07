# ── Stage 1: install deps (cached layer) ─────────────────────────────────────
FROM node:20-slim AS deps

RUN npm install -g pnpm

WORKDIR /app

COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
RUN pnpm install --frozen-lockfile

# ── Stage 2: dev server (default target) ─────────────────────────────────────
FROM deps AS dev

COPY . .

EXPOSE 5173

# Vite needs 0.0.0.0 to be reachable from outside the container
CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "5173"]

# ── Stage 3: production — serve static files via nginx ────────────────────────
FROM nginx:1.27-alpine AS prod

# Copy static public assets (the actual app — CDN-loaded JSX prototype)
COPY public/ /usr/share/nginx/html/

# nginx config: serve static files + proxy /api/* to the backend container
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
