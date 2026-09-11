# ==============================================================================
# CampusFlow Frontend Dockerfile — Multi-Stage Build
# ==============================================================================

# Stage 1: Node Build Stage
FROM node:22-alpine AS build

WORKDIR /app

# Install dependencies deterministically
COPY package.json package-lock.json ./
RUN npm ci

# Copy source code and build production bundle
COPY . .

# Build-time argument for API URL (defaults to reverse-proxy route /api/v1)
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build


# Stage 2: Unprivileged Nginx Runtime
FROM nginx:alpine AS runner

# Replace default Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy production static assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Configure file ownership and runtime directories for non-root nginx user
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

USER nginx

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://localhost:8080/nginx-health || exit 1

CMD ["nginx", "-g", "daemon off;"]
