# DiPeO 가이드

## 이게 뭐하는 건가요?

  블록 다이어그램을 통해 코딩을 대신하는 툴입니다. 흔하디 흔하게 볼 수 있을법한 프로젝트이지만, 본 프로젝트에서는 LLM API를 활용하기 쉽게끔 프로젝트를 설계했습니다.
  
  참고로 모든 동작은 설치하신 컴퓨터 내에서만 이루어집니다. 서버라는 개념은 '로컬 서버', 즉 설치하신 컴퓨터 내에서 가상의 서버를 돌리는 것으로, 내부에서만 동작할 뿐 그 어떠한 데이터도 외부로 전송하지 않습니다.


## 어떻게 시작하면 되나요?

우선 api key가 있어야 합니다. openai에서 계정을 만들고 돈을 충전한 다음, api key를 만들어주세요. custom LLM API는 추후 지원 예정입니다. (추가하고 싶다면 `apps/server/src/dipeo_server/domains/llm` 및 `dipeo/models/src/diagram.ts` 를 참고하여 추가해주세요.)

좌측 사이드바의 api keys 버튼을 누르시면 api key를 입력하는 창이 뜹니다. 여기에서 api key를 등록하면 자동으로 `files/apikeys.json` 이라는 파일이 만들어지며, 해당 파일로 api key를 관리할 수 있습니다.

그 다음 사용할 LLM API를 관리할 차례인데, 여기서는 LLM을 'person'이라고 부릅니다. add person 버튼을 누르고 person이 사용할 API key를 골라주세요. 그러면 자동으로 사용 가능한 모델 리스트가 나옵니다. 이 중 하나를 선택하면, 이 person이 LLM API로써 동작합니다. 우측의 system prompt는 선택입니다.

이후 왼쪽에서 start, person job, endpoint 블록을 드래그하여 적당히 캔버스에 올려놓고, default가 적힌 블록 위 버튼 (핸들) 을 드래그하여 블록들을 이어주세요. 그리고 person job에서는 person을 골라서 어떤 LLM API를 사용할지 선택한 다음, 원하는 명령어를 Default Prompt에 입력해주세요.

다이어그램이 만들어졌다면 상단 좌측의 Execution mode로 들어간 다음 Run diagram을 눌러주세요. 다이어그램을 저장하고 싶다면 Quicksave 버튼을 눌러주세요.


## 왜 person job, person 처럼 이상한 개념을 만드신건가요?

LLM을 활용할 때 제일 중요한 것은 컨텍스트를 관리하는 것입니다. 그런데 이 개념은 실제 코딩이나 실제 업무 환경과는 조금 다르게 흘러가는데, 예를 들어서
```
c = f(a + b)
print(f(a))
```
라고 하면, a+b를 이미 실행했음에도 불구하고 f라는 함수에는 이 기억이 없어 f(a)를 실행할 수 없습니다. 반면 LLM은
```
a+b는?
-> c 입니다.
a는 뭐였어?
```
와 같은 대답에 답할 수 있습니다. a를 이미 앞에서 관측했기 때문입니다.

업무 환경에서는,
```
a씨, b씨와 서류 작업을 해줘.
c씨, 봤지?
```
와 같은 일이 자주 일어남에도,
```
a와 b 대화
c에서 a와 b 대화를 로드 -> ?
```
처럼, 다른 LLM에서 실행한 일은 전혀 모르는 상황이 일어납니다.

코딩은 현실에서 발생하는 반복적인 어려움을 풀기 위한 도구입니다만, 이런 결정적인 차이가 존재하기 때문에 파일 개념, RAG 개념 등 다양한 개념을 도입하고 있습니다. 하지만 여전히 코딩을 하든 LLM을 쓰든 이런 간극을 수동으로 메꿔줘야 합니다. 그래서 코딩이나 LLM이나 장벽이 존재합니다.

## 그래서요?

그래서 현실 업무와 최대한 유사한 'person' 개념을 도입했습니다. person은 LLM API 그 자체로, 다이어그램 플로우대로 실행하는 작업들과 별개로 자체적인 컨텍스트와 기억을 가지고 있습니다. 때문에, person job을 통해 person이 수행하는 작업 블록을 놓고 각각 person a와 b를 할당한 다음, 다음 작업에서 person c를 할당하더라도 기존의 대화를 전부 기억합니다.
다만 기억하기 원하지 않는 경우, person job 블록에서 'forget' 속성을 눌러 'forget upon request'를 사용하면 앞서서 한 대화를 잊고 오로지 자신에게 온 요청만 읽어들입니다.

## Install guide

### node, pnpm 설치

[여기](https://nodejs.org/ko/download)서 윈도우, 맥, 리눅스 각자 맞는 환경에서, 아무 방식이나 고른 다음 pnpm을 설치하시면 됩니다.

### 파이썬 설치

[여기](https://www.python.org/downloads/release/python-3130/)서 맨 아래로 내려간 다음, 윈도우의 경우 windows installer 64-bit, 맥 유저의 경우 다른거 등 version 쪽의 링크를 클릭하여 설치하시면 됩니다.

### git 설치

[여기](https://git-scm.com/book/ko/v2/%EC%8B%9C%EC%9E%91%ED%95%98%EA%B8%B0-Git-%EC%84%A4%EC%B9%98)서 git을 설치해주세요.

### 프로젝트 복사

적당한 위치에서 powershell을 연 다음, `git clone https://github.com/sorryhyun/DiPeO.git` 을 입력하면 프로젝트가 받아집니다.

### 환경 설치

프로젝트를 받은 다음 DiPeO 폴더로 들어가서, 다음 명령어들을 실행합니다:

```bash
make install    # 모든 필요 요소 설치
make codegen    # 코드 생성
```

### 실행

다음 중 하나를 선택하여 실행합니다:

### 방법 1: 모든 서버 동시 실행 (권장)
```bash
make dev-all
```

### 방법 2: 개별 서버 실행
터미널을 두 개 열어서:
- 첫 번째 터미널에서 `make dev-server` 실행 (백엔드 서버)
- 두 번째 터미널에서 `make dev-web` 실행 (프론트엔드 서버)

브라우저 주소에 http://localhost:3000/ 을 입력하고 누르면 다이어그램을 만드는 창이 나오게 됩니다.


