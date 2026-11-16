# =============================================================================
# VisionForensics AI — Frontend Pilot Container Dockerfile
# Nginx 1.27 Alpine Static Serving & Reverse Proxy
# =============================================================================

FROM nginx:1.27-alpine AS runtime

# Remove default Nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy pre-compiled frontend SPA production build
COPY dist /usr/share/nginx/html

# Copy TLS certificates for pilot HTTPS termination
COPY certs /etc/nginx/certs
RUN chmod 600 /etc/nginx/certs/pilot.key && \
    chmod 644 /etc/nginx/certs/pilot.crt && \
    chmod 644 /etc/nginx/certs/pilot_ca.crt && \
    chown -R root:nginx /etc/nginx/certs

# Copy pilot Nginx reverse proxy configuration
COPY nginx.pilot.conf /etc/nginx/conf.d/default.conf
COPY security-headers.conf /etc/nginx/security-headers.conf

EXPOSE 80 443

HEALTHCHECK --interval=20s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --no-check-certificate --spider https://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
