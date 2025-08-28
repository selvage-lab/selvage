#!/bin/bash
# TestPyPI 이미지 빌드 스크립트
# 항상 최신 버전을 가져오도록 캐시 무력화

set -e

echo "🚀 Building TestPyPI Docker image with latest selvage version..."

# 현재 timestamp를 CACHEBUST 인자로 전달하여 캐시 무력화
TIMESTAMP=$(date +%s)

docker build \
    --no-cache \
    --build-arg CACHEBUST=$TIMESTAMP \
    -t selvage-testpypi:latest \
    -f e2e/dockerfiles/testpypi/Dockerfile \
    .

echo "✅ Docker image built successfully!"

# 설치된 버전 확인
echo "📦 Installed selvage version:"
docker run --rm selvage-testpypi:latest selvage --version