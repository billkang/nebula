# ── 构建阶段 ──
FROM node:20-alpine AS builder
RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app
COPY pnpm-lock.yaml pnpm-workspace.yaml ./
COPY packages/shared-ui/ ./packages/shared-ui/
COPY packages/build-engine/frontend/ ./packages/build-engine/frontend/

RUN pnpm install --frozen-lockfile
RUN pnpm --filter ./packages/build-engine/frontend run build

# ── 生产阶段 ──
FROM nginx:alpine

COPY --from=builder /app/packages/build-engine/frontend/dist /usr/share/nginx/html

RUN echo 'server { \
    listen 80; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    location /api/ { \
        proxy_pass http://backend:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
