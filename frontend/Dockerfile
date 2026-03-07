# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar manifests primeiro (camada cacheada se deps não mudarem)
COPY package.json ./

RUN npm install --ignore-scripts

# Copiar código e buildar
COPY . .
RUN npm run build


# ── Stage 2: Production (Nginx) ───────────────────────────────────────────────
FROM nginx:alpine AS production

# Remover config padrão do nginx
RUN rm /etc/nginx/conf.d/default.conf

# Config customizada: gzip, cache, proxy /api e /ws, SPA fallback
COPY nginx.conf /etc/nginx/conf.d/logia.conf

# Copiar build do Vite
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
