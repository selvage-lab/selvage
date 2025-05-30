# TestPyPI 테스트용 사전 구성된 도커 이미지
# 의존성은 미리 설치하고, selvage는 TestPyPI에서 설치하여 테스트

FROM python:3.11-slim

# 시스템 패키지 업데이트 및 필요한 도구 설치
RUN apt-get update && apt-get install -y \
  git \
  && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# pyproject.toml 복사 (의존성 정보만 필요)
COPY pyproject.toml /app/

# pip 업그레이드
RUN pip install --upgrade pip

# pyproject.toml에서 의존성만 설치 (selvage 자체는 제외)
# 임시로 toml 패키지 설치하여 의존성 추출
RUN pip install toml && \
  python -c "import toml; data = toml.load('pyproject.toml'); print('\n'.join(data['project']['dependencies']))" > /tmp/deps.txt && \
  pip install -r /tmp/deps.txt && \
  rm /tmp/deps.txt

# 컨테이너가 계속 실행되도록 설정
CMD ["bash", "-c", "while true; do sleep 1; done"] 
