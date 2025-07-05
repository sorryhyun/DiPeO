# Quickstart 가이드

## node, pnpm 설치

[여기](https://nodejs.org/ko/download)서 윈도우, 맥, 리눅스 각자 맞는 환경에서, 아무 방식이나 고른 다음 pnpm을 설치하시면 됩니다.

## 파이썬 설치

[여기](https://www.python.org/downloads/release/python-3130/)서 맨 아래로 내려간 다음, 윈도우의 경우 windows installer 64-bit, 맥 유저의 경우 다른거 등 version 쪽의 링크를 클릭하여 설치하시면 됩니다.

## git 설치

[여기](https://git-scm.com/book/ko/v2/%EC%8B%9C%EC%9E%91%ED%95%98%EA%B8%B0-Git-%EC%84%A4%EC%B9%98)서 git을 설치해주세요.

## 프로젝트 복사

적당한 위치에서 powershell을 연 다음, `git clone https://github.com/sorryhyun/DiPeO.git` 을 입력하면 프로젝트가 받아집니다.

## 환경 설치

프로젝트를 받은 다음 DiPeO 폴더로 들어가서, powershell에서 `make install-all` 을 입력하면 모든 필요 요소가 설치됩니다.

## 실행

5. 환경 설치

프로젝트를 받은 다음 DiPeO 폴더로 들어가서, powershell에서 make install-all 을 입력하면 모든 필요 요소가 설치됩니다.

6. 실행

터미널을 두 개 열어서:
- 첫 번째 터미널에서 `make dev-server` 실행 (백엔드 서버)
- 두 번째 터미널에서 `make dev-web` 실행 (프론트엔드 서버)

브라우저 주소에 http://localhost:3000/ 을 입력하고 누르면 다이어그램을 만드는 창이 나오게 됩니다.
=======
`bash ./dev.sh --all` 을 누르면 서버 및 브라우저가 가동됩니다. 브라우저 주소에 `http://localhost:3000/` 을 입력하고 누르면 다이어그램을 만드는 창이 나오게 됩니다.


