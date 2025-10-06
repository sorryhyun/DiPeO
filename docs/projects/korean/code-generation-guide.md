# 코드 생성 가이드

## 개요

DiPeO는 다이어그램 기반의 다단계 코드 생성 파이프라인을 통해 자체 실행 엔진을 도그푸딩(dogfooding)합니다. 모든 생성 작업을 DiPeO 다이어그램으로 오케스트레이션하여 TypeScript 노드 명세부터 GraphQL 쿼리, Python 핸들러까지 일관된 타입 안전성을 유지합니다.

**핵심 철학**: DiPeO는 DiPeO로 DiPeO를 빌드합니다. 전 과정이 다이어그램으로 실행되기 때문에 플랫폼의 성숙도와 역량을 직접 증명합니다.

## 생성 흐름

```
1. 노드 명세 (TypeScript in /dipeo/models/src/)
   ↓
2. generate_all 다이어그램 실행 (dipeo run codegen/diagrams/generate_all)
   ├─→ TypeScript 파싱 → AST 캐시(글롭으로 자동 탐색)
   ├─→ 도메인 모델 생성 → /dipeo/diagram_generated_staged/
   └─→ 프론트엔드 코드 생성 → /apps/web/src/__generated__/
   ↓
3. /dipeo/diagram_generated_staged/에서 스테이징 코드 검증
   ↓
4. 스테이징 변경 적용 (make apply-syntax-only)
   ↓
5. GraphQL 스키마 내보내기 → /apps/server/schema.graphql
   ↓
6. TypeScript 타입 생성 (pnpm codegen)
```

**주요 특징**:

* **통합 생성**: 단일 `generate_all` 다이어그램이 모델과 프론트엔드를 병렬로 처리
* **스테이징 디렉터리**: `/dipeo/diagram_generated_staged/`에서 변경 사항을 적용 전 미리보기
* **동적 탐색**: 글롭 패턴으로 모든 TypeScript 파일 자동 검색
* **외부 코드화**: 생성 로직은 `projects/codegen/code/`에 위치하여 재사용 가능
* **문법 검증**: 기본 검증으로 생성 코드의 문법적 정확성 보장
* **단일 출처**: TypeScript 정의가 모든 다운스트림 코드를 생성

### 1단계: TypeScript 파싱 & 캐싱

**소스**: `/dipeo/models/src/`의 모든 TypeScript 파일
**캐시**: `/temp/codegen/` 및 `/temp/core/` (AST JSON 파일)
**다이어그램**: `codegen/diagrams/shared/parse_typescript_batch.light.yaml`

시스템은 모든 TypeScript 파일을 자동으로 탐색해 파싱하고, 이후 단계를 위해 AST를 캐시합니다.

### 2단계: 통합 코드 생성

**소스**: 캐시된 AST 파일 + TypeScript 명세
**다이어그램**: `codegen/diagrams/generate_all.light.yaml`
**출력**:

* 도메인 모델 → `/dipeo/diagram_generated_staged/`
* 프론트엔드 코드 → `/apps/web/src/__generated__/`

`generate_all` 다이어그램은 모델 생성과 프론트엔드 생성을 병렬로 실행합니다.

**도메인 모델**(스테이징으로 출력):

* Pydantic 모델 (`/models/`)
* Enums (`/enums/`)
* 검증 모델 (`/validation/`)
* GraphQL 스키마 템플릿
* Strawberry 타입과 mutation
* 정적 노드 클래스
* 타입 변환기

**프론트엔드 컴포넌트**(직접 출력):

* 필드 설정 (`/fields/`)
* 노드 모델과 설정 (`/models/`, `/nodes/`)
* GraphQL 쿼리 (`/queries/*.graphql`)
* Zod 검증 스키마
* 프론트엔드 레지스트리

### 3단계: 스테이징 변경 적용

**작업**: `/dipeo/diagram_generated_staged/` → `/dipeo/diagram_generated/`로 수동 복사
**검증**: 기본값은 문법 검증(파이썬 컴파일 체크)

`make apply-syntax-only` 또는 `make apply`를 사용해 스테이징된 백엔드 코드를 활성 디렉터리로 이동합니다. 이를 통해:

* 활성화 전 검증 수행
* 적용 전 변경 사항 리뷰 가능
* 생성 문제 발생 시 롤백 안전성 확보

### 4단계: GraphQL 스키마 내보내기

**명령**: `make graphql-schema`
**출력**: `/apps/server/schema.graphql`

애플리케이션 계층에서 전체 GraphQL 스키마를 내보내며, 생성된 Strawberry 타입의 모든 타입과 오퍼레이션을 반영합니다.

### 5단계: GraphQL TypeScript 생성

**소스**: `/apps/web/src/__generated__/queries/*.graphql` + `/apps/server/schema.graphql`
**출력**: `/apps/web/src/__generated__/graphql.tsx`
**명령**: `pnpm codegen`으로 자동 실행

다음을 완전 타입으로 생성:

* 모든 GraphQL 오퍼레이션의 TypeScript 타입
* React 훅(useQuery, useMutation, useSubscription)
* Apollo Client 연동 코드

## 명령어

### 권장 워크플로우

```bash
# 1단계: 전체 코드 생성(모델 + 프론트엔드)
dipeo run codegen/diagrams/generate_all --light --debug --timeout=90

# 2단계: 스테이징 변경 검토
make diff-staged           # 스테이징 vs 활성 파일 비교

# 3단계: 스테이징 백엔드 코드 적용
make apply-test     # 문법 검증만 수행하여 적용
# 또는
make apply                 # mypy 타입 체크를 포함한 전체 검증 적용

# 4단계: GraphQL 스키마와 타입 업데이트
make graphql-schema        # 스키마 내보내기 및 TypeScript 타입 생성
```

### 빠른 명령

```bash
make codegen-auto         # 위험: generate_all + 자동 적용 + GraphQL 스키마까지 실행
```

### 스테이징 관련 명령

```bash
make diff-staged            # 스테이징과 활성 생성 파일 비교
make validate-staged        # mypy 타입 체크 포함 전체 검증
make validate-staged-syntax # 문법 검증만(더 빠름)
make apply                  # 전체 검증과 함께 적용
make apply-syntax-only      # 문법 검증만으로 적용
make backup-generated       # 적용 전 백업
```

### 직접 다이어그램 실행(고급)

```bash
# 전체 생성(모델 + 프론트엔드)
dipeo run codegen/diagrams/generate_all --light --debug

# 특정 노드만 생성(디버깅용)
dipeo run codegen/diagrams/models/generate_backend_models_single --light \
  --input-data '{"node_name": "person_job"}'

# IR만 재생성(디버깅용)
dipeo run codegen/diagrams/generate_backend_simplified --light --debug
```

## 도그푸딩 아키텍처

DiPeO의 코드 생성은 전형적인 도그푸딩 사례입니다. 곧, DiPeO 다이어그램을 이용해 DiPeO의 코드를 만들어 갑니다.

1. **비주얼 프로그래밍**: 각 생성 단계가 다이어그램 노드로 표현됩니다.
2. **IR 기반 설계**: 일관성을 위해 중앙 집중형 중간 표현(Intermediate Representation)을 사용합니다.
3. **조합성**: 서브 다이어그램이 특정 생성 작업을 담당합니다.
4. **병렬화**: 여러 파일을 배치 처리합니다.
5. **에러 처리**: 배치 작업에서도 우아하게 실패를 처리합니다.
6. **캐싱**: AST 파싱과 IR 파일을 캐시해 디버깅과 재사용을 돕습니다.

이 접근은 세련된 IR 기반 메타 프로그래밍으로 플랫폼이 스스로를 구축할 만큼 성숙하다는 사실을 입증합니다.

## 스테이징 접근의 의의

스테이징 디렉터리(`diagram_generated_staged`)는 다음과 같은 핵심 목적을 갖습니다.

1. **변경 미리보기**: 적용 전 생성 코드를 리뷰
2. **원자적 업데이트**: 전부 적용 또는 전부 취소
3. **문법 검증**: 시스템을 깨뜨리기 전에 오류 포착
4. **롤백 안전성**: 잘못된 생성은 손쉽게 폐기
5. **프론트엔드 의존성**: 프론트엔드는 적용된(스테이징이 아닌) 모델을 참조

## 신규 기능 추가

### 새 노드 타입 추가

1. **노드 명세 생성**:

   ```typescript
   // /dipeo/models/src/node-specs/my-node.spec.ts
   export const myNodeSpec: NodeSpecification = {
     nodeType: NodeType.MyNode,
     category: 'processing',
     displayName: 'My Node',
     icon: 'Code',
     fields: [
       {
         name: 'myField',
         type: 'string',
         required: true,
         description: '필드 설명',
         uiType: 'text',  // 프론트엔드 UI 힌트
         placeholder: '값을 입력하세요...'
       }
     ]
   };
   ```

2. **Python 핸들러 생성**:

   ```python
   # /dipeo/application/execution/handlers/my_node.py
   from dipeo.diagram_generated.models.my_node import MyNodeData
   from dipeo.application.execution.handlers.base import TypedNodeHandler
   from dipeo.domain.base.mixins import LoggingMixin, ValidationMixin

   @register_handler
   class MyNodeHandler(TypedNodeHandler[MyNodeData], LoggingMixin, ValidationMixin):
       def prepare_inputs(self, inputs: dict, request: ExecutionRequest) -> dict:
           # 원시 입력 변환

       async def run(self, inputs: dict, request: ExecutionRequest) -> Any:
           # 로깅/검증 믹스인을 사용한 구현

       def serialize_output(self, result: Any, request: ExecutionRequest) -> Envelope:
           # Envelope로 변환
   ```

3. **코드 생성 실행**:

   ```bash
   # 새로운 노드를 포함해 전체 코드 생성
   dipeo run codegen/diagrams/generate_all --light --debug

   # 스테이징 변경 적용
   make apply-syntax-only

   # GraphQL 스키마 업데이트
   make graphql-schema
   ```

4. **이제 노드 사용 가능**:

   * Python과 TypeScript 전반에서 타입 안전성 확보
   * 자동 생성된 UI 컴포넌트
   * GraphQL 타입과 오퍼레이션
   * 검증 스키마

### 새로운 GraphQL 쿼리/뮤테이션 추가

1. **기존 엔티티용**: 쿼리 생성기를 수정

   ```python
   # /projects/codegen/code/frontend/generators/query_generator_dipeo.py
   # generate_diagram_queries() 등에서

   queries.append("""query MyNewQuery($id: ID!) {
     diagram(id: $id) {
       # 필드 추가
     }
   }""")
   ```

2. **새 엔티티용**: 새로운 쿼리 생성기 추가

   ```python
   # /projects/codegen/code/frontend/queries/my_entity_queries.py
   class MyEntityQueryGenerator:
       def generate(self) -> List[str]:
           return [
               """query GetMyEntity($id: ID!) {
                 myEntity(id: $id) {
                   id
                   name
                 }
               }"""
           ]
   ```

3. **메인 생성기에 등록**:

   ```python
   # DiPeOQueryGenerator.generate_all_queries() 내
   my_entity_generator = MyEntityQueryGenerator()
   self.write_query_file('myEntity', my_entity_generator.generate())
   ```

4. **생성 실행**:

   ```bash
   make codegen                 # 스키마 내보내기 포함 전체 파이프라인
   cd apps/web && pnpm codegen  # 업데이트된 스키마로 TypeScript 생성
   ```

## IR 기반 생성 시스템

현재 코드 생성 시스템은 IR 기반 패턴을 사용하며 다음과 같은 특징을 갖습니다.

1. **중간 표현(Intermediate Representation)**: JSON 파일을 단일 진실의 원천으로 사용합니다.
2. **IR 빌더**: 추출 로직을 전용 모듈에 모아 관리합니다.
3. **템플릿 잡 노드**: IR 데이터를 바로 렌더링합니다.
4. **동적 탐색**: 글롭 패턴으로 모든 파일을 자동 검색합니다.
5. **외부 코드화**: `projects/codegen/code/` 아래에서 IR 빌더를 재사용합니다.
6. **배치 처리**: 여러 노드를 병렬로 생성합니다.
7. **향상된 에러 처리**: 배치 작업에서 우아한 강건성을 제공합니다.

예시 패턴:

```yaml
- label: Generate Field Configs
  type: template_job
  props:
    template_path: projects/codegen/templates/frontend/field_config.jinja2
    output_path: "{{ output_dir }}/fields/{{ node_type_pascal }}Fields.ts"
    context:
      node_type: "{{ node_type }}"
      fields: "{{ fields }}"
      # ... 기타 컨텍스트
```

## 커스텀 템플릿 시스템

DiPeO는 커스텀 필터가 포함된 Jinja2 템플릿을 사용합니다.

**타입 변환 필터**:

* `ts_to_python` - TypeScript 타입을 Python으로 변환
* `ts_to_graphql` - TypeScript 타입을 GraphQL로 변환
* `get_zod_type` - Zod 검증 타입 반환
* `get_graphql_type` - GraphQL 타입 반환

**네이밍 컨벤션 필터**:

* `snake_case`, `camel_case`, `pascal_case` - 케이스 변환
* `pluralize` - 컬렉션 명칭 복수화

**핵심 제너레이터**:

- `/projects/codegen/code/models/` - Python 모델 생성
- `/projects/codegen/code/frontend/` - React/TypeScript 생성
- 모든 로직을 외부 파일로 분리해 테스트 가능성과 재사용성을 높입니다.

## 주요 파일 및 디렉터리

### 소스 파일

- `/dipeo/models/src/` – TypeScript 명세(단일 진실의 원천)
  - `/node-specs/` – 노드 타입 정의
  - `/core/` – 핵심 도메인 타입
  - `/codegen/` – 코드 생성 매핑

### 코드 생성 시스템

- `/projects/codegen/diagrams/` – DiPeO 다이어그램으로 생성 작업을 오케스트레이션
  - `generate_all.light.yaml` – 전체 파이프라인
  - `generate_backend_simplified.light.yaml` – IR에서 백엔드 생성
  - `generate_frontend_simplified.light.yaml` – IR에서 프론트엔드 생성
  - `generate_strawberry.light.yaml` – IR에서 GraphQL 생성
- `/projects/codegen/code/` – IR 빌더와 추출기
  - `backend_ir_builder.py` – 백엔드 모델/타입 수집
  - `frontend_ir_builder.py` – 프런트엔드 컴포넌트/스키마 추출
  - `strawberry_ir_builder.py` – GraphQL 오퍼레이션과 도메인 타입
- `/projects/codegen/ir/` – 중간 표현(JSON)
  - `backend_ir.json` – 노드 스펙, 모델, enum
  - `frontend_ir.json` – 컴포넌트, 스키마, 필드
  - `strawberry_ir.json` – GraphQL 오퍼레이션, 타입, 입력값
- `/projects/codegen/templates/` – IR을 소비하는 Jinja2 템플릿
  - `/backend/` – Python 모델 템플릿
  - `/frontend/` – TypeScript/React 템플릿
  - `/strawberry/` – GraphQL/Strawberry 템플릿

### 생성 파일(수정 금지)

- `/dipeo/diagram_generated_staged/` – 적용 전 스테이징 코드
- `/dipeo/diagram_generated/` – 활성 Python 생성 코드
- `/apps/web/src/__generated__/` – 생성된 프런트엔드 코드
- `/temp/` – AST 캐시(버전 관리 대상 아님)

### 설정

- `/apps/web/codegen.yml` – GraphQL 코드 생성기 설정
- `Makefile` – 전체 파이프라인을 오케스트레이션

## 아키텍처 노트

### v1.0 리팩터링 완료

주요 아키텍처 개선이 완료되었습니다.
- **믹스인 기반 서비스**: 단일 상속 대신 선택적 믹스인을 사용합니다.
- **통합 EventBus**: 이벤트 프로토콜을 단일 인터페이스로 통합했습니다.
- **직접 프로토콜 구현**: 불필요한 어댑터 레이어를 제거했습니다.
- **강화된 타입 안전성**: 결과 타입과 JSON 정의를 개선했습니다.
- **스네이크 케이스**: Python은 스네이크 케이스를 사용하고, 호환성을 위해 Pydantic alias를 제공합니다.
- **생성된 enum**: 모든 enum을 TypeScript 명세에서 자동 생성합니다.

### 왜 마스터 다이어그램 대신 Make 명령을 쓰는가

코드베이스는 단일 마스터 다이어그램 대신 Make 명령을 사용합니다. 그 이유는:

- **우수한 에러 처리**: Make는 첫 오류에서 중단합니다.
- **명확한 실행 흐름**: 각 단계가 명시적입니다.
- **디버깅 용이**: 개별 단계만 실행하거나 IR을 점검할 수 있습니다.
- **표준 도구 사용**: 개발자에게 친숙한 Make를 활용합니다.
- **IR 점검**: 생성 중간 결과(JSON)를 살펴볼 수 있습니다.

### 2단계 GraphQL 생성

시스템은 GraphQL을 두 단계로 생성합니다.

1. **DiPeO가 도메인 지식으로 쿼리 생성**
2. **GraphQL 코드젠이 쿼리 + 스키마로 TypeScript 생성**

이를 통해:

* **도메인 주도 쿼리**: 오퍼레이션이 도메인 모델과 정합
* **엔드 투 엔드 타입 안전성**: Python에서 TypeScript까지
* **유연성**: 스키마 변경 없이 쿼리 커스터마이즈
* **일관성**: 모든 쿼리가 동일한 패턴을 따름

### IR 기반 코드 구성

모든 생성 로직은 IR 빌더를 거쳐 템플릿으로 전달됩니다.
- **IR 빌더**: `*_ir_builder.py` 파일이 추출 로직을 중앙에서 관리합니다.
- **템플릿**: IR 데이터를 소비해 일관된 출력을 생성합니다.
- **패턴**: `AST 파싱 → IR 빌드 → 템플릿 렌더링 → 출력` 흐름을 따릅니다.
- **단위 테스트 지원**: 추출/생성 로직을 개별적으로 검증할 수 있습니다.
- **코드 재사용**: 다이어그램 간 로직 재사용이 용이합니다.
- **IR 검토**: `projects/codegen/ir/`의 JSON을 확인해 디버깅할 수 있습니다.

## 모범 사례

1. **생성 파일은 절대 수정하지 말 것** - 다음 생성에서 덮어씌워짐
2. **명세 변경 후 `make codegen` 실행** - 전체 파이프라인 자동 처리
3. **`make diff-staged`로 변경 미리보기** - 적용 전 리뷰
4. **`make apply`는 필요할 때만 수동 실행** - 전체 코드젠에 포함되어 있음
5. **타이프드 오퍼레이션 활용** - 프론트엔드에서 생성된 훅 적극 사용
6. **네이밍 컨벤션 준수**:

   * 쿼리: `Get{Entity}`, `List{Entities}`
   * 뮤테이션: `Create{Entity}`, `Update{Entity}`, `Delete{Entity}`
   * 서브스크립션: `{Entity}Updates`

## 문제 해결

**노드 추가 후 타입 누락**:

```bash
make codegen           # IR 재생성과 전체 코드 생성
make apply-syntax-only # 스테이징 적용
make graphql-schema    # 스키마 업데이트
make dev-all           # 서버 재시작
```

**IR 디버깅**:

```bash
# 생성 중인 내용을 이해하기 위해 IR 파일을 살펴봅니다.
cat projects/codegen/ir/backend_ir.json | jq '.node_specs[0]'
cat projects/codegen/ir/frontend_ir.json | jq '.components[0]'
cat projects/codegen/ir/strawberry_ir.json | jq '.operations[0]'
```

**GraphQL 쿼리 미발견**:

1. `/apps/web/src/__generated__/queries/`에 쿼리 파일이 생성되었는지 확인합니다.
2. `/apps/web/`에서 `pnpm codegen`을 실행했는지 확인합니다.
3. 컴포넌트에서 사용하는 쿼리 이름이 일치하는지 검증합니다.

**타입 불일치 오류**:

- 스키마와 쿼리가 동기화되지 않았거나 IR이 오래됐을 수 있습니다.
- 전체 워크플로우를 다시 실행합니다.

  ```bash
  make codegen          # IR 재생성과 전체 코드 생성
  make apply-syntax-only
  make graphql-schema
  ```

## 결론

DiPeO의 IR 기반 코드 생성 시스템은 도그푸딩 접근으로 플랫폼의 성숙도를 증명합니다. DiPeO 다이어그램이 중간 표현을 거쳐 DiPeO의 코드를 생성함으로써, 복잡한 메타 프로그래밍 과제를 시각적 프로그래밍으로 해결하면서도 TypeScript 명세에서 IR, Python 모델, GraphQL 오퍼레이션까지 일관된 타입 안전성을 유지합니다. 스테이징 디렉터리와 병렬 배치 처리, 중앙 집중형 IR 설계가 중복을 제거하고 추출 로직을 하나의 진실 원천으로 묶어주어, 강력하면서도 유지보수 가능한 생성 파이프라인을 제공합니다.
