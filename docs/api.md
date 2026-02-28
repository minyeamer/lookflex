# LookFlex API 문서

> **Base URL** `http://localhost:8000/api/v1`
> **인증 방식** JWT Bearer Token (`Authorization: Bearer <access_token>`)
> **Content-Type** `application/json` (파일 업로드 제외)

---

## 공통 규격

### 응답 Envelope

모든 응답은 아래 구조를 따릅니다.

```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

오류 응답:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "인증이 필요합니다."
  }
}
```

### HTTP 상태 코드

| 코드 | 의미 |
|---|---|
| 200 | 성공 |
| 201 | 생성 성공 |
| 204 | 성공 (응답 본문 없음) |
| 400 | 잘못된 요청 |
| 401 | 인증 필요 |
| 403 | 권한 없음 |
| 404 | 리소스 없음 |
| 409 | 충돌 (중복 등) |
| 422 | 유효성 검사 실패 |
| 500 | 서버 오류 |

### Enum 정의

#### Role — 사용자 역할

| 값 | 설명 |
|---|---|
| `OWNER` | 시스템 소유자. 전체 관리 권한 (1명 고정) |
| `ADMIN` | 관리자. 사용자·데이터소스·대시보드 관리 |
| `EDITOR` | 편집자. 대시보드·차트 생성/수정 |
| `VIEWER` | 뷰어. 조회 및 개인 뷰 설정만 가능 |

#### ApprovalStatus — 회원가입 요청 상태

| 값 | 설명 |
|---|---|
| `PENDING` | 관리자 승인 대기 중 |
| `APPROVED` | 승인됨 — 사용자 계정 생성 |
| `REJECTED` | 거절됨 |

#### GroupType — 그룹 유형

| 값 | 설명 |
|---|---|
| `DEPARTMENT` | 부서 |
| `POSITION` | 직급 |
| `CUSTOM` | 사용자 정의 그룹 |

#### DSSourceType — 데이터 소스 유형

| 값 | 설명 |
|---|---|
| `POSTGRESQL` | PostgreSQL 데이터베이스 |
| `MYSQL` | MySQL 데이터베이스 |
| `MSSQL` | Microsoft SQL Server |
| `BIGQUERY` | Google BigQuery |
| `EXCEL` | Excel 파일 업로드 |
| `CSV` | CSV 파일 업로드 |

#### FieldType — 데이터 필드 타입

| 값 | 설명 |
|---|---|
| `TEXT` | 문자열 |
| `NUMBER` | 숫자 |
| `DATE` | 날짜 (YYYY-MM-DD) |
| `DATETIME` | 날짜+시간 (ISO 8601) |
| `BOOLEAN` | 참/거짓 |

#### AggregateType — 집계 함수

| 값 | 설명 |
|---|---|
| `SUM` | 합계 |
| `AVG` | 평균 |
| `MIN` | 최솟값 |
| `MAX` | 최댓값 |
| `COUNT` | 건수 |
| `COUNT_DISTINCT` | 고유 건수 |
| `NONE` | 집계 없음 (원본 값) |

#### ChartType — 차트 유형

| 값 | 설명 |
|---|---|
| `TABLE` | 테이블 (표) |
| `PIVOT` | 피벗 테이블 |
| `LINE` | 꺾은선 그래프 |
| `BAR` | 막대 그래프 |
| `STACKED_BAR` | 누적 막대 그래프 |
| `PIE` | 원형 차트 |
| `SCORECARD` | 스코어카드 (KPI 지표) |

#### FilterType — 필터 UI 유형

| 값 | 설명 |
|---|---|
| `DROPDOWN` | 드롭다운 선택 |
| `TEXT_INPUT` | 텍스트 입력 |
| `RANGE` | 범위 슬라이더 |
| `DATE_RANGE` | 날짜 범위 선택 |

#### FilterOp — 필터 연산자

| 값 | 설명 |
|---|---|
| `EQ` | 같음 (`=`) |
| `NEQ` | 같지 않음 (`!=`) |
| `CONTAINS` | 포함 |
| `NOT_CONTAINS` | 미포함 |
| `STARTS_WITH` | ~로 시작 |
| `ENDS_WITH` | ~로 끝남 |
| `REGEX` | 정규식 매칭 |
| `GT` | 초과 (`>`) |
| `GTE` | 이상 (`>=`) |
| `LT` | 미만 (`<`) |
| `LTE` | 이하 (`<=`) |
| `BETWEEN` | 범위 내 (이상 ~ 이하) |
| `IS_NULL` | 값 없음 |
| `IS_NOT_NULL` | 값 있음 |

#### SortDir — 정렬 방향

| 값 | 설명 |
|---|---|
| `ASC` | 오름차순 |
| `DESC` | 내림차순 |

#### CondFormatApplyTo — 조건부 서식 적용 대상

| 값 | 설명 |
|---|---|
| `CELL` | 셀 단위 적용 |
| `ROW` | 행 전체 적용 |

#### NotificationType — 알림 유형

| 값 | 설명 |
|---|---|
| `REGISTER_REQUEST` | 새 회원가입 요청 (ADMIN에게 발송) |
| `REGISTER_APPROVED` | 회원가입 승인 알림 |
| `REGISTER_REJECTED` | 회원가입 거절 알림 |

#### AuditAction — 감사 로그 액션

| 값 | 설명 |
|---|---|
| `LOGIN` | 로그인 |
| `LOGOUT` | 로그아웃 |
| `DATA_QUERY` | 데이터 조회 |
| `EXPORT` | 데이터 내보내기 |
| `DASHBOARD_EDIT` | 대시보드 수정 |
| `DATASOURCE_EDIT` | 데이터 소스 수정 |
| `USER_EDIT` | 사용자 정보 수정 |

### 에러 코드

모든 에러 응답의 `error.code` 필드에 사용되는 코드입니다.

| 코드 | HTTP | 설명 |
|---|---|---|
| `EMAIL_ALREADY_EXISTS` | 409 | 이미 가입된 이메일 |
| `EMAIL_NOT_VERIFIED` | 403 | 이메일 인증 미완료 |
| `REGISTER_REQUEST_PENDING` | 409 | 동일 이메일로 대기 중인 요청 존재 |
| `INVALID_CODE` | 400 | 인증 코드 불일치 |
| `CODE_EXPIRED` | 400 | 인증 코드 만료 |
| `INVALID_CREDENTIALS` | 401 | 이메일 또는 비밀번호 불일치 |
| `ACCOUNT_DISABLED` | 403 | 비활성화된 계정 |
| `INVALID_TOKEN` | 401 | 유효하지 않거나 만료된 토큰 |
| `USER_NOT_FOUND` | 404 | 사용자를 찾을 수 없음 |
| `NOT_FOUND` | 404 | 리소스를 찾을 수 없음 |
| `ALREADY_PROCESSED` | 409 | 이미 처리된 요청 |
| `UNAUTHORIZED` | 401 | 인증이 필요함 |
| `FORBIDDEN` | 403 | 권한 없음 |
| `VALIDATION_ERROR` | 422 | 요청 데이터 유효성 검사 실패 |

### 페이지네이션 공통 쿼리 파라미터

페이지네이션이 적용되는 목록 API는 모두 아래 파라미터를 지원합니다.

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `page` | integer | 1 | 페이지 번호 (1-based) |
| `limit` | integer | 20 | 페이지당 항목 수 (최대 100) |

페이지네이션 응답 구조:

```json
{
  "success": true,
  "data": {
    "items": [ ... ],
    "total": 120,
    "page": 1,
    "limit": 20,
    "total_pages": 6
  }
}
```

---

## 1. 인증 (Auth)

> **회원가입 플로우 (UI 기준)**
> 1. `POST /auth/send-verification` → 이메일 입력 후 OTP 요청
> 2. `POST /auth/verify-email` → OTP 입력 후 인증 확인 (제출 버튼 활성화)
> 3. `POST /auth/register` → 나머지 정보 입력 후 회원가입 제출

---

### 1.1. 이메일 인증 코드 발송

이메일 주소만으로 OTP를 발송합니다. DB 기록 수행 없음.

```
POST /auth/send-verification
```

**Request Body**

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `email` | string (email) | ✅ | 이메일 주소 |

```json
{
  "email": "user@example.com"
}
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "message": "인증 코드가 발송되었습니다."
  }
}
```

**Error Cases**

| 상태 | code | 설명 |
|---|---|---|
| 409 | EMAIL_ALREADY_EXISTS | 이미 가입된 이메일 |

---

### 1.2. 이메일 인증 코드 확인

OTP를 검증하고 Redis에 인증 완료 플래그를 저장합니다 (30분 유효).
DB 수정 없음 — 회원가입 제출 전까지의 UI 메시지 활성화 용도.

```
POST /auth/verify-email
```

**Request Body**

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `email` | string (email) | ✅ | 이메일 주소 |
| `code` | string (6자리) | ✅ | OTP 인증 코드 |

```json
{
  "email": "user@example.com",
  "code": "483921"
}
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "message": "이메일 인증이 완료되었습니다. 회원가입을 이어서 진행해주세요."
  }
}
```

**Error Cases**

| 상태 | code | 설명 |
|---|---|---|
| 400 | INVALID_CODE | 코드 불일치 |
| 400 | CODE_EXPIRED | 코드 만료 (유효시간 10분) |

---

### 1.3. 인증코드 재발송

```
POST /auth/resend-code
```

**Request Body**

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `email` | string (email) | ✅ | 이메일 주소 |

```json
{
  "email": "user@example.com"
}
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "message": "인증 코드가 재발송되었습니다."
  }
}
```

**Error Cases**

| 상태 | code | 설명 |
|---|---|---|
| 409 | EMAIL_ALREADY_EXISTS | 이미 가입된 이메일 |

---

### 1.4. 회원가입 요청

`/verify-email` 완료 후 나머지 정보를 제출합니다.
Redis에 인증 완료된 이메일이 없으면 403을 반환합니다.
승인된 이후 로그인 가능 상태로 사용자 계정이 생성됩니다.

```
POST /auth/register
```

**Request Body**

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `email` | string (email) | ✅ | 이메일 주소 |
| `password` | string | ✅ | 비밀번호 (8–100자) |
| `name` | string | ✅ | 이름 (1–100자) |
| `requested_role` | Role | - | 희망 역할 (`EDITOR` \| `VIEWER`, 기본값 `VIEWER`) |

```json
{
  "email": "user@example.com",
  "password": "P@ssw0rd!",
  "name": "홍길동",
  "requested_role": "EDITOR"
}
```

**Response `201`**

```json
{
  "success": true,
  "data": {
    "message": "회원가입 요청이 완료되었습니다. 관리자 승인을 기다려주세요.",
    "email": "user@example.com"
  }
}
```

**Error Cases**

| 상태 | code | 설명 |
|---|---|---|
| 403 | EMAIL_NOT_VERIFIED | 이메일 인증이 필요합니다 (Redis 인증 완료 키 없음) |
| 409 | EMAIL_ALREADY_EXISTS | 이미 가입된 이메일 |
| 409 | REGISTER_REQUEST_PENDING | 동일 이메일로 대기 중인 요청 존재 |

---

### 1.5. 로그인

```
POST /auth/login
```

**Request Body**

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `email` | string (email) | ✅ | 이메일 주소 |
| `password` | string | ✅ | 비밀번호 |

```json
{
  "email": "user@example.com",
  "password": "P@ssw0rd!"
}
```

**Response `200`**

Access Token은 응답 바디에, Refresh Token은 `HttpOnly` 쿠키로 설정됩니다.

```json
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 900
  }
}
```

Set-Cookie: `refresh_token=<token>; HttpOnly; SameSite=Strict; Path=/api/v1/auth/refresh; Max-Age=604800`

**Error Cases**

| 상태 | code | 설명 |
|---|---|---|
| 401 | INVALID_CREDENTIALS | 이메일 또는 비밀번호 불일치 |
| 403 | EMAIL_NOT_VERIFIED | 이메일 미인증 |
| 403 | ACCOUNT_DISABLED | 비활성화된 계정 |

---

### 1.6. 토큰 갱신

```
POST /auth/refresh
```

쿠키의 Refresh Token을 사용하며 Request Body 없음.

**Response `200`**

```json
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 900
  }
}
```

---

### 1.7. 로그아웃

```
POST /auth/logout
```

서버에서 Refresh Token 쿠키를 만료 처리합니다.

**Response `204`**

---

### 1.8. 회원가입 요청 목록 조회

> 권한: ADMIN 이상

```
GET /auth/register-requests?status=PENDING&page=1&limit=20
```

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `status` | ApprovalStatus | PENDING | 필터 상태 |

**Response `200`**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "email": "user@example.com",
        "name": "홍길동",
        "requested_role": "EDITOR",
        "status": "PENDING",
        "email_verified_at": "2026-02-28T09:00:00Z",
        "created_at": "2026-02-28T08:55:00Z"
      }
    ],
    "total": 3,
    "page": 1,
    "limit": 20,
    "total_pages": 1
  }
}
```

---

### 1.9. 회원가입 요청 처리 (승인/거절)

> 권한: ADMIN 이상

```
PATCH /auth/register-requests/:request_id
```

**Path Parameters**

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `request_id` | UUID | 요청 ID |

**Request Body**

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `status` | ApprovalStatus | ✅ | `APPROVED` \| `REJECTED` |
| `assigned_role` | Role | 승인 시 필수 | 부여할 역할 (`EDITOR` \| `VIEWER`) |
| `reject_reason` | string | - | 거절 사유 (선택) |

```json
{
  "status": "APPROVED",
  "assigned_role": "EDITOR",
  "reject_reason": null
}
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "user_id": "uuid",         // 승인 시에만 반환
    "status": "APPROVED"
  }
}
```

**Error Cases**

| 상태 | code | 설명 |
|---|---|---|
| 404 | NOT_FOUND | 요청을 찾을 수 없음 |
| 409 | ALREADY_PROCESSED | 이미 처리된 요청 |
```

---

### 1.10. 비밀번호 재설정 요청

```
POST /auth/password-reset-request
```

**Request Body**

```json
{
  "email": "user@example.com"
}
```

**Response `200`** — 이메일 존재 여부와 무관하게 동일 응답 반환 (보안)

```json
{
  "success": true,
  "data": {
    "message": "등록된 이메일인 경우 재설정 링크가 발송됩니다."
  }
}
```

---

### 1.11. 비밀번호 재설정

```
POST /auth/password-reset
```

**Request Body**

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `token` | string | ✅ | 이메일로 전송된 재설정 토큰 |
| `new_password` | string | ✅ | 새 비밀번호 (8–100자) |

```json
{
  "token": "reset-token-from-email",
  "new_password": "NewP@ssw0rd!"
}
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "message": "비밀번호가 변경되었습니다."
  }
}
```

**Error Cases**

| 상태 | code | 설명 |
|---|---|---|
| 400 | INVALID_TOKEN | 유효하지 않거나 만료된 토큰 |
| 404 | USER_NOT_FOUND | 사용자를 찾을 수 없음 |
```

---

## 2. 사용자 (Users)

### 2.1. 내 프로필 조회

```
GET /users/me
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "홍길동",
    "profile_image_url": "https://...",
    "role": "EDITOR",
    "groups": [
      { "id": "uuid", "name": "마케팅팀", "type": "DEPARTMENT" },
      { "id": "uuid", "name": "대리", "type": "POSITION" }
    ],
    "joined_at": "2026-02-28T09:00:00Z"
  }
}
```

---

### 2.2. 내 프로필 수정

```
PATCH /users/me
```

**Request Body** (모든 필드 선택적)

```json
{
  "name": "홍길동",
  "profile_image_url": "https://..."
}
```

**Response `200`** — 변경된 프로필 전체 반환 (2.1 응답과 동일 구조)

---

### 2.3. 프로필 이미지 업로드

```
POST /users/me/profile-image
Content-Type: multipart/form-data
```

**Form Data**

| 필드 | 타입 | 설명 |
|---|---|---|
| `file` | File | 이미지 파일 (jpg/png/webp, 최대 5MB) |

**Response `200`**

```json
{
  "success": true,
  "data": {
    "profile_image_url": "https://..."
  }
}
```

---

### 2.4. 내 비밀번호 변경

```
PATCH /users/me/password
```

**Request Body**

```json
{
  "current_password": "P@ssw0rd!",
  "new_password": "NewP@ssw0rd!"
}
```

**Response `200`**

```json
{
  "success": true,
  "data": { "message": "비밀번호가 변경되었습니다." }
}
```

---

### 2.5. 사용자 목록 조회

> 권한: ADMIN 이상

```
GET /users?search=홍길동&role=EDITOR&group_id=uuid&page=1&limit=20
```

**Query Parameters**

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `search` | string | 이름 또는 이메일 검색 |
| `role` | Role | 역할 필터 |
| `group_id` | UUID | 그룹 필터 |

**Response `200`**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "email": "user@example.com",
        "name": "홍길동",
        "profile_image_url": null,
        "role": "EDITOR",
        "groups": [ { "id": "uuid", "name": "마케팅팀", "type": "DEPARTMENT" } ],
        "joined_at": "2026-02-28T09:00:00Z"
      }
    ],
    "total": 45,
    "page": 1,
    "limit": 20,
    "total_pages": 3
  }
}
```

---

### 2.6. 사용자 단건 조회

> 권한: ADMIN 이상

```
GET /users/:user_id
```

**Response `200`** — 2.1 응답과 동일 구조

---

### 2.7. 다중 사용자 역할 수정

> 권한: ADMIN 이상 (OWNER 역할 부여/취소 불가, 본인 역할 변경 불가)

```
PATCH /users/roles
```

**Request Body**

```json
{
  "updates": [
    { "user_id": "uuid", "role": "VIEWER" },
    { "user_id": "uuid", "role": "EDITOR" }
  ]
}
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "updated_count": 2
  }
}
```

---

### 2.8. 다중 사용자 그룹/프로필 수정

> 권한: ADMIN 이상

```
PATCH /users/profiles
```

**Request Body**

```json
{
  "updates": [
    {
      "user_id": "uuid",
      "name": "홍길동",
      "group_ids": ["uuid-dept", "uuid-position"]
    }
  ]
}
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "updated_count": 1
  }
}
```

---

### 2.9. 사용자 비활성화

> 권한: ADMIN 이상 (OWNER는 비활성화 불가)

```
DELETE /users/:user_id
```

**Response `204`**

---

## 3. 그룹 (Groups)

사용자에게 부여하는 커스텀 그룹 (부서, 직급 등)입니다.
데이터 소스 접근 권한을 그룹 단위로 설정하는 데 사용됩니다.

### 3.1. 그룹 생성

> 권한: ADMIN 이상

```
POST /groups
```

**Request Body**

```json
{
  "name": "마케팅팀",
  "type": "DEPARTMENT",   // DEPARTMENT | POSITION | CUSTOM
  "description": "마케팅 부서"
}
```

**Response `201`**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "마케팅팀",
    "type": "DEPARTMENT",
    "description": "마케팅 부서",
    "member_count": 0,
    "created_at": "2026-02-28T09:00:00Z"
  }
}
```

---

### 3.2. 그룹 목록 조회

```
GET /groups?type=DEPARTMENT
```

**Query Parameters**

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `type` | string | DEPARTMENT \| POSITION \| CUSTOM |

**Response `200`**

```json
{
  "success": true,
  "data": {
    "items": [
      { "id": "uuid", "name": "마케팅팀", "type": "DEPARTMENT", "member_count": 12 }
    ],
    "total": 5
  }
}
```

---

### 3.3. 그룹 수정

> 권한: ADMIN 이상

```
PATCH /groups/:group_id
```

**Request Body**

```json
{
  "name": "마케팅팀",
  "description": "수정된 설명"
}
```

**Response `200`** — 수정된 그룹 전체 반환

---

### 3.4. 그룹 삭제

> 권한: ADMIN 이상

```
DELETE /groups/:group_id
```

**Response `204`**

---

## 4. 대시보드 & 페이지 (Dashboards & Pages)

**개념 정의**
- **페이지(Page)**: 위젯(차트, 표 등)을 px 단위로 배치하는 캔버스 단위. 독립 생성 가능.
- **대시보드(Dashboard)**: 1개 이상의 페이지를 순서대로 묶은 묶음. 탭 또는 슬라이드 형태로 탐색.

### 4.1. 대시보드 생성

> 권한: EDITOR 이상

```
POST /dashboards
```

**Request Body**

```json
{
  "name": "매출 현황 대시보드",
  "description": "브랜드별 일별 매출 요약",
  "is_public": false
}
```

**Response `201`**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "매출 현황 대시보드",
    "description": "브랜드별 일별 매출 요약",
    "is_public": false,
    "owner_id": "uuid",
    "owner_name": "홍길동",
    "page_count": 0,
    "created_at": "2026-02-28T09:00:00Z",
    "updated_at": "2026-02-28T09:00:00Z"
  }
}
```

---

### 4.2. 대시보드 목록 조회

```
GET /dashboards?search=매출&owner_id=uuid&is_favorite=false&page=1&limit=20
```

**Query Parameters**

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `search` | string | 이름 검색 |
| `owner_id` | UUID | 작성자 필터 |
| `is_favorite` | boolean | 즐겨찾기 필터 |

**Response `200`**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "name": "매출 현황 대시보드",
        "description": "...",
        "is_public": false,
        "owner_id": "uuid",
        "owner_name": "홍길동",
        "is_favorite": false,
        "page_count": 3,
        "thumbnail_url": null,
        "created_at": "2026-02-28T09:00:00Z",
        "updated_at": "2026-02-28T09:00:00Z"
      }
    ],
    "total": 12,
    "page": 1,
    "limit": 20,
    "total_pages": 1
  }
}
```

---

### 4.3. 대시보드 단건 조회 (페이지 목록 포함)

```
GET /dashboards/:dashboard_id
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "매출 현황 대시보드",
    "description": "...",
    "is_public": false,
    "owner_id": "uuid",
    "owner_name": "홍길동",
    "is_favorite": false,
    "pages": [
      {
        "id": "uuid",
        "name": "매출 요약",
        "order": 1,
        "width": 1920,
        "height": 1080,
        "thumbnail_url": null
      }
    ],
    "created_at": "2026-02-28T09:00:00Z",
    "updated_at": "2026-02-28T09:00:00Z"
  }
}
```

---

### 4.4. 대시보드 수정

> 권한: 소유자 또는 ADMIN 이상

```
PATCH /dashboards/:dashboard_id
```

**Request Body** (모든 필드 선택적)

```json
{
  "name": "매출 현황 대시보드 v2",
  "description": "수정된 설명",
  "is_public": true
}
```

**Response `200`** — 수정된 대시보드 전체 반환

---

### 4.5. 대시보드 삭제

> 권한: 소유자 또는 ADMIN 이상

```
DELETE /dashboards/:dashboard_id
```

**Response `204`**

---

### 4.6. 대시보드 즐겨찾기 토글

```
POST /dashboards/:dashboard_id/favorite
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "is_favorite": true
  }
}
```

---

### 4.7. 페이지 생성

> 권한: EDITOR 이상

```
POST /dashboards/:dashboard_id/pages
```

**Request Body**

```json
{
  "name": "브랜드별 상세",
  "width": 1920,
  "height": 1080,
  "order": 2,
  "background_color": "#ffffff"
}
```

**Response `201`**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "dashboard_id": "uuid",
    "name": "브랜드별 상세",
    "width": 1920,
    "height": 1080,
    "order": 2,
    "background_color": "#ffffff",
    "owner_id": "uuid",
    "created_at": "2026-02-28T09:00:00Z",
    "updated_at": "2026-02-28T09:00:00Z"
  }
}
```

---

### 4.8. 페이지 상세 조회 (위젯 포함)

```
GET /dashboards/:dashboard_id/pages/:page_id
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "dashboard_id": "uuid",
    "name": "매출 요약",
    "width": 1920,
    "height": 1080,
    "order": 1,
    "background_color": "#f8f9fa",
    "charts": [
      {
        "id": "uuid",
        "type": "TABLE",
        "title": "쇼핑몰별 결제금액",
        "x": 0,
        "y": 0,
        "width": 800,
        "height": 400
      }
    ],
    "filters": [
      {
        "id": "uuid",
        "type": "DATE_RANGE",
        "title": "주문일자",
        "x": 900,
        "y": 10,
        "width": 300,
        "height": 40
      }
    ],
    "created_at": "2026-02-28T09:00:00Z",
    "updated_at": "2026-02-28T09:00:00Z"
  }
}
```

---

### 4.9. 페이지 수정

> 권한: 소유자 또는 ADMIN 이상

```
PATCH /dashboards/:dashboard_id/pages/:page_id
```

**Request Body** (모든 필드 선택적)

```json
{
  "name": "수정된 페이지명",
  "width": 1920,
  "height": 1200,
  "background_color": "#f0f0f0"
}
```

**Response `200`** — 수정된 페이지 전체 반환 (4.8 응답 구조)

---

### 4.10. 페이지 순서 변경

> 권한: 소유자 또는 ADMIN 이상

```
PATCH /dashboards/:dashboard_id/pages/reorder
```

**Request Body**

```json
{
  "orders": [
    { "page_id": "uuid", "order": 1 },
    { "page_id": "uuid", "order": 2 }
  ]
}
```

**Response `200`**

```json
{
  "success": true,
  "data": { "message": "페이지 순서가 변경되었습니다." }
}
```

---

### 4.11. 페이지 삭제

> 권한: 소유자 또는 ADMIN 이상

```
DELETE /dashboards/:dashboard_id/pages/:page_id
```

**Response `204`**

---

### 4.12. 페이지 복제

> 권한: EDITOR 이상

```
POST /dashboards/:dashboard_id/pages/:page_id/duplicate
```

**Request Body** (선택적)

```json
{
  "name": "매출 요약 (복사본)",
  "target_dashboard_id": "uuid"
}  // 다른 대시보드로 복제 시 지정
}
```

**Response `201`** — 새로 생성된 페이지 전체 반환 (4.8 응답 구조)

---

### 4.13. 즐겨찾는 페이지 토글

```
POST /dashboards/:dashboard_id/pages/:page_id/favorite
```

**Response `200`**

```json
{
  "success": true,
  "data": { "is_favorite": true }
}
```

---

## 5. 데이터 소스 (Data Sources)

### 5.1. 데이터 소스 생성 — 외부 DB 연결

> 권한: ADMIN 이상

```
POST /datasources
```

**Request Body**

```json
{
  "label": "메인 주문 DB",
  "source_id": "order_db",
  "source_type": "POSTGRESQL",
  "description": "일별 주문/결제 적재 DB",
  "connection_config": {
    "host": "localhost",
    "port": 5432,
    "database": "sales",
    "username": "readonly_user",
    "password": "secret",
    "schema": "public",
    "query": "SELECT * FROM daily_sales WHERE date = '{{date}}'"
    // BigQuery의 경우 projectId, datasetId, serviceAccountKey 등 포함
  }
}
```

**Response `201`**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "label": "메인 주문 DB",
    "source_id": "order_db",
    "source_type": "POSTGRESQL",
    "description": "일별 주문/결제 적재 DB",
    "field_count": 0,
    "created_at": "2026-02-28T09:00:00Z"
  }
}
```

---

### 5.2. 데이터 소스 생성 — 파일 업로드 (Excel/CSV)

> 권한: ADMIN 이상

```
POST /datasources/upload
Content-Type: multipart/form-data
```

**Form Data**

| 필드 | 타입 | 설명 |
|---|---|---|
| `file` | File | xlsx / csv 파일 (최대 50MB) |
| `label` | string | 데이터 소스 이름 |
| `source_id` | string | 영문 ID |
| `description` | string | (선택) |
| `header_row` | integer | 헤더 행 번호 (기본값: 1) |
| `sheet_name` | string | xlsx 시트명 (기본값: 첫 번째 시트) |

**Response `201`** — 5.1 응답과 동일 구조

---

### 5.3. 연결 테스트

> 권한: ADMIN 이상

외부 DB 연결 정보의 유효성을 사전 확인합니다.

```
POST /datasources/test-connection
```

**Request Body** — 5.1의 `connection_config`와 동일

**Response `200`**

```json
{
  "success": true,
  "data": {
    "connected": true,
    "message": "연결 성공",
    "sample_columns": ["date", "brand", "settlement_amount"]
  }
}
```

---

### 5.4. 데이터 소스 목록 조회

```
GET /datasources?source_type=POSTGRESQL&search=주문
```

**Query Parameters**

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `source_type` | DSSourceType | 유형 필터 |
| `search` | string | label 또는 source_id 검색 |

**Response `200`**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "label": "메인 주문 DB",
        "source_id": "order_db",
        "source_type": "POSTGRESQL",
        "description": "...",
        "field_count": 24,
        "has_access": true,
        "created_at": "2026-02-28T09:00:00Z"
      }
    ],
    "total": 5
  }
}
```

---

### 5.5. 데이터 소스 필드 목록 조회

```
GET /datasources/:datasource_id/fields
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "datasource_id": "uuid",
    "source_id": "order_db",
    "label": "메인 주문 DB",
    "fields": [
      {
        "id": "uuid",
        "field_id": "settlement_amount",
        "label": "결제금액",
        "type": "NUMBER",
        "default_aggregate": "SUM",
        "description": "정산금액 기준 결제금액",
        "number_format": "#,##0",
        "order": 1,
        "is_hidden": false
      }
    ]
  }
}
```

---

### 5.6. 데이터 소스 필드 다중 수정

> 권한: ADMIN 이상

```
PATCH /datasources/:datasource_id/fields
```

**Request Body**

```json
{
  "updates": [
    {
      "field_id": "settlement_amount",
      "label": "결제금액",
      "type": "NUMBER",
      "default_aggregate": "SUM",
      "description": "정산금액 기준",
      "number_format": "#,##0",
      "order": 1,
      "is_hidden": false
    }
  ]
}
```

**Response `200`**

```json
{
  "success": true,
  "data": { "updated_count": 1 }
}
```

---

### 5.7. 데이터 소스 수정

> 권한: ADMIN 이상

```
PATCH /datasources/:datasource_id
```

**Request Body** (모든 필드 선택적)

```json
{
  "label": "수정된 이름",
  "description": "수정된 설명",
  "connection_config": { ... }
}
```

**Response `200`** — 수정된 데이터 소스 전체 반환

---

### 5.8. 데이터 소스 삭제

> 권한: ADMIN 이상

```
DELETE /datasources/:datasource_id
```

**Response `204`**

---

### 5.9. 데이터 소스 접근 권한 설정

> 권한: ADMIN 이상

```
PUT /datasources/:datasource_id/permissions
```

**Request Body**

지정하지 않은 대상은 기본적으로 접근 불가입니다.
`allow_all: true`로 전체 허용 가능합니다.

```json
{
  "allow_all": false,
  "group_ids": ["uuid1", "uuid2"],
  "user_ids": ["uuid3"]
}
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "allow_all": false,
    "group_ids": ["uuid1", "uuid2"],
    "user_ids": ["uuid3"]
  }
}
```

---

### 5.10. 데이터 소스 접근 권한 조회

> 권한: ADMIN 이상

```
GET /datasources/:datasource_id/permissions
```

**Response `200`** — 5.9 응답과 동일 구조

---

### 5.11. 데이터 소스 연관 대시보드/페이지 목록 조회

```
GET /datasources/:datasource_id/references
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "dashboards": [
      { "id": "uuid", "name": "매출 현황 대시보드" }
    ],
    "pages": [
      { "id": "uuid", "name": "브랜드별 상세", "dashboard_id": "uuid", "dashboard_name": "매출 현황 대시보드" }
    ]
  }
}
```

---

### 5.12. 데이터 소스 스키마 동기화

외부 DB 변경 사항(컬럼 추가/삭제)을 감지하여 필드 목록을 갱신합니다.

> 권한: ADMIN 이상

```
POST /datasources/:datasource_id/sync
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "added_fields": ["new_column"],
    "removed_fields": ["old_column"],
    "message": "스키마 동기화 완료"
  }
}
```

---

### 5.13. 데이터 소스 미리보기

```
GET /datasources/:datasource_id/preview?limit=10
```

**Query Parameters**

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `limit` | integer | 10 | 미리보기 행 수 (최대 100) |

**Response `200`**

```json
{
  "success": true,
  "data": {
    "columns": ["date", "brand", "settlement_amount"],
    "rows": [
      ["2026-02-02", "닥터트루", 13681410]
    ],
    "total_rows": 1234
  }
}
```

---

## 6. 차트 (Charts)

### 6.1. 차트 생성

> 권한: EDITOR 이상 (해당 페이지 소유자 또는 ADMIN)

```
POST /dashboards/:dashboard_id/pages/:page_id/charts
```

**Request Body**

```json
{
  "type": "TABLE",
  "title": "쇼핑몰별 결제금액",
  "x": 0,
  "y": 0,
  "width": 800,
  "height": 400,
  "datasource_id": "uuid",
  "config": {
    "dimensions": [
      { "field_id": "brand", "label": "브랜드", "order": 1 }
    ],
    "metrics": [
      {
        "field_id": "settlement_amount",
        "label": "결제금액",
        "aggregate": "SUM",
        "number_format": "#,##0",
        "order": 1
      }
    ],
    "default_sort": { "field_id": "settlement_amount", "direction": "DESC" },
    "rows_per_page": 20,
    "show_totals_row": true
  }
}
```

**Response `201`**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "page_id": "uuid",
    "type": "TABLE",
    "title": "쇼핑몰별 결제금액",
    "x": 0,
    "y": 0,
    "width": 800,
    "height": 400,
    "datasource_id": "uuid",
    "config": { ... },
    "style": { ... },
    "created_at": "2026-02-28T09:00:00Z"
  }
}
```

**차트 타입별 `config` 주요 필드**

| 타입 | 주요 config 필드 |
|---|---|
| TABLE | dimensions, metrics, default_sort, rows_per_page, show_totals_row, frozen_columns |
| PIVOT | row_dimension, col_dimension, metrics, show_subtotals |
| LINE / BAR | x_axis (dimension), y_axis (metrics), legend, smooth |
| STACKED_BAR | x_axis, series (dimension), metrics |
| PIE | dimension, metric |
| SCORECARD | metric, comparison_metric, comparison_label |

---

### 6.2. 차트 단건 조회

```
GET /dashboards/:dashboard_id/pages/:page_id/charts/:chart_id
```

**Response `200`** — 6.1 응답과 동일 구조

---

### 6.3. 차트 수정 (설정)

> 권한: 소유자 또는 ADMIN 이상

```
PATCH /dashboards/:dashboard_id/pages/:page_id/charts/:chart_id
```

**Request Body** (모든 필드 선택적)

```json
{
  "title": "수정된 차트 제목",
  "x": 10,
  "y": 20,
  "width": 900,
  "height": 450,
  "config": { ... }
}
```

**Response `200`** — 수정된 차트 전체 반환

---

### 6.4. 차트 스타일 수정

> 권한: 소유자 또는 ADMIN 이상

```
PATCH /dashboards/:dashboard_id/pages/:page_id/charts/:chart_id/style
```

**Request Body**

```json
{
  "header": {
    "font_size": 13,
    "font_weight": "bold",
    "background_color": "#f1f5f9",
    "text_color": "#1e293b",
    "wrap_text": false
  },
  "body": {
    "font_size": 13,
    "alternate_row_color": "#f8fafc",
    "border_color": "#e2e8f0"
  },
  "totals_row": {
    "background_color": "#e2e8f0",
    "font_weight": "bold"
  },
  "show_border": true,
  "border_radius": 4,
  "padding": { "top": 8, "right": 12, "bottom": 8, "left": 12 }
}
```

**Response `200`**

```json
{
  "success": true,
  "data": { "style": { ... } }
}
```

---

### 6.5. 차트 삭제

> 권한: 소유자 또는 ADMIN 이상

```
DELETE /dashboards/:dashboard_id/pages/:page_id/charts/:chart_id
```

**Response `204`**

---

### 6.6. 차트 복제

> 권한: EDITOR 이상

```
POST /dashboards/:dashboard_id/pages/:page_id/charts/:chart_id/duplicate
```

**Request Body** (선택적)

```json
{
  "target_page_id": "uuid",
  "offset_x": 20,
  "offset_y": 20
}
```

**Response `201`** — 새로 생성된 차트 전체 반환

---

### 6.7. 다중 차트 위치/크기 일괄 수정

드래그 후 일괄 저장에 사용됩니다.

> 권한: 소유자 또는 ADMIN 이상

```
PATCH /dashboards/:dashboard_id/pages/:page_id/charts/positions
```

**Request Body**

```json
{
  "updates": [
    { "chart_id": "uuid", "x": 0, "y": 0, "width": 800, "height": 400 },
    { "chart_id": "uuid", "x": 820, "y": 0, "width": 400, "height": 400 }
  ]
}
```

**Response `200`**

```json
{
  "success": true,
  "data": { "updated_count": 2 }
}
```

---

### 6.8. 차트 그룹 생성

여러 차트를 하나의 그룹으로 묶어 이동/크기 조정 연동.

> 권한: 소유자 또는 ADMIN 이상

```
POST /dashboards/:dashboard_id/pages/:page_id/chart-groups
```

**Request Body**

```json
{
  "name": "브랜드 섹션",
  "chart_ids": ["uuid1", "uuid2"]
}
```

**Response `201`**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "브랜드 섹션",
    "chart_ids": ["uuid1", "uuid2"]
  }
}
```

---

### 6.9. 차트 데이터 조회

차트 렌더링을 위한 실제 데이터를 반환합니다.
필터 파라미터는 현재 페이지에 활성화된 필터 값들을 전달합니다.

```
POST /dashboards/:dashboard_id/pages/:page_id/charts/:chart_id/data
```

**Request Body**

```json
{
  "filters": [
    { "filter_id": "uuid", "value": "2026-02-01" },
    { "filter_id": "uuid", "value": ["닥터트루", "바른농장"] }
  ],
  "sort": { "field_id": "settlement_amount", "direction": "DESC" },
  "page": 1,
  "limit": 20
}
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "columns": [
      { "field_id": "brand", "label": "브랜드", "type": "TEXT" },
      { "field_id": "settlement_amount", "label": "결제금액", "type": "NUMBER", "aggregate": "SUM" }
    ],
    "rows": [
      ["닥터트루", 13681410],
      ["바른농장", 585780]
    ],
    "totals": [null, 39734385],
    "total": 5,
    "page": 1,
    "limit": 20,
    "queried_at": "2026-02-28T09:01:23Z"
  }
}
```

---

### 6.10. 차트 데이터 내보내기

```
POST /dashboards/:dashboard_id/pages/:page_id/charts/:chart_id/export
```

**Request Body**

```json
{
  "format": "XLSX",
  "filters": [ ... ],
  "include_headers": true
}
```

**Response `200`**

```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="chart_export_20260228.xlsx"
(바이너리 스트림)
```

---

## 7. 필터 (Filters)

필터는 페이지 내에 UI 요소로 배치되거나, 차트/페이지에 고정 적용되는 기본 필터로 사용됩니다.

### 7.1. 필터 생성

> 권한: EDITOR 이상

```
POST /dashboards/:dashboard_id/pages/:page_id/filters
```

**Request Body**

```json
{
  "type": "DATE_RANGE",
  "title": "주문일자",
  "x": 1600,
  "y": 10,
  "width": 280,
  "height": 40,
  "datasource_id": "uuid",
  "field_id": "order_date",
  "config": {
    "default_value": "LAST_7_DAYS",
    "apply_to": "PAGE"
  }
}
```

**Response `201`**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "type": "DATE_RANGE",
    "title": "주문일자",
    "x": 1600,
    "y": 10,
    "width": 280,
    "height": 40,
    "datasource_id": "uuid",
    "field_id": "order_date",
    "config": { ... },
    "created_at": "2026-02-28T09:00:00Z"
  }
}
```

**필터 타입별 `config` 주요 필드**

| 타입 | config 필드 |
|---|---|
| DROPDOWN | `multi_select: boolean`, `default_value: string[]`, `apply_to` |
| TEXT_INPUT | `operator: FilterOp`, `placeholder`, `apply_to` |
| RANGE | `operator: FilterOp`, `min, max`, `step`, `apply_to` |
| DATE_RANGE | `default_value`, `apply_to` |

---

### 7.2. 필터 수정

> 권한: 소유자 또는 ADMIN 이상

```
PATCH /dashboards/:dashboard_id/pages/:page_id/filters/:filter_id
```

**Request Body** (모든 필드 선택적) — 7.1 Request Body 참고

**Response `200`** — 수정된 필터 전체 반환

---

### 7.3. 필터 삭제

> 권한: 소유자 또는 ADMIN 이상

```
DELETE /dashboards/:dashboard_id/pages/:page_id/filters/:filter_id
```

**Response `204`**

---

### 7.4. 기본 필터 설정 (차트 또는 페이지에 고정 적용)

> 권한: 소유자 또는 ADMIN 이상

```
PUT /dashboards/:dashboard_id/pages/:page_id/default-filters
```

**Request Body**

```json
{
  "apply_to": "PAGE",
  "rules": [
    {
      "datasource_id": "uuid",
      "field_id": "is_active",
      "operator": "EQ",
      "value": true
    },
    {
      "datasource_id": "uuid",
      "field_id": "brand",
      "operator": "EQ",
      "value": "닥터트루"
    }
  ]
}
```

**Response `200`**

```json
{
  "success": true,
  "data": { "rules": [ ... ] }
}
```

---

## 8. 조건부 서식 (Conditional Formatting)

### 8.1. 조건부 서식 목록 조회

```
GET /dashboards/:dashboard_id/pages/:page_id/charts/:chart_id/conditional-formats
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "chart_id": "uuid",
        "name": "ROI 색상 서식",
        "order": 1,
        "apply_to": "CELL",
        "target_fields": ["roi"],
        "rules": [
          {
            "operator": "LT",
            "value": 0,
            "style": {
              "background_color": "#fee2e2",
              "color": "#dc2626",
              "font_weight": "bold"
            }
          },
          {
            "operator": "GTE",
            "value": 50,
            "style": {
              "background_color": "#dcfce7",
              "color": "#16a34a"
            }
          }
        ]
      }
    ]
  }
}
```

---

### 8.2. 조건부 서식 생성

> 권한: EDITOR 이상

```
POST /dashboards/:dashboard_id/pages/:page_id/charts/:chart_id/conditional-formats
```

**Request Body**

```json
{
  "name": "ROI 색상 서식",
  "apply_to": "CELL",
  "target_fields": ["roi"],
  "rules": [
    {
      "operator": "LT",
      "value": 0,
      "second_value": null,
      "style": {
        "background_color": "#fee2e2",
        "color": "#dc2626",
        "font_weight": "normal",
        "font_style": "normal",
        "text_decoration": "none"
      }
    }
  ]
}
```

**Response `201`**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "ROI 색상 서식",
    "order": 1,
    "apply_to": "CELL",
    "target_fields": ["roi"],
    "rules": [ ... ],
    "created_at": "2026-02-28T09:00:00Z"
  }
}
```

---

### 8.3. 조건부 서식 수정

> 권한: EDITOR 이상

```
PATCH /dashboards/:dashboard_id/pages/:page_id/charts/:chart_id/conditional-formats/:format_id
```

**Request Body** — 8.2 Request Body 참고 (모든 필드 선택적)

**Response `200`** — 수정된 서식 전체 반환

---

### 8.4. 조건부 서식 삭제

> 권한: EDITOR 이상

```
DELETE /dashboards/:dashboard_id/pages/:page_id/charts/:chart_id/conditional-formats/:format_id
```

**Response `204`**

---

### 8.5. 조건부 서식 순서 변경

서식은 위에서 아래로 순서대로 평가되며, 첫 번째 매칭 규칙이 적용됩니다.

> 권한: EDITOR 이상

```
PATCH /dashboards/:dashboard_id/pages/:page_id/charts/:chart_id/conditional-formats/reorder
```

**Request Body**

```json
{
  "orders": [
    { "format_id": "uuid", "order": 1 },
    { "format_id": "uuid", "order": 2 }
  ]
}
```

**Response `200`**

```json
{
  "success": true,
  "data": { "message": "순서가 변경되었습니다." }
}
```

---

### 8.6. 조건부 서식 복사 (다른 차트로)

> 권한: EDITOR 이상

```
POST /dashboards/:dashboard_id/pages/:page_id/charts/:chart_id/conditional-formats/:format_id/copy
```

**Request Body**

```json
{
  "target_chart_id": "uuid"
}
```

**Response `201`** — 새로 생성된 서식 전체 반환

---

## 9. 개인 뷰 설정 (User View Configs)

Viewer 포함 모든 사용자가 차트의 메트릭, 정렬 등을 개인적으로 오버라이드하여 저장합니다.
본인에게만 적용되며 원본 차트 설정에는 영향을 주지 않습니다.

### 9.1. 개인 뷰 저장/갱신

```
PUT /dashboards/:dashboard_id/pages/:page_id/charts/:chart_id/my-view
```

**Request Body** (모든 필드 선택적, 저장할 항목만 포함)

```json
{
  "metrics": ["settlement_amount", "margin", "roi"],
  "sort": { "field_id": "settlement_amount", "direction": "DESC" },
  "column_widths": { "brand": 120, "roi": 80 },
  "frozen_columns": ["brand"],
  "rows_per_page": 50
}
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "chart_id": "uuid",
    "config": { ... },
    "updated_at": "2026-02-28T09:05:00Z"
  }
}
```

---

### 9.2. 개인 뷰 조회

```
GET /dashboards/:dashboard_id/pages/:page_id/charts/:chart_id/my-view
```

**Response `200`** — 9.1 응답과 동일 구조

---

### 9.3. 개인 뷰 초기화

```
DELETE /dashboards/:dashboard_id/pages/:page_id/charts/:chart_id/my-view
```

**Response `204`**

---

## 10. 숫자/날짜 서식 (Number Formats)

### 10.1. 사전 정의 서식 목록 조회

프런트엔드 서식 선택 드롭다운에 사용합니다.

```
GET /number-formats
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "number": [
      { "id": "comma", "label": "천 단위 구분", "format": "#,##0" },
      { "id": "comma_decimal2", "label": "소수 2자리", "format": "#,##0.00" },
      { "id": "percent", "label": "백분율", "format": "0.00%" },
      { "id": "krw", "label": "원화", "format": "₩#,##0" }
    ],
    "date": [
      { "id": "date_kr", "label": "한국 날짜", "format": "YYYY.MM.DD" },
      { "id": "datetime_kr", "label": "한국 날짜+시간", "format": "YYYY.MM.DD HH:mm" }
    ]
  }
}
```

---

## 11. 알림 (Notifications)

### 11.1. 내 알림 목록 조회

```
GET /notifications?is_read=false
```

**Query Parameters**

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `is_read` | boolean | 읽음 여부 필터 |

**Response `200`**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "type": "REGISTER_REQUEST",
        "title": "새 회원가입 요청",
        "message": "홍길동(user@example.com) 님이 회원가입을 요청했습니다.",
        "link_url": "/admin/users/requests",
        "is_read": false,
        "created_at": "2026-02-28T09:00:00Z"
      }
    ],
    "unread_count": 3
  }
}
```

---

### 11.2. 알림 읽음 처리

```
PATCH /notifications/read
```

**Request Body**

```json
{
  "notification_ids": ["uuid1", "uuid2"],
  "read_all": false
}
```

**Response `200`**

```json
{
  "success": true,
  "data": { "updated_count": 2 }
}
```

---

## 12. SMTP 설정 (Admin)

### 12.1. SMTP 설정 조회

> 권한: ADMIN 이상

```
GET /admin/smtp
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "host": "smtp.gmail.com",
    "port": 587,
    "username": "noreply@example.com",
    "use_tls": true,
    "from_name": "LookFlex",
    "from_email": "noreply@example.com",
    "is_configured": true
  }
}
```

---

### 12.2. SMTP 설정 저장

> 권한: ADMIN 이상

```
PUT /admin/smtp
```

**Request Body**

```json
{
  "host": "smtp.gmail.com",
  "port": 587,
  "username": "noreply@example.com",
  "password": "app-password",
  "use_tls": true,
  "from_name": "LookFlex",
  "from_email": "noreply@example.com"
}
```

**Response `200`** — 12.1 응답과 동일 구조 (password 제외)

---

### 12.3. SMTP 연결 테스트

> 권한: ADMIN 이상

```
POST /admin/smtp/test
```

**Request Body**

```json
{
  "to_email": "test@example.com"
}
```

**Response `200`**

```json
{
  "success": true,
  "data": { "message": "테스트 이메일이 발송되었습니다." }
}
```

---

## 13. 시스템 (System)

### 13.1. 헬스 체크

인증 불필요.

```
GET /health
```

**Response `200`**

```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2026-02-28T09:00:00Z"
}
```

---

### 13.2. 감사 로그 조회

> 권한: ADMIN 이상

```
GET /admin/audit-logs?user_id=uuid&action=DATA_QUERY&from=2026-02-01T00:00:00Z&to=2026-02-28T23:59:59Z&page=1&limit=50
```

**Query Parameters**

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `user_id` | UUID | 특정 사용자 필터 |
| `action` | string | 액션 타입 필터 |
| `from` | ISO8601 | 시작 일시 |
| `to` | ISO8601 | 종료 일시 |

**Action 타입**: `LOGIN` \| `LOGOUT` \| `DATA_QUERY` \| `EXPORT` \| `DASHBOARD_EDIT` \| `DATASOURCE_EDIT` \| `USER_EDIT`

**Response `200`**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "user_id": "uuid",
        "user_name": "홍길동",
        "action": "DATA_QUERY",
        "detail": { "chart_id": "uuid", "datasource_id": "uuid" },
        "ip_address": "192.168.1.10",
        "created_at": "2026-02-28T09:01:23Z"
      }
    ],
    "total": 200,
    "page": 1,
    "limit": 50,
    "total_pages": 4
  }
}
```

---

*총 API 엔드포인트: 약 60개*
*최종 업데이트: 2026-02-28*
