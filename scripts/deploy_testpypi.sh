#!/bin/bash
# TestPyPI 배포 스크립트
# 사용법: ./scripts/deploy_testpypi.sh

set -e

echo "🚀 TestPyPI 배포 시작..."

# 현재 버전 확인
CURRENT_VERSION=$(python3 -c "import sys; sys.path.insert(0, 'selvage'); from __version__ import __version__; print(__version__)")
echo "📦 현재 버전: v${CURRENT_VERSION}"

# 1. 빌드
echo "🔨 패키지 빌드 중..."
uv run python -m build

# 2. Infisical에서 TestPyPI 토큰 가져오기 (development 환경)
echo "🔐 Infisical에서 API 토큰 가져오는 중..."
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=$(infisical secrets get testpypi --env=dev --plain)

if [ -z "$TWINE_PASSWORD" ]; then
    echo "❌ 에러: TestPyPI API 토큰을 가져올 수 없습니다."
    echo "   Infisical에서 'testpypi' 시크릿을 확인하세요. (environment: development)"
    exit 1
fi

# 3. TestPyPI 업로드
echo "📤 TestPyPI에 업로드 중..."
uv run twine upload --repository testpypi dist/selvage-${CURRENT_VERSION}*

# 4. 성공 메시지
echo ""
echo "✅ TestPyPI 배포 완료!"
echo "🔗 https://test.pypi.org/project/selvage/${CURRENT_VERSION}/"
echo ""
echo "설치 테스트:"
echo "  pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple selvage==${CURRENT_VERSION}"
