# ── Stage 1: Build React app ─────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG REACT_APP_API_URL=/api
ENV REACT_APP_API_URL=$REACT_APP_API_URL
RUN npm run build

# ── Stage 2: Serve with NGINX ────────────────────────
FROM nginx:1.25-alpine
RUN addgroup -S nginxapp && adduser -S -G nginxapp nginxapp

COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN chown -R nginxapp:nginxapp /usr/share/nginx/html && \
    chown -R nginxapp:nginxapp /var/cache/nginx && \
    chown -R nginxapp:nginxapp /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown nginxapp:nginxapp /var/run/nginx.pid

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=5s \
  CMD wget -qO- http://localhost/health || exit 1
CMD ["nginx", "-g", "daemon off;"]