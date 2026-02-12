# Task 01: MCP 마켓플레이스/플러그인 등록

## 목표

selvage MCP 서버를 주요 마켓플레이스와 플러그인 디렉토리에 등록하여 GitHub star 및 사용자 유입을 늘린다.

---

## 등록 채널 목록

| 순위 | 채널 | 난이도 | 기대 효과 | 필요 작업 |
|------|------|--------|-----------|-----------|
| 1 | 공식 MCP Registry (registry.modelcontextprotocol.io) | 중 | 최고 | `server.json` 생성, README에 `mcp-name` 추가, `mcp-publisher` CLI로 퍼블리시 |
| 2 | Smithery (smithery.ai) | 중 | 높음 | `smithery.yaml` 루트에 생성, GitHub 연결 |
| 3 | Cline MCP Marketplace | 낮음 | 높음 | GitHub Issue 제출, 400x400 PNG 로고 필요 |
| 4 | Claude Plugins Official (anthropics/claude-plugins-official) | 중 | 높음 | `.claude-plugin/plugin.json` 구조, 제출 폼 작성 |
| 5 | awesome-mcp-servers (punkpeye, appcypher) | 낮음 | 중 | PR 제출만 |
| 6 | mcp.so / Glama.ai / PulseMCP / mcpmarket.com | 낮음 | 중 | 각 사이트 Submit 페이지에서 등록 |

---

## 사전 준비물 체크리스트

- [ ] `server.json` 생성 (공식 레지스트리)
- [ ] `smithery.yaml` 생성 (Smithery)
- [ ] 400x400 PNG 로고 제작 (Cline)
- [ ] README에 `mcp-name: io.github.demin-coder/selvage` 추가
- [ ] PyPI 키워드에 `mcp`, `mcp-server`, `code-review` 추가

---

## 채널별 상세 등록 절차

### 1. 공식 MCP Registry

Linux Foundation 산하 Agentic AI Foundation(AAIF)에서 관리하는 공식 레지스트리.
모든 MCP 클라이언트(Claude Desktop, Claude Code, Cursor 등)에서 검색 가능.

#### Step 1: mcp-publisher CLI 설치

```bash
# Homebrew (macOS)
brew install mcp-publisher

# 또는 바이너리 직접 다운로드
curl -L "https://github.com/modelcontextprotocol/registry/releases/download/v1.0.0/mcp-publisher_1.0.0_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/').tar.gz" | tar xz mcp-publisher && sudo mv mcp-publisher /usr/local/bin/
```

#### Step 2: server.json 초기화

```bash
mcp-publisher init
```

생성할 `server.json` 예시:

```json
{
  "$schema": "https://static.modelcontextprotocol.io/schemas/2025-07-09/server.schema.json",
  "name": "io.github.demin-coder/selvage",
  "description": "An LLM-based code review MCP server with smart context extraction",
  "version": "0.2.0",
  "packages": [
    {
      "registry_type": "pypi",
      "identifier": "selvage",
      "version": "0.2.0"
    }
  ]
}
```

#### Step 3: PyPI README에 mcp-name 추가

README.md에 아래 문자열을 포함시켜야 함 (HTML 주석도 가능):

```
mcp-name: io.github.demin-coder/selvage
```

#### Step 4: 인증 및 퍼블리시

```bash
mcp-publisher login github    # GitHub OAuth 인증
mcp-publisher publish          # 퍼블리시
mcp-publisher publish --dry-run  # 검증만 (사전 확인용)
```

#### Step 5: 등록 확인

```bash
curl "https://registry.modelcontextprotocol.io/v0/servers?search=selvage"
```

---

### 2. Smithery (smithery.ai)

MCP 서버 중앙 허브. 원클릭 설치, 자동 컨테이너화, 호스팅 서비스 제공.

#### Step 1: smithery.yaml 생성 (리포지토리 루트)

```yaml
startCommand:
  type: stdio
configSchema:
  type: object
  properties:
    api_key:
      type: string
      description: "API key for the LLM provider (optional for agent-delegated mode)"
commandFunction: |-
  (config) => ({ command: 'selvage', args: ['mcp'] })
exampleConfig: {}
```

#### Step 2: GitHub로 로그인

- https://smithery.ai/new 에서 GitHub 계정으로 로그인

#### Step 3: 리포지토리 연결 및 배포

- GitHub 리포지토리를 연결하고 `smithery.yaml`이 루트에 있는지 확인

---

### 3. Cline MCP Marketplace

Cline(VS Code AI 코딩 에이전트)의 공식 MCP 마켓플레이스. 수백만 개발자에게 노출 가능.

#### 제출 방법

[cline/mcp-marketplace](https://github.com/cline/mcp-marketplace) 리포지토리에서 Issue 생성

#### 필수 제출 항목

- **GitHub Repo URL**: `https://github.com/demin-coder/selvage`
- **Logo Image**: 400x400 PNG 아이콘
- **설명**: 서버가 Cline 사용자에게 어떤 도움이 되는지 설명
- **테스트 확인**: Cline에 README.md 또는 `llms-install.md`만 제공하고 성공적으로 설정되는지 테스트했다는 확인

#### 심사 기준

- Community Adoption (GitHub 지표)
- Developer Credibility (메인테이너 신뢰도)
- Project Maturity (코드 품질, 문서 완성도)
- Security Considerations

심사 기간: 제출 후 약 2일 내 리뷰

---

### 4. Claude Plugins Official

Anthropic이 관리하는 공식 Claude Code 플러그인 디렉토리.

#### 플러그인 구조

```
selvage-plugin/
  .claude-plugin/
    plugin.json          # 필수 - 플러그인 메타데이터
  .mcp.json              # MCP 서버 설정 (선택)
  commands/              # 슬래시 커맨드 (선택)
  agents/                # 에이전트 정의 (선택)
  skills/                # 스킬 정의 (선택)
  README.md              # 플러그인 문서
```

#### 제출 방법

- 공식 제출 폼: https://clau.de/plugin-directory-submission
- 품질 및 보안 기준 충족 필요
- "Anthropic Verified" 배지는 추가 리뷰 통과 시 부여

---

### 5. awesome-mcp-servers 리포지토리

#### (a) punkpeye/awesome-mcp-servers

- PR 제출: https://github.com/punkpeye/awesome-mcp-servers

#### (b) appcypher/awesome-mcp-servers

- PR 제출: https://github.com/appcypher/awesome-mcp-servers

#### (c) wong2/awesome-mcp-servers (mcpservers.org)

- 웹사이트 제출: https://mcpservers.org/submit

---

### 6. 기타 디렉토리

| 사이트 | 등록 방법 |
|--------|-----------|
| mcp.so | 네비게이션 바 'Submit' 버튼 또는 GitHub Issues |
| Glama.ai | 공개 리포지토리는 자동 크롤링, 또는 Discord/웹사이트로 문의 |
| PulseMCP | https://www.pulsemcp.com/use-cases/submit |
| mcpmarket.com | https://mcpmarket.com/submit |

---

## 실행 계획

### Phase 1: 사전 준비 (1-2일)

1. `server.json` 파일 생성
2. `smithery.yaml` 파일 생성
3. README에 `mcp-name` 추가
4. PyPI 키워드 업데이트 및 새 버전 배포
5. 400x400 PNG 로고 제작

### Phase 2: 주요 채널 등록 (3-5일)

1. 공식 MCP Registry 퍼블리시
2. Smithery 배포
3. Cline MCP Marketplace Issue 제출
4. Claude Plugins Official 제출

### Phase 3: 커뮤니티 채널 등록 (1-2일)

1. awesome-mcp-servers PR 제출 (punkpeye, appcypher)
2. mcpservers.org 제출
3. mcp.so / Glama.ai / PulseMCP / mcpmarket.com 등록
