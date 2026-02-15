#!/bin/bash
# PyPI 배포 스크립트 (Production)
# 사용법: ./scripts/deploy_pypi.sh

set -e

echo "🚀 PyPI 배포 시작..."

# 경고 메시지
echo "⚠️  WARNING: Production PyPI 배포입니다!"
echo "   계속하려면 'yes'를 입력하세요."
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ 배포 취소됨"
    exit 0
fi

# 현재 버전 확인
CURRENT_VERSION=$(python3 -c "import sys; sys.path.insert(0, 'selvage'); from __version__ import __version__; print(__version__)")
echo "📦 현재 버전: v${CURRENT_VERSION}"

# 1. 빌드
echo "🔨 패키지 빌드 중..."
uv run python -m build

# 2. Infisical에서 PyPI 토큰 가져오기 (production 환경)
echo "🔐 Infisical에서 API 토큰 가져오는 중..."
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=$(infisical secrets get pypi --env=prod --plain)

if [ -z "$TWINE_PASSWORD" ]; then
    echo "❌ 에러: PyPI API 토큰을 가져올 수 없습니다."
    echo "   Infisical에서 'pypi' 시크릿을 확인하세요. (environment: production)"
    exit 1
fi

# 3. PyPI 업로드
echo "📤 PyPI에 업로드 중..."
uv run twine upload dist/selvage-${CURRENT_VERSION}*

# 4. 성공 메시지
echo ""
echo "✅ PyPI 배포 완료!"
echo "🔗 https://pypi.org/project/selvage/${CURRENT_VERSION}/"
echo ""
echo "설치 테스트:"
echo "  pip install selvage==${CURRENT_VERSION}"
