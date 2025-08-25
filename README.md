<h1 align="center">Selvage: AI 기반 코드 리뷰 자동화 도구</h1>

<p align="center">🌐 <a href="README_EN.md"><strong>English</strong></a></p>

<p align="center"><strong>Git diff를 AI가 분석하여 코드 품질 향상, 버그 발견, 보안 취약점 식별을 도와주는 현대적인 CLI 도구입니다.</strong></p>

<p align="center">
  <a href="https://pypi.org/project/selvage/"><img alt="PyPI" src="https://img.shields.io/pypi/v/selvage"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-Apache--2.0-blue.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.10+-blue">
  <img alt="AI Models" src="https://img.shields.io/badge/AI-GPT--5%20%7C%20Claude%20%7C%20Gemini-green">
</p>

<!-- TODO: 데모 GIF 추가 -->
<!-- <p align="center"> <img src="[데모 GIF URL]" width="100%" alt="Selvage Demo"/> </p> -->

<p align="center">
  <img src="assets/demo.gif" width="100%" alt="Selvage Demo"/>
</p>

**Selvage: 코드 리뷰도 엣지있게!**

더 이상 리뷰를 기다리지 마세요. AI가 코드 변경사항을 즉시 분석하여 품질 개선과 버그 예방을 제공합니다.  
스마트 컨텍스트 분석(AST 기반)으로 정확하고 비용 효율적이며, 멀티턴 처리로 대용량까지 - 모든 Git 워크플로우에 완벽 통합됩니다.

<details>
<summary><strong>Table of Contents</strong></summary>

- [✨ 주요 기능](#-주요-기능)
- [🚀 빠른 시작](#-빠른-시작)
- [🌐 지원 언어 및 모델](#-지원-언어-및-모델)
  - [지원 파일 형식](#지원-파일-형식)
  - [지원 AI 모델](#지원-ai-모델)
- [⌨️ CLI 사용법](#️-cli-사용법)
  - [Selvage 설정하기](#selvage-설정하기)
  - [코드 리뷰하기](#코드-리뷰하기)
  - [결과 확인하기](#결과-확인하기)
- [📄 리뷰 결과 저장 형식](#-리뷰-결과-저장-형식)
- [🛠️ 고급 사용법](#️-고급-사용법)
- [🤝 기여하기](#-기여하기)
- [📜 라이선스](#-라이선스)
- [�� 문의 및 커뮤니티](#-문의-및-커뮤니티)

</details>

## ✨ 주요 기능

- **🤖 다양한 AI 모델 지원**: OpenAI GPT-5, Anthropic Claude Sonnet-4, Google Gemini 등 최신 LLM 모델 활용
- **🔍 Git 워크플로우와 통합**: staged, unstaged, 특정 커밋/브랜치 간 변경사항 분석 지원
- **🐛 포괄적 코드 검토**: 버그 및 논리 오류 탐지, 코드 품질 및 가독성 향상 제안
- **🎯 최적화된 컨텍스트 분석**: Tree-sitter 기반 AST 분석을 통해 변경 라인이 속하는 가장 작은 코드 블록과 dependency statement를 자동 추출하여 상황에 따라 최적화된 컨텍스트 제공
- **🔄 자동 멀티턴 처리**: 컨텍스트 제한 초과 시 프롬프트를 자동 분할하여 안정적인 대용량 코드 리뷰 지원
- **📖 오픈소스**: Apache-2.0 라이선스로 자유롭게 사용 및 수정 가능

## 🚀 빠른 시작

### 1. 설치

```bash
pip install selvage
```

### 2. API 키 설정

[OpenRouter](https://openrouter.ai)에서 API 키를 발급받아 설정하세요:

```bash
export OPENROUTER_API_KEY="your_openrouter_api_key_here"
```

### 3. 코드 리뷰 시작

```bash
selvage review --model claude-sonnet-4-thinking
```

🎉 **완료!** 리뷰 결과가 터미널에 바로 출력됩니다.

**💡 더 많은 옵션:** [CLI 사용법](#️-cli-사용법) | [고급 사용법](#️-고급-사용법)

---

## ⌨️ CLI 사용법

### Selvage 설정하기

```bash
# 모든 설정 보기
selvage config list

# 기본 모델 설정
selvage config model <모델명>

```

### 코드 리뷰하기

```bash
selvage review [OPTIONS]
```

#### 주요 옵션

- `--repo-path <경로>`: Git 저장소 경로 (기본값: 현재 디렉토리)
- `--staged`: 스테이징된 변경사항만 리뷰
- `--target-commit <커밋ID>`: 특정 커밋부터 HEAD까지의 변경사항 리뷰 (예: abc1234)
- `--target-branch <브랜치명>`: 현재 브랜치와 지정된 브랜치 간 변경사항 리뷰 (예: main)
- `--model <모델명>`: 사용할 AI 모델 (예: claude-sonnet-4-thinking)
- `--open-ui`: 리뷰 완료 후 자동으로 UI 실행
- `--no-print`: 터미널에 리뷰 결과를 출력하지 않음 (기본적으로 터미널 출력 활성화)

#### 사용 예시

```bash
# 현재 워킹 디렉토리 변경사항 리뷰
selvage review

# 커밋 전 최종 점검
selvage review --staged

# 특정 파일들만 리뷰
git add specific_files.py && selvage review --staged

# PR 보내기 전 코드 리뷰
selvage review --target-branch develop

# 빠르고 경제적인 모델로 간단한 변경사항 리뷰
selvage review --model gemini-2.5-flash

# 리뷰 후 웹 UI로 자세히 확인
selvage review --target-branch main --open-ui
```

### 결과 확인하기

리뷰 결과는 **터미널에 바로 출력**되며, 동시에 파일로도 자동 저장됩니다.

**추가적인 리뷰 관리 및 재확인**을 위해 웹 UI를 사용할 수 있습니다:

```bash
# 저장된 모든 리뷰 결과를 웹 UI로 관리
selvage view

# 다른 포트에서 UI 실행
selvage view --port 8502
```

**UI 주요 기능:**

- 📋 모든 리뷰 결과 목록 표시
- 🎨 마크다운 형식 표시
- 🗂️ JSON 구조화된 결과 보기

## 🌐 지원 언어 및 모델

### 지원 파일 형식

- **Python** (`.py`)
- **JavaScript** (`.js`)
- **TypeScript** (`.ts`)
- **Java** (`.java`)
- **Kotlin** (`.kt`, `.kts`)
- **Go** (`.go`)
- **Ruby** (`.rb`)
- **PHP** (`.php`)
- **C#** (`.cs`)
- **C/C++** (`.c`, `.cpp`, `.h`, `.hpp`)
- **HTML** (`.html`)
- **CSS/SCSS** (`.css`, `.scss`)
- **Shell** (`.sh`, `.bash`)
- **SQL** (`.sql`)
- **Markdown** (`.md`)
- **JSON** (`.json`)
- **YAML** (`.yaml`, `.yml`)
- **XML** (`.xml`)
- 기타 텍스트 기반 코드 파일

### 지원 AI 모델

🚀 **OpenRouter API 키 하나로 아래 모든 모델을 통합 관리하세요!**

#### OpenAI 모델 (OpenRouter 또는 OpenAI API 키)

- **gpt-5**: 최신 고급 추론 모델 (400K 컨텍스트)
- **gpt-5-high**: ⭐ **추천** - 높은 정확도의 추론 모델 (400K 컨텍스트)
- **gpt-5-mini**: 경량화된 빠른 응답 모델 (400K 컨텍스트)

#### Anthropic 모델 (OpenRouter 또는 Anthropic API 키)

- **claude-sonnet-4**: 하이브리드 추론 모델로 고급 코딩 최적화 (200K 컨텍스트)
- **claude-sonnet-4-thinking**: ⭐ **추천** - 확장 사고 프로세스 지원 (200K 컨텍스트)

#### Google 모델 (OpenRouter 또는 Google API 키)

- **gemini-2.5-pro**: 대용량 컨텍스트 및 고급 추론 (1M+ 토큰)
- **gemini-2.5-flash**: 응답 속도와 비용 효율성 최적화 (1M+ 토큰)

#### 🌟 OpenRouter 제공 모델 (OpenRouter API 키만 필요)

- **qwen3-coder** (Qwen): ⭐ **추천** - 480B 파라미터 MoE 코딩 특화 모델 (1M+ 토큰)
- **kimi-k2** (Moonshot AI): 1T 파라미터 MoE 대용량 추론 모델 (128K 토큰)

## 📄 리뷰 결과 저장 형식

리뷰 결과는 터미널 출력과 동시에 **구조화된 파일**로 저장됩니다:

- **📋 Markdown 형식**: 사람이 읽기 편한 깔끔한 구조로 요약, 이슈 목록, 개선 제안 포함
- **🔧 JSON 형식**: 프로그래밍 방식 처리 및 다른 도구와의 통합에 활용

<p align="center">
  <img src="assets/demo-ui.png" width="100%" alt="Selvage UI Demo"/>
</p>

## 🛠️ 고급 사용법

### 다양한 Git 워크플로우와 통합

#### 팀 협업 워크플로우

```bash
# Pull Request 생성 전 코드 품질 검증
selvage review --target-branch main --model claude-sonnet-4-thinking

# 코드 리뷰어를 위한 변경사항 사전 분석
selvage review --target-branch develop --model claude-sonnet-4-thinking

# 특정 커밋 이후 모든 변경사항 종합 리뷰
selvage review --target-commit a1b2c3d --model claude-sonnet-4-thinking
```

#### 개발 단계별 품질 관리

```bash
# 개발 중 빠른 피드백 (WIP 커밋 전)
selvage review --model gemini-2.5-flash

# 스테이징된 변경사항 최종 검증 (커밋 전)
selvage review --staged --model claude-sonnet-4-thinking

# 핫픽스 배포 전 긴급 검토
selvage review --target-branch main --model claude-sonnet-4-thinking
```

### 대용량 코드 리뷰

```bash
# 대용량 코드베이스도 자동으로 처리
selvage review --model claude-sonnet-4  # 사용 방법은 동일, 자동 감지 후 멀티턴 처리 적용
```

Selvage는 LLM model의 컨텍스트 제한을 초과하는 대용량 코드 변경사항도 처리합니다.  
Long Context Mode는 자동으로 실행되니 기다리기만 하면 됩니다.

### 비용 최적화

```bash
# 작은 변경사항에는 경제적인 모델 사용
selvage review --model gemini-2.5-flash
```

## 💡 고급 설정 (개발자/기여자용)

<details>
<summary><strong>개발 및 고급 설정 옵션</strong></summary>

### 개발 버전 설치

```bash
git clone https://github.com/anomie7/selvage.git
cd selvage
pip install -e .
```

### 개발 환경 설치

```bash
# 개발 의존성 포함 설치 (pytest, build 등)
pip install -e .[dev]

# 개발 + E2E 테스트 환경 설치 (testcontainers, docker 등)
pip install -e .[dev,e2e]
```

### 개별 Provider API 키 사용

OpenRouter 대신 각 provider API 키를 개별 설정할 수도 있습니다:

```bash
export OPENAI_API_KEY="your_openai_api_key_here"
export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
export GEMINI_API_KEY="your_gemini_api_key_here"
```

### 개발 및 디버깅 설정

```bash
# 기본 사용할 모델 설정 (고급 사용자)
selvage config model claude-sonnet-4-thinking

# 설정 확인
selvage config list

# 디버그 모드 활성화 (문제 해결 및 개발시 사용)
selvage config debug-mode on
```

</details>

## 🤝 기여하기

Selvage는 오픈소스 프로젝트이며, 여러분의 기여를 언제나 환영합니다! 버그 리포트, 기능 제안, 문서 개선, 코드 기여 등 어떤 형태의 기여든 좋습니다.

**기여 방법:**

- 🐛 [GitHub Issues](https://github.com/anomie7/selvage/issues)에서 버그 리포트 또는 기능 제안
- 🔧 Pull Request를 통한 코드 기여
- 📚 문서 개선 및 번역

**상세한 기여 가이드라인은 [CONTRIBUTING.md](CONTRIBUTING.md)에서 확인하실 수 있습니다.**

## 📜 라이선스

Selvage는 [Apache License 2.0](LICENSE) 하에 배포됩니다. 이 라이선스는 상업적 이용, 수정, 배포를 허용하며, 특허 보호 및 상표권 제한을 포함한 포괄적인 오픈소스 라이선스입니다.

## 📞 문의 및 커뮤니티

- **🐛 버그 리포트 및 기능 요청**: [GitHub Issues](https://github.com/anomie7/selvage/issues)
- **📧 직접 문의**: anomie7777@gmail.com

---

<p align="center">
  <strong>Selvage와 함께 더 나은 코드를 작성하세요! 🚀</strong><br>
  ⭐ 프로젝트가 도움이 되셨다면 GitHub에서 Star를 눌러주세요!
</p>
