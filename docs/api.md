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

```
Role         : OWNER | ADMIN | EDITOR | VIEWER
FieldType    : TEXT | NUMBER | DATE | DATETIME | BOOLEAN
AggregateType: SUM | AVG | MIN | MAX | COUNT | COUNT_DISTINCT | NONE
ChartType    : TABLE | PIVOT | LINE | BAR | STACKED_BAR | PIE | SCORECARD
FilterType   : DROPDOWN | TEXT_INPUT | RANGE | DATE_RANGE
FilterOp     : EQ | NEQ | CONTAINS | NOT_CONTAINS | STARTS_WITH | ENDS_WITH
             | REGEX | GT | GTE | LT | LTE | BETWEEN | IS_NULL | IS_NOT_NULL
SortDir      : ASC | DESC
DSSourceType : POSTGRESQL | MYSQL | MSSQL | BIGQUERY | EXCEL | CSV
ApprovalStatus: PENDING | APPROVED | REJECTED
```

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
    "totalPages": 6
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

---

### 1.4. 회원가입 요청

`/verify-email` 완료 후 나머지 정보를 제출합니다.
Redis에 인증 완료된 이메일이 없으면 403을 반환합니다.
승인된 이후 로그인 가능 상태로 사용자 계정이 생성됩니다.

```
POST /auth/register
```

**Request Body**

```json
{
  "email": "user@example.com",
  "password": "P@ssw0rd!",
  "name": "홍길동",
  "requested_role": "EDITOR"   // EDITOR | VIEWER 만 선택 가능
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
| 409 | EMAIL_ALREADY_EXISTS | 이미 가입된 이메일 |
| 409 | REGISTER_REQUEST_PENDING | 동일 이메일로 대기 중인 요청 존재 |

---

### 1.5. 로그인

```
POST /auth/login
```

**Request Body**

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
    "accessToken": "eyJ...",
    "tokenType": "Bearer",
    "expiresIn": 900
  }
}
```

Set-Cookie: `refresh_token=<token>; HttpOnly; SameSite=Strict; Path=/api/v1/auth/refresh; Max-Age=604800`

**Error Cases**

| 상태 | code | 설명 |
|---|---|---|
| 401 | INVALID_CREDENTIALS | 이메일 또는 비밀번호 불일치 |
| 403 | EMAIL_NOT_VERIFIED | 이메일 미인증 |
| 403 | APPROVAL_PENDING | 관리자 승인 대기 중 |
| 403 | APPROVAL_REJECTED | 가입 요청 거절됨 |

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
    "accessToken": "eyJ...",
    "tokenType": "Bearer",
    "expiresIn": 900
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
        "requestedRole": "EDITOR",
        "status": "PENDING",
        "emailVerifiedAt": "2026-02-28T09:00:00Z",
        "createdAt": "2026-02-28T08:55:00Z"
      }
    ],
    "total": 3,
    "page": 1,
    "limit": 20,
    "totalPages": 1
  }
}
```

---

### 1.9. 회원가입 요청 처리 (승인/거절)

> 권한: ADMIN 이상

```
PATCH /auth/register-requests/:requestId
```

**Path Parameters**

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `requestId` | UUID | 요청 ID |

**Request Body**

```json
{
  "status": "APPROVED",       // APPROVED | REJECTED
  "assignedRole": "EDITOR",   // 승인 시 필수 (EDITOR | VIEWER)
  "rejectReason": null        // 거절 시 선택
}
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "userId": "uuid",         // 승인 시에만 반환
    "status": "APPROVED"
  }
}
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

```json
{
  "token": "reset-token-from-email",
  "newPassword": "NewP@ssw0rd!"
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
    "profileImageUrl": "https://...",
    "role": "EDITOR",
    "groups": [
      { "id": "uuid", "name": "마케팅팀", "type": "DEPARTMENT" },
      { "id": "uuid", "name": "대리", "type": "POSITION" }
    ],
    "joinedAt": "2026-02-28T09:00:00Z"
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
  "profileImageUrl": "https://..."
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
    "profileImageUrl": "https://..."
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
  "currentPassword": "P@ssw0rd!",
  "newPassword": "NewP@ssw0rd!"
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
GET /users?search=홍길동&role=EDITOR&groupId=uuid&page=1&limit=20
```

**Query Parameters**

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `search` | string | 이름 또는 이메일 검색 |
| `role` | Role | 역할 필터 |
| `groupId` | UUID | 그룹 필터 |

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
        "profileImageUrl": null,
        "role": "EDITOR",
        "groups": [ { "id": "uuid", "name": "마케팅팀", "type": "DEPARTMENT" } ],
        "joinedAt": "2026-02-28T09:00:00Z"
      }
    ],
    "total": 45,
    "page": 1,
    "limit": 20,
    "totalPages": 3
  }
}
```

---

### 2.6. 사용자 단건 조회

> 권한: ADMIN 이상

```
GET /users/:userId
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
    { "userId": "uuid", "role": "VIEWER" },
    { "userId": "uuid", "role": "EDITOR" }
  ]
}
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "updatedCount": 2
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
      "userId": "uuid",
      "name": "홍길동",
      "groupIds": ["uuid-dept", "uuid-position"]
    }
  ]
}
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "updatedCount": 1
  }
}
```

---

### 2.9. 사용자 비활성화

> 권한: ADMIN 이상 (OWNER는 비활성화 불가)

```
DELETE /users/:userId
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
    "memberCount": 0,
    "createdAt": "2026-02-28T09:00:00Z"
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
      { "id": "uuid", "name": "마케팅팀", "type": "DEPARTMENT", "memberCount": 12 }
    ],
    "total": 5
  }
}
```

---

### 3.3. 그룹 수정

> 권한: ADMIN 이상

```
PATCH /groups/:groupId
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
DELETE /groups/:groupId
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
  "isPublic": false
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
    "isPublic": false,
    "ownerId": "uuid",
    "ownerName": "홍길동",
    "pageCount": 0,
    "createdAt": "2026-02-28T09:00:00Z",
    "updatedAt": "2026-02-28T09:00:00Z"
  }
}
```

---

### 4.2. 대시보드 목록 조회

```
GET /dashboards?search=매출&ownerId=uuid&isFavorite=false&page=1&limit=20
```

**Query Parameters**

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `search` | string | 이름 검색 |
| `ownerId` | UUID | 작성자 필터 |
| `isFavorite` | boolean | 즐겨찾기 필터 |

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
        "isPublic": false,
        "ownerId": "uuid",
        "ownerName": "홍길동",
        "isFavorite": false,
        "pageCount": 3,
        "thumbnailUrl": null,
        "createdAt": "2026-02-28T09:00:00Z",
        "updatedAt": "2026-02-28T09:00:00Z"
      }
    ],
    "total": 12,
    "page": 1,
    "limit": 20,
    "totalPages": 1
  }
}
```

---

### 4.3. 대시보드 단건 조회 (페이지 목록 포함)

```
GET /dashboards/:dashboardId
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "매출 현황 대시보드",
    "description": "...",
    "isPublic": false,
    "ownerId": "uuid",
    "ownerName": "홍길동",
    "isFavorite": false,
    "pages": [
      {
        "id": "uuid",
        "name": "매출 요약",
        "order": 1,
        "width": 1920,
        "height": 1080,
        "thumbnailUrl": null
      }
    ],
    "createdAt": "2026-02-28T09:00:00Z",
    "updatedAt": "2026-02-28T09:00:00Z"
  }
}
```

---

### 4.4. 대시보드 수정

> 권한: 소유자 또는 ADMIN 이상

```
PATCH /dashboards/:dashboardId
```

**Request Body** (모든 필드 선택적)

```json
{
  "name": "매출 현황 대시보드 v2",
  "description": "수정된 설명",
  "isPublic": true
}
```

**Response `200`** — 수정된 대시보드 전체 반환

---

### 4.5. 대시보드 삭제

> 권한: 소유자 또는 ADMIN 이상

```
DELETE /dashboards/:dashboardId
```

**Response `204`**

---

### 4.6. 대시보드 즐겨찾기 토글

```
POST /dashboards/:dashboardId/favorite
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "isFavorite": true
  }
}
```

---

### 4.7. 페이지 생성

> 권한: EDITOR 이상

```
POST /dashboards/:dashboardId/pages
```

**Request Body**

```json
{
  "name": "브랜드별 상세",
  "width": 1920,
  "height": 1080,
  "order": 2,
  "backgroundColor": "#ffffff"
}
```

**Response `201`**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "dashboardId": "uuid",
    "name": "브랜드별 상세",
    "width": 1920,
    "height": 1080,
    "order": 2,
    "backgroundColor": "#ffffff",
    "ownerId": "uuid",
    "createdAt": "2026-02-28T09:00:00Z",
    "updatedAt": "2026-02-28T09:00:00Z"
  }
}
```

---

### 4.8. 페이지 상세 조회 (위젯 포함)

```
GET /dashboards/:dashboardId/pages/:pageId
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "dashboardId": "uuid",
    "name": "매출 요약",
    "width": 1920,
    "height": 1080,
    "order": 1,
    "backgroundColor": "#f8f9fa",
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
    "createdAt": "2026-02-28T09:00:00Z",
    "updatedAt": "2026-02-28T09:00:00Z"
  }
}
```

---

### 4.9. 페이지 수정

> 권한: 소유자 또는 ADMIN 이상

```
PATCH /dashboards/:dashboardId/pages/:pageId
```

**Request Body** (모든 필드 선택적)

```json
{
  "name": "수정된 페이지명",
  "width": 1920,
  "height": 1200,
  "backgroundColor": "#f0f0f0"
}
```

**Response `200`** — 수정된 페이지 전체 반환 (4.8 응답 구조)

---

### 4.10. 페이지 순서 변경

> 권한: 소유자 또는 ADMIN 이상

```
PATCH /dashboards/:dashboardId/pages/reorder
```

**Request Body**

```json
{
  "orders": [
    { "pageId": "uuid", "order": 1 },
    { "pageId": "uuid", "order": 2 }
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
DELETE /dashboards/:dashboardId/pages/:pageId
```

**Response `204`**

---

### 4.12. 페이지 복제

> 권한: EDITOR 이상

```
POST /dashboards/:dashboardId/pages/:pageId/duplicate
```

**Request Body** (선택적)

```json
{
  "name": "매출 요약 (복사본)",
  "targetDashboardId": "uuid"  // 다른 대시보드로 복제 시 지정
}
```

**Response `201`** — 새로 생성된 페이지 전체 반환 (4.8 응답 구조)

---

### 4.13. 즐겨찾는 페이지 토글

```
POST /dashboards/:dashboardId/pages/:pageId/favorite
```

**Response `200`**

```json
{
  "success": true,
  "data": { "isFavorite": true }
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
  "sourceId": "order_db",         // 영문, 언더스코어. 필드 접근 시 prefix로 사용
  "sourceType": "POSTGRESQL",
  "description": "일별 주문/결제 적재 DB",
  "connectionConfig": {
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
    "sourceId": "order_db",
    "sourceType": "POSTGRESQL",
    "description": "일별 주문/결제 적재 DB",
    "fieldCount": 0,
    "createdAt": "2026-02-28T09:00:00Z"
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
| `sourceId` | string | 영문 ID |
| `description` | string | (선택) |
| `headerRow` | integer | 헤더 행 번호 (기본값: 1) |
| `sheetName` | string | xlsx 시트명 (기본값: 첫 번째 시트) |

**Response `201`** — 5.1 응답과 동일 구조

---

### 5.3. 연결 테스트

> 권한: ADMIN 이상

외부 DB 연결 정보의 유효성을 사전 확인합니다.

```
POST /datasources/test-connection
```

**Request Body** — 5.1의 `connectionConfig`와 동일

**Response `200`**

```json
{
  "success": true,
  "data": {
    "connected": true,
    "message": "연결 성공",
    "sampleColumns": ["date", "brand", "settlement_amount"]
  }
}
```

---

### 5.4. 데이터 소스 목록 조회

```
GET /datasources?sourceType=POSTGRESQL&search=주문
```

**Query Parameters**

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `sourceType` | DSSourceType | 유형 필터 |
| `search` | string | label 또는 sourceId 검색 |

**Response `200`**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "label": "메인 주문 DB",
        "sourceId": "order_db",
        "sourceType": "POSTGRESQL",
        "description": "...",
        "fieldCount": 24,
        "hasAccess": true,
        "createdAt": "2026-02-28T09:00:00Z"
      }
    ],
    "total": 5
  }
}
```

---

### 5.5. 데이터 소스 필드 목록 조회

```
GET /datasources/:datasourceId/fields
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "datasourceId": "uuid",
    "sourceId": "order_db",
    "label": "메인 주문 DB",
    "fields": [
      {
        "id": "uuid",
        "fieldId": "settlement_amount",
        "label": "결제금액",
        "type": "NUMBER",
        "defaultAggregate": "SUM",
        "description": "정산금액 기준 결제금액",
        "numberFormat": "#,##0",
        "order": 1,
        "isHidden": false
      }
    ]
  }
}
```

---

### 5.6. 데이터 소스 필드 다중 수정

> 권한: ADMIN 이상

```
PATCH /datasources/:datasourceId/fields
```

**Request Body**

```json
{
  "updates": [
    {
      "fieldId": "settlement_amount",
      "label": "결제금액",
      "type": "NUMBER",
      "defaultAggregate": "SUM",
      "description": "정산금액 기준",
      "numberFormat": "#,##0",
      "order": 1,
      "isHidden": false
    }
  ]
}
```

**Response `200`**

```json
{
  "success": true,
  "data": { "updatedCount": 1 }
}
```

---

### 5.7. 데이터 소스 수정

> 권한: ADMIN 이상

```
PATCH /datasources/:datasourceId
```

**Request Body** (모든 필드 선택적)

```json
{
  "label": "수정된 이름",
  "description": "수정된 설명",
  "connectionConfig": { ... }
}
```

**Response `200`** — 수정된 데이터 소스 전체 반환

---

### 5.8. 데이터 소스 삭제

> 권한: ADMIN 이상

```
DELETE /datasources/:datasourceId
```

**Response `204`**

---

### 5.9. 데이터 소스 접근 권한 설정

> 권한: ADMIN 이상

```
PUT /datasources/:datasourceId/permissions
```

**Request Body**

지정하지 않은 대상은 기본적으로 접근 불가입니다.
`allowAll: true`로 전체 허용 가능합니다.

```json
{
  "allowAll": false,
  "groupIds": ["uuid1", "uuid2"],
  "userIds": ["uuid3"]
}
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "allowAll": false,
    "groupIds": ["uuid1", "uuid2"],
    "userIds": ["uuid3"]
  }
}
```

---

### 5.10. 데이터 소스 접근 권한 조회

> 권한: ADMIN 이상

```
GET /datasources/:datasourceId/permissions
```

**Response `200`** — 5.9 응답과 동일 구조

---

### 5.11. 데이터 소스 연관 대시보드/페이지 목록 조회

```
GET /datasources/:datasourceId/references
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
      { "id": "uuid", "name": "브랜드별 상세", "dashboardId": "uuid", "dashboardName": "매출 현황 대시보드" }
    ]
  }
}
```

---

### 5.12. 데이터 소스 스키마 동기화

외부 DB 변경 사항(컬럼 추가/삭제)을 감지하여 필드 목록을 갱신합니다.

> 권한: ADMIN 이상

```
POST /datasources/:datasourceId/sync
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "addedFields": ["new_column"],
    "removedFields": ["old_column"],
    "message": "스키마 동기화 완료"
  }
}
```

---

### 5.13. 데이터 소스 미리보기

```
GET /datasources/:datasourceId/preview?limit=10
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
    "totalRows": 1234
  }
}
```

---

## 6. 차트 (Charts)

### 6.1. 차트 생성

> 권한: EDITOR 이상 (해당 페이지 소유자 또는 ADMIN)

```
POST /dashboards/:dashboardId/pages/:pageId/charts
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
  "datasourceId": "uuid",
  "config": {
    "dimensions": [
      { "fieldId": "brand", "label": "브랜드", "order": 1 }
    ],
    "metrics": [
      {
        "fieldId": "settlement_amount",
        "label": "결제금액",
        "aggregate": "SUM",
        "numberFormat": "#,##0",
        "order": 1
      }
    ],
    "defaultSort": { "fieldId": "settlement_amount", "direction": "DESC" },
    "rowsPerPage": 20,
    "showTotalsRow": true
  }
}
```

**Response `201`**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "pageId": "uuid",
    "type": "TABLE",
    "title": "쇼핑몰별 결제금액",
    "x": 0,
    "y": 0,
    "width": 800,
    "height": 400,
    "datasourceId": "uuid",
    "config": { ... },
    "style": { ... },
    "createdAt": "2026-02-28T09:00:00Z"
  }
}
```

**차트 타입별 `config` 주요 필드**

| 타입 | 주요 config 필드 |
|---|---|
| TABLE | dimensions, metrics, defaultSort, rowsPerPage, showTotalsRow, frozenColumns |
| PIVOT | rowDimension, colDimension, metrics, showSubtotals |
| LINE / BAR | xAxis (dimension), yAxis (metrics), legend, smooth |
| STACKED_BAR | xAxis, series (dimension), metrics |
| PIE | dimension, metric |
| SCORECARD | metric, comparisonMetric, comparisonLabel |

---

### 6.2. 차트 단건 조회

```
GET /dashboards/:dashboardId/pages/:pageId/charts/:chartId
```

**Response `200`** — 6.1 응답과 동일 구조

---

### 6.3. 차트 수정 (설정)

> 권한: 소유자 또는 ADMIN 이상

```
PATCH /dashboards/:dashboardId/pages/:pageId/charts/:chartId
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
PATCH /dashboards/:dashboardId/pages/:pageId/charts/:chartId/style
```

**Request Body**

```json
{
  "header": {
    "fontSize": 13,
    "fontWeight": "bold",
    "backgroundColor": "#f1f5f9",
    "textColor": "#1e293b",
    "wrapText": false
  },
  "body": {
    "fontSize": 13,
    "alternateRowColor": "#f8fafc",
    "borderColor": "#e2e8f0"
  },
  "totalsRow": {
    "backgroundColor": "#e2e8f0",
    "fontWeight": "bold"
  },
  "showBorder": true,
  "borderRadius": 4,
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
DELETE /dashboards/:dashboardId/pages/:pageId/charts/:chartId
```

**Response `204`**

---

### 6.6. 차트 복제

> 권한: EDITOR 이상

```
POST /dashboards/:dashboardId/pages/:pageId/charts/:chartId/duplicate
```

**Request Body** (선택적)

```json
{
  "targetPageId": "uuid",   // 다른 페이지로 복제 시 지정
  "offsetX": 20,
  "offsetY": 20
}
```

**Response `201`** — 새로 생성된 차트 전체 반환

---

### 6.7. 다중 차트 위치/크기 일괄 수정

드래그 후 일괄 저장에 사용됩니다.

> 권한: 소유자 또는 ADMIN 이상

```
PATCH /dashboards/:dashboardId/pages/:pageId/charts/positions
```

**Request Body**

```json
{
  "updates": [
    { "chartId": "uuid", "x": 0, "y": 0, "width": 800, "height": 400 },
    { "chartId": "uuid", "x": 820, "y": 0, "width": 400, "height": 400 }
  ]
}
```

**Response `200`**

```json
{
  "success": true,
  "data": { "updatedCount": 2 }
}
```

---

### 6.8. 차트 그룹 생성

여러 차트를 하나의 그룹으로 묶어 이동/크기 조정 연동.

> 권한: 소유자 또는 ADMIN 이상

```
POST /dashboards/:dashboardId/pages/:pageId/chart-groups
```

**Request Body**

```json
{
  "name": "브랜드 섹션",
  "chartIds": ["uuid1", "uuid2"]
}
```

**Response `201`**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "브랜드 섹션",
    "chartIds": ["uuid1", "uuid2"]
  }
}
```

---

### 6.9. 차트 데이터 조회

차트 렌더링을 위한 실제 데이터를 반환합니다.
필터 파라미터는 현재 페이지에 활성화된 필터 값들을 전달합니다.

```
POST /dashboards/:dashboardId/pages/:pageId/charts/:chartId/data
```

**Request Body**

```json
{
  "filters": [
    { "filterId": "uuid", "value": "2026-02-01" },
    { "filterId": "uuid", "value": ["닥터트루", "바른농장"] }
  ],
  "sort": { "fieldId": "settlement_amount", "direction": "DESC" },
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
      { "fieldId": "brand", "label": "브랜드", "type": "TEXT" },
      { "fieldId": "settlement_amount", "label": "결제금액", "type": "NUMBER", "aggregate": "SUM" }
    ],
    "rows": [
      ["닥터트루", 13681410],
      ["바른농장", 585780]
    ],
    "totals": [null, 39734385],
    "total": 5,
    "page": 1,
    "limit": 20,
    "queriedAt": "2026-02-28T09:01:23Z"
  }
}
```

---

### 6.10. 차트 데이터 내보내기

```
POST /dashboards/:dashboardId/pages/:pageId/charts/:chartId/export
```

**Request Body**

```json
{
  "format": "XLSX",      // XLSX | CSV
  "filters": [ ... ],
  "includeHeaders": true
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
POST /dashboards/:dashboardId/pages/:pageId/filters
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
  "datasourceId": "uuid",
  "fieldId": "order_date",
  "config": {
    "defaultValue": "LAST_7_DAYS",  // TODAY | YESTERDAY | LAST_7_DAYS | THIS_MONTH | CUSTOM
    "applyTo": "PAGE"               // PAGE | chart_id
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
    "datasourceId": "uuid",
    "fieldId": "order_date",
    "config": { ... },
    "createdAt": "2026-02-28T09:00:00Z"
  }
}
```

**필터 타입별 `config` 주요 필드**

| 타입 | config 필드 |
|---|---|
| DROPDOWN | `multiSelect: boolean`, `defaultValue: string[]`, `applyTo` |
| TEXT_INPUT | `operator: FilterOp`, `placeholder`, `applyTo` |
| RANGE | `operator: FilterOp`, `min, max`, `step`, `applyTo` |
| DATE_RANGE | `defaultValue`, `applyTo` |

---

### 7.2. 필터 수정

> 권한: 소유자 또는 ADMIN 이상

```
PATCH /dashboards/:dashboardId/pages/:pageId/filters/:filterId
```

**Request Body** (모든 필드 선택적) — 7.1 Request Body 참고

**Response `200`** — 수정된 필터 전체 반환

---

### 7.3. 필터 삭제

> 권한: 소유자 또는 ADMIN 이상

```
DELETE /dashboards/:dashboardId/pages/:pageId/filters/:filterId
```

**Response `204`**

---

### 7.4. 기본 필터 설정 (차트 또는 페이지에 고정 적용)

> 권한: 소유자 또는 ADMIN 이상

```
PUT /dashboards/:dashboardId/pages/:pageId/default-filters
```

**Request Body**

```json
{
  "applyTo": "PAGE",        // PAGE | chart_id
  "rules": [
    {
      "datasourceId": "uuid",
      "fieldId": "is_active",
      "operator": "EQ",
      "value": true
    },
    {
      "datasourceId": "uuid",
      "fieldId": "brand",
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
GET /dashboards/:dashboardId/pages/:pageId/charts/:chartId/conditional-formats
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "chartId": "uuid",
        "name": "ROI 색상 서식",
        "order": 1,
        "applyTo": "CELL",          // CELL | ROW
        "targetFields": ["roi"],
        "rules": [
          {
            "operator": "LT",
            "value": 0,
            "style": {
              "backgroundColor": "#fee2e2",
              "color": "#dc2626",
              "fontWeight": "bold"
            }
          },
          {
            "operator": "GTE",
            "value": 50,
            "style": {
              "backgroundColor": "#dcfce7",
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
POST /dashboards/:dashboardId/pages/:pageId/charts/:chartId/conditional-formats
```

**Request Body**

```json
{
  "name": "ROI 색상 서식",
  "applyTo": "CELL",           // CELL | ROW
  "targetFields": ["roi"],     // applyTo=ROW인 경우 조건 판단에 사용할 필드
  "rules": [
    {
      "operator": "LT",        // FilterOp 참고
      "value": 0,
      "secondValue": null,     // BETWEEN 연산자 사용 시 상한값
      "style": {
        "backgroundColor": "#fee2e2",
        "color": "#dc2626",
        "fontWeight": "normal",   // normal | bold
        "fontStyle": "normal",    // normal | italic
        "textDecoration": "none"  // none | underline | line-through
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
    "applyTo": "CELL",
    "targetFields": ["roi"],
    "rules": [ ... ],
    "createdAt": "2026-02-28T09:00:00Z"
  }
}
```

---

### 8.3. 조건부 서식 수정

> 권한: EDITOR 이상

```
PATCH /dashboards/:dashboardId/pages/:pageId/charts/:chartId/conditional-formats/:formatId
```

**Request Body** — 8.2 Request Body 참고 (모든 필드 선택적)

**Response `200`** — 수정된 서식 전체 반환

---

### 8.4. 조건부 서식 삭제

> 권한: EDITOR 이상

```
DELETE /dashboards/:dashboardId/pages/:pageId/charts/:chartId/conditional-formats/:formatId
```

**Response `204`**

---

### 8.5. 조건부 서식 순서 변경

서식은 위에서 아래로 순서대로 평가되며, 첫 번째 매칭 규칙이 적용됩니다.

> 권한: EDITOR 이상

```
PATCH /dashboards/:dashboardId/pages/:pageId/charts/:chartId/conditional-formats/reorder
```

**Request Body**

```json
{
  "orders": [
    { "formatId": "uuid", "order": 1 },
    { "formatId": "uuid", "order": 2 }
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
POST /dashboards/:dashboardId/pages/:pageId/charts/:chartId/conditional-formats/:formatId/copy
```

**Request Body**

```json
{
  "targetChartId": "uuid"
}
```

**Response `201`** — 새로 생성된 서식 전체 반환

---

## 9. 개인 뷰 설정 (User View Configs)

Viewer 포함 모든 사용자가 차트의 메트릭, 정렬 등을 개인적으로 오버라이드하여 저장합니다.
본인에게만 적용되며 원본 차트 설정에는 영향을 주지 않습니다.

### 9.1. 개인 뷰 저장/갱신

```
PUT /dashboards/:dashboardId/pages/:pageId/charts/:chartId/my-view
```

**Request Body** (모든 필드 선택적, 저장할 항목만 포함)

```json
{
  "metrics": ["settlement_amount", "margin", "roi"],
  "sort": { "fieldId": "settlement_amount", "direction": "DESC" },
  "columnWidths": { "brand": 120, "roi": 80 },
  "frozenColumns": ["brand"],
  "rowsPerPage": 50
}
```

**Response `200`**

```json
{
  "success": true,
  "data": {
    "chartId": "uuid",
    "config": { ... },
    "updatedAt": "2026-02-28T09:05:00Z"
  }
}
```

---

### 9.2. 개인 뷰 조회

```
GET /dashboards/:dashboardId/pages/:pageId/charts/:chartId/my-view
```

**Response `200`** — 9.1 응답과 동일 구조

---

### 9.3. 개인 뷰 초기화

```
DELETE /dashboards/:dashboardId/pages/:pageId/charts/:chartId/my-view
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
GET /notifications?isRead=false
```

**Query Parameters**

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `isRead` | boolean | 읽음 여부 필터 |

**Response `200`**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "type": "REGISTER_REQUEST",   // REGISTER_REQUEST | REGISTER_APPROVED | REGISTER_REJECTED
        "title": "새 회원가입 요청",
        "message": "홍길동(user@example.com) 님이 회원가입을 요청했습니다.",
        "linkUrl": "/admin/users/requests",
        "isRead": false,
        "createdAt": "2026-02-28T09:00:00Z"
      }
    ],
    "unreadCount": 3
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
  "notificationIds": ["uuid1", "uuid2"],
  "readAll": false    // true이면 notificationIds 무시하고 전체 읽음 처리
}
```

**Response `200`**

```json
{
  "success": true,
  "data": { "updatedCount": 2 }
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
    "useTls": true,
    "fromName": "LookFlex",
    "fromEmail": "noreply@example.com",
    "isConfigured": true
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
  "useTls": true,
  "fromName": "LookFlex",
  "fromEmail": "noreply@example.com"
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
  "toEmail": "test@example.com"
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
GET /admin/audit-logs?userId=uuid&action=DATA_QUERY&from=2026-02-01T00:00:00Z&to=2026-02-28T23:59:59Z&page=1&limit=50
```

**Query Parameters**

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `userId` | UUID | 특정 사용자 필터 |
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
        "userId": "uuid",
        "userName": "홍길동",
        "action": "DATA_QUERY",
        "detail": { "chartId": "uuid", "datasourceId": "uuid" },
        "ipAddress": "192.168.1.10",
        "createdAt": "2026-02-28T09:01:23Z"
      }
    ],
    "total": 200,
    "page": 1,
    "limit": 50,
    "totalPages": 4
  }
}
```

---

*총 API 엔드포인트: 약 60개*
*최종 업데이트: 2026-02-28*
