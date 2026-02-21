# Frontend Dockerfile — multi-stage: build + nginx
# Vite build, static served by nginx

# --- Build stage ---
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./

# Build-time API URL (baked into static)
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm ci

COPY . .
RUN npm run build

# --- Runtime stage — nginx ---
FROM nginx:alpine

# Copy built static from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# SPA config: fallback to index.html for client-side routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 5173

CMD ["nginx", "-g", "daemon off;"]
