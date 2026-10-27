# O painel em produção: o build do front (Vite) servido pelo Caddy, que também passa /api para a API e cuida do
# HTTPS (certificado automático para o domínio). Construído a partir da raiz do repositório.

FROM node:22-alpine AS build
WORKDIR /front
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM caddy:2-alpine
COPY docker/caddy/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /front/dist /srv/site
