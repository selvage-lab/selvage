#!/bin/bash

#############################################################################
# Selvage 데모 영상 제작 자동화 스크립트
#############################################################################
#
# 🎬 사용 방법:
#   ./scripts/create_demo.sh
#
# 🔧 필요한 도구:
#   - asciinema   : 터미널 세션 녹화 (brew install asciinema)
#   - expect      : 대화형 프로세스 자동화 (brew install expect)  
#   - agg         : GIF 변환 (cargo install --git https://github.com/asciinema/agg)
#   - selvage     : 프로젝트가 개발 모드로 설치되어 있어야 함 (pip install -e .)
#
# 📋 스크립트가 수행하는 작업:
#   1. 데모용 워크스페이스 생성 (demo_workspace)
#   2. Git 저장소 초기화
#   3. 샘플 Python 파일들 생성 (hello.py, calculator.py)
#   4. 파일들을 Git staging area에 추가
#   5. asciinema로 터미널 세션 자동 녹화:
#      - PS1 프롬프트를 "selvage $ "로 변경
#      - selvage review --staged 명령 실행
#      - 리뷰 완료 후 자동 종료
#   6. agg로 GIF 변환 (demo.gif 생성)
#
# 📁 생성되는 파일:
#   - demo_workspace/demo.cast : asciinema 녹화 파일 (작업용)
#   - demo_workspace/demo.gif  : GIF 데모 영상 (작업용)
#   - assets/demo.cast : assets 디렉토리에 복사된 최종 녹화 파일
#   - assets/demo.gif  : assets 디렉토리에 복사된 최종 데모 영상
#
# ⚠️  주의사항:
#   - 기존 demo_workspace 디렉터리는 자동으로 삭제됩니다
#   - agg가 설치되어 있지 않으면 GIF 변환은 건너뜁니다
#   - selvage 명령이 2분(120초) 내에 완료되지 않으면 타임아웃됩니다
#
#############################################################################

# 간단한 데모 녹화 스크립트
set -e

echo "🎬 Selvage 데모 영상 제작을 시작합니다..."

# 현재 디렉터리 확인
DEMO_DIR="demo_workspace"
if [ -d "$DEMO_DIR" ]; then
    echo "🧹 기존 데모 워크스페이스를 정리합니다..."
    rm -rf "$DEMO_DIR"
fi

# 데모용 워크스페이스 생성
echo "📁 데모 워크스페이스를 생성합니다..."
mkdir "$DEMO_DIR"
cd "$DEMO_DIR"

# Git 초기화
echo "🔧 Git 저장소를 초기화합니다..."
git init --quiet
git config user.email "demo@example.com"
git config user.name "Demo User"

# 샘플 파일 생성
echo "📝 샘플 파일들을 생성합니다..."
cat > hello.py << 'EOF'
def greet(name):
    return f"Hello, {name}!"

def main():
    names = ["World", "Selvage", "Developer"]
    for name in names:
        print(greet(name))

if __name__ == "__main__":
    main()
EOF

cat > calculator.py << 'EOF'
class Calculator:
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

calc = Calculator()
print(calc.add(5, 3))
print(calc.multiply(4, 7))
EOF

# 파일들을 staging
echo "📦 파일들을 Git staging area에 추가합니다..."
git add .

echo "✅ 준비 완료!"

# 녹화 스크립트 생성 (더 간단한 버전)
cat > record.exp << 'EOF'
#!/usr/bin/expect -f

set timeout 120
spawn asciinema rec -c "/bin/bash --noprofile --norc -i" demo.cast

# 초기 프롬프트 대기
expect {
    timeout { puts "Timeout"; exit 1 }
    -re {.*[\$%#] $} { puts "Got prompt" }
}

# PS1 변경
send "export PS1=\"selvage \\$ \"\r"
sleep 1

# selvage 실행
send "selvage review --staged\r"

# 완료 대기 (안정적인 패턴)
expect {
    timeout { 
        puts "Command completed or timeout"
        send "exit\r"
        exit 0
    }
    -re "추천사항" {
        puts "Review completed - recommendations shown!"
        sleep 3
        send "exit\r"
        expect eof
        exit 0
    }
    -re {~[\r\n]+~} {
        puts "Review completed - pager end detected!"
        sleep 2
        send "q"
        sleep 1
        send "exit\r"
        expect eof
        exit 0
    }
    -re {.*[\$%#] $} {
        puts "Got prompt back"
        send "exit\r"
        expect eof
        exit 0
    }
}
EOF

chmod +x record.exp

echo "🎬 녹화를 시작합니다..."
./record.exp

if [ -f "demo.cast" ]; then
    echo "📹 녹화가 완료되었습니다!"
    
    # exit 관련 줄들을 자동으로 제거
    echo "🧹 녹화 파일에서 exit 관련 내용을 정리합니다..."
    # exit 명령어가 포함된 마지막 줄들을 제거 (일반적으로 마지막 1-3줄)
    if grep -q "exit" demo.cast; then
        # exit가 포함된 줄들을 역순으로 찾아서 제거
        while tail -1 demo.cast | grep -q "exit\|selvage.*exit"; do
            sed -i '' '$d' demo.cast
        done
        echo "✅ exit 관련 내용이 제거되었습니다."
    fi
    
    # 데모 파일들을 assets 디렉토리로 복사
    echo "📂 데모 파일들을 assets 디렉토리로 복사합니다..."
    mkdir -p ../assets
    cp demo.cast ../assets/demo.cast
    
    # agg 설치 확인 및 변환
    if command -v agg &> /dev/null; then
        echo "🎨 GIF로 변환 중..."
        agg --theme=dracula --font-family "D2Coding" --font-size 23 --speed 3 demo.cast demo.gif
        echo "✨ GIF 변환 완료: $(pwd)/demo.gif"
        
        # GIF도 assets 디렉토리로 복사
        cp demo.gif ../assets/demo.gif
        echo "📂 GIF 파일도 assets 디렉토리로 복사되었습니다."
    else
        echo "📝 수동으로 GIF 변환하세요:"
        echo "   agg --theme=dracula --font-family \"D2Coding\" --font-size 23 --speed 3 demo.cast demo.gif"
    fi
    
    echo "📊 파일 크기:"
    ls -lh demo.cast
    if [ -f "demo.gif" ]; then
        ls -lh demo.gif
    fi
    
    echo ""
    echo "📁 최종 파일 위치:"
    echo "   $(pwd)/../assets/demo.cast"
    if [ -f "../assets/demo.gif" ]; then
        echo "   $(pwd)/../assets/demo.gif"
    fi
else
    echo "❌ 녹화 파일이 생성되지 않았습니다."
fi

# 정리
rm -f record.exp

echo "🎉 데모 제작 완료!" 
