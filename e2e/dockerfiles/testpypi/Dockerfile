# TestPyPI 테스트용 사전 구성된 도커 이미지
# TestPyPI에서 selvage를 직접 설치하여 실제 배포 환경과 동일하게 테스트

FROM python:3.11-slim

# 시스템 패키지 업데이트 및 필요한 도구 설치
RUN apt-get update && apt-get install -y \
  git \
  && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# pip 업그레이드
RUN pip install --upgrade pip

# TestPyPI에서 selvage 설치 (의존성 포함)
# ARG를 사용해서 빌드 시마다 캐시 무력화
ARG CACHEBUST=1
RUN pip install --no-cache-dir --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple selvage

# 컨테이너가 계속 실행되도록 설정
CMD ["bash", "-c", "while true; do sleep 1; done"] 
