#!/bin/bash
# MinIO Bucket Initialization Script for Pilah.in
# This script creates required buckets after MinIO starts

# Wait for MinIO to be ready
echo "Waiting for MinIO to be ready..."
until curl -s http://localhost:9000/minio/health/live > /dev/null; do
    sleep 1
done

echo "MinIO is ready. Initializing buckets..."

# Create buckets using mc (MinIO Client)
mc alias set pilah http://localhost:9000 "${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}"

# Create buckets
mc mb pilah/pilah-uploads
mc mb pilah/pilah-models
mc mb pilah/pilah-education

# Set policies (public read for uploads, private for models)
mc policy set public pilah/pilah-uploads
mc policy set download pilah/pilah-models

echo "Buckets initialized successfully!"
echo "Available buckets: pilah-uploads, pilah-models, pilah-education"

# List buckets
echo "Buckets list:"
mc ls pilah
