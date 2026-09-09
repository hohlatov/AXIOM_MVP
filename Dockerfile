# ====================
# STAGE 1: Build Frontend
# ====================
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY axiom-frontend/package*.json ./
RUN npm install
COPY axiom-frontend/ ./
RUN npm run build

# ====================
# STAGE 2: Build Backend
# ====================
FROM python:3.11-slim AS backend-builder
WORKDIR /app/backend
COPY axiom-backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY axiom-backend/ ./

# ====================
# STAGE 3: Final Image
# ====================
FROM python:3.11-slim
WORKDIR /app

# Copy backend
COPY --from=backend-builder /app/backend /app/backend
WORKDIR /app/backend

# Copy frontend static files (if needed for serving)
COPY --from=frontend-builder /app/frontend/.next /app/frontend/.next

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Expose ports
EXPOSE 8000

# Run backend
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]