# LookFlex 테스트 가이드

로컬 개발 환경에서 백엔드 API를 검증하는 절차를 기록합니다.
현재 구현된 Auth API(10개 엔드포인트)를 전수 테스트합니다.

---

## 0. 사전 준비

필요한 도구:

- Docker Desktop (실행 중)
- `curl` (macOS 기본 포함)
- `jq` (응답 JSON 포맷팅용, 선택) — `brew install jq`
- `redis-cli` (OTP 직접 조회용, 선택) — `brew install redis`

---

## 1. 환경 시작 / 종료

### 컨테이너 시작 (postgres + redis + backend)

```bash
cd /Users/cuz/Documents/Github/lookflex

docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d postgres redis backend
```

> **주의:** frontend가 아직 없으므로 frontend/nginx 서비스는 제외합니다.  
> `make dev`는 현재 프론트 컨테이너를 같이 띄우므로 직접 compose 명령을 사용합니다.

### 상태 확인

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps
```

정상 상태:

```
NAME                STATUS
lookflex-postgres   Up X seconds (healthy)
lookflex-redis      Up X seconds (healthy)
lookflex-backend    Up X seconds
```

backend가 `Restarting` 상태라면 로그를 확인합니다:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs backend --tail 40
```

### 컨테이너 종료

```bash
# 컨테이너만 종료 (데이터 유지)
docker compose -f docker-compose.yml -f docker-compose.dev.yml down

# 볼륨까지 삭제 (DB 초기화)
docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v
```

---

## 2. 헬스체크

```bash
curl -s http://localhost:8000/api/v1/health | jq
```

기대 응답:

```json
{"status": "ok", "version": "0.1.0"}
```

Swagger UI: http://localhost:8000/api/docs

---

## 3. Auth API 전수 테스트

테스트는 순서대로 진행합니다. 각 단계의 응답값을 다음 단계에서 사용합니다.

### 3.1. 회원가입 요청

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "name": "Alice",
    "password": "TestPass1!",
    "requested_role": "EDITOR"
  }' | jq
```

기대 응답 (`201`):

```json
{
  "success": true,
  "data": {
    "message": "이메일 인증 코드가 발송되었습니다.",
    "email": "alice@example.com"
  },
  "error": null
}
```

오류 케이스:

| 재현 방법 | 기대 응답 |
|---|---|
| 동일 이메일로 `/register` 재호출 | `409 EMAIL_ALREADY_EXISTS` 또는 `REGISTER_REQUEST_PENDING` |

---

### 3.2. OTP 코드 확인

SMTP가 미설정된 개발 환경에서는 인증 코드가 컨테이너 로그에 출력됩니다.

**방법 A: 컨테이너 로그에서 추출**

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs backend \
  | grep "이메일 인증 코드" | tail -3
```

출력 예시:

```
lookflex-backend | [EMAIL - SMTP 미설정] to=alice@example.com | subject=[LookFlex] 이메일 인증 코드 | body=
    ...
    <h2 style="letter-spacing:6px">483921</h2>
    ...
```

HTML body 안에 6자리 숫자가 코드입니다.

**방법 B: redis-cli로 직접 조회** (더 간편)

```bash
# redis-cli를 컨테이너 안에서 실행
docker exec -it lookflex-redis redis-cli -a devredis123

# 또는 로컬 redis-cli 사용
redis-cli -p 6379 -a devredis123

# Redis 키 확인
GET otp:alice@example.com
```

반환값이 6자리 코드입니다. TTL 확인:

```bash
TTL otp:alice@example.com
# → 남은 초 (최대 600, 10분)
```

---

### 3.3. 이메일 인증

위에서 얻은 코드를 사용합니다.

```bash
CODE=483921  # 실제 코드로 교체

curl -s -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"alice@example.com\",
    \"code\": \"$CODE\"
  }" | jq
```

기대 응답 (`200`):

```json
{
  "success": true,
  "data": {
    "message": "이메일 인증이 완료되었습니다. 관리자 승인을 기다려주세요."
  },
  "error": null
}
```

오류 케이스:

| 재현 방법 | 기대 응답 |
|---|---|
| 코드 잘못 입력 | `400 INVALID_CODE` |
| 코드 만료 후 (10분 경과 또는 Redis에서 직접 삭제) | `400 CODE_EXPIRED` |

---

### 3.4. 인증 코드 재발송

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/resend-code \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com"}' | jq
```

기대 응답 (`200`): `"인증 코드가 재발송되었습니다."`

---

### 3.5. 초기 OWNER 계정 생성 (DB 직접 삽입)

가입 승인 테스트를 위해 ADMIN/OWNER 계정이 필요합니다.
첫 번째 관리자는 닭-달걀 문제로 DB에 직접 삽입합니다.

```bash
# postgres 컨테이너에 접속
docker exec -it lookflex-postgres psql -U lookflex -d lookflex
```

```sql
-- bcrypt 해시: "AdminPass1!" (rounds=12)
-- 아래 해시는 고정값 — 실제 사용 전 반드시 교체하세요
INSERT INTO users (id, email, name, hashed_password, role, is_active, email_verified_at, joined_at, updated_at)
VALUES (
  gen_random_uuid(),
  'admin@example.com',
  'Admin',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQyCCpSHjzDGDanG8P3ZJYVcm',
  'OWNER',
  true,
  now(),
  now(),
  now()
);

-- 삽입 확인
SELECT id, email, role, is_active FROM users;
\q
```

> 비밀번호 해시를 직접 생성하려면:
> ```bash
> docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm --no-deps backend \
>   python -c "from app.core.security import hash_password; print(hash_password('AdminPass1!'))"
> ```

---

### 3.6. 로그인

```bash
# OWNER 계정으로 로그인 (쿠키를 파일에 저장)
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -c /tmp/lookflex_cookies.txt \
  -d '{
    "email": "admin@example.com",
    "password": "AdminPass1!"
  }' | jq
```

기대 응답 (`200`):

```json
{
  "success": true,
  "data": {
    "accessToken": "eyJ...",
    "tokenType": "Bearer",
    "expiresIn": 900
  },
  "error": null
}
```

Access Token을 변수로 저장:

```bash
ACCESS_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -c /tmp/lookflex_cookies.txt \
  -d '{"email":"admin@example.com","password":"AdminPass1!"}' \
  | jq -r '.data.accessToken')

echo $ACCESS_TOKEN
```

오류 케이스:

| 재현 방법 | 기대 응답 |
|---|---|
| 잘못된 비밀번호 | `401 INVALID_CREDENTIALS` |
| 이메일 미인증 계정으로 로그인 | `403 EMAIL_NOT_VERIFIED` |
| 승인 대기 중 계정 | `403 APPROVAL_PENDING` |

---

### 3.7. 회원가입 요청 목록 조회 (ADMIN 전용)

```bash
curl -s http://localhost:8000/api/v1/auth/register-requests \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
```

기대 응답 (`200`): alice의 PENDING 요청이 목록에 포함됩니다.

```bash
# 상태별 필터
curl -s "http://localhost:8000/api/v1/auth/register-requests?status=PENDING" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq

# 요청 ID 추출
REQUEST_ID=$(curl -s "http://localhost:8000/api/v1/auth/register-requests?status=PENDING" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  | jq -r '.data.items[0].id')

echo $REQUEST_ID
```

---

### 3.8. 회원가입 요청 승인 / 거절

```bash
# 승인
curl -s -X PATCH http://localhost:8000/api/v1/auth/register-requests/$REQUEST_ID \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "approve"}' | jq

# 거절
curl -s -X PATCH http://localhost:8000/api/v1/auth/register-requests/$REQUEST_ID \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "reject", "reject_reason": "테스트 거절"}' | jq
```

승인 시 기대 응답 (`200`):

```json
{
  "success": true,
  "data": {
    "message": "승인되었습니다.",
    "user_id": "uuid"
  },
  "error": null
}
```

승인 후 users 테이블에 alice가 생성됐는지 확인:

```bash
docker exec -it lookflex-postgres psql -U lookflex -d lookflex \
  -c "SELECT id, email, role, is_active FROM users;"
```

---

### 3.9. alice로 로그인

3.8 승인 후 alice 계정으로 로그인합니다.

```bash
ALICE_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -c /tmp/alice_cookies.txt \
  -d '{"email":"alice@example.com","password":"TestPass1!"}' \
  | jq -r '.data.accessToken')

echo $ALICE_TOKEN
```

---

### 3.10. 토큰 갱신

로그인 시 저장된 쿠키를 사용합니다.

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/refresh \
  -b /tmp/lookflex_cookies.txt | jq
```

기대 응답 (`200`): 새 `accessToken` 반환.

---

### 3.11. 비밀번호 재설정 요청

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/password-reset-request \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com"}' | jq
```

재설정 링크는 컨테이너 로그 또는 Redis에서 확인:

```bash
# 로그에서 확인
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs backend \
  | grep "비밀번호 재설정"

# Redis에서 토큰 목록 확인 (키 패턴 검색)
docker exec -it lookflex-redis redis-cli -a devredis123 KEYS "pw_reset:*"
```

---

### 3.12. 비밀번호 재설정

로그에서 URL의 `token=` 파라미터 값을 추출합니다 (예: `abc123def456...`).

```bash
RESET_TOKEN=<로그에서_추출한_토큰>

curl -s -X POST http://localhost:8000/api/v1/auth/password-reset \
  -H "Content-Type: application/json" \
  -d "{
    \"token\": \"$RESET_TOKEN\",
    \"new_password\": \"NewPass1!\"
  }" | jq
```

기대 응답 (`200`): `"비밀번호가 변경되었습니다."`

---

### 3.13. 로그아웃

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/logout \
  -b /tmp/lookflex_cookies.txt
# → HTTP 204, 빈 응답
```

로그아웃 후 토큰 갱신 시도가 실패하는지 확인:

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/refresh \
  -b /tmp/lookflex_cookies.txt | jq
# → 401 UNAUTHORIZED
```

---

## 4. 권한 테스트

### 4.1. 인증 없이 보호된 엔드포인트 호출

```bash
curl -s http://localhost:8000/api/v1/auth/register-requests | jq
# → 401
```

### 4.2. VIEWER 계정으로 ADMIN 전용 엔드포인트 호출

alice(EDITOR)가 register-requests에 접근:

```bash
curl -s http://localhost:8000/api/v1/auth/register-requests \
  -H "Authorization: Bearer $ALICE_TOKEN" | jq
# → 403
```

---

## 5. DB 상태 직접 확인

```bash
# 모든 테이블 목록 확인 (22개)
docker exec -it lookflex-postgres psql -U lookflex -d lookflex -c "\dt"

# users 목록
docker exec -it lookflex-postgres psql -U lookflex -d lookflex \
  -c "SELECT id, email, role, is_active FROM users;"

# register_requests 목록
docker exec -it lookflex-postgres psql -U lookflex -d lookflex \
  -c "SELECT id, email, status FROM register_requests;"

# Alembic 마이그레이션 히스토리
docker exec -it lookflex-postgres psql -U lookflex -d lookflex \
  -c "SELECT * FROM alembic_version;"
```

---

## 6. Redis 상태 확인

```bash
docker exec -it lookflex-redis redis-cli -a devredis123

# 전체 키 목록
KEYS *

# OTP 조회
GET otp:alice@example.com

# OTP 남은 TTL (초)
TTL otp:alice@example.com

# 비밀번호 재설정 토큰
KEYS pw_reset:*

# 종료
quit
```

---

## 7. 로그 모니터링

```bash
# 실시간 로그
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f backend

# 에러만 필터
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs backend \
  | grep -i "error\|exception\|traceback"

# HTTP 요청 로그만
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs backend \
  | grep "HTTP/1.1"
```

---

## 8. 재빌드가 필요한 경우

`pyproject.toml` 의존성 변경 시 이미지를 다시 빌드해야 합니다:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build postgres redis backend
```

`alembic/versions/` 마이그레이션 파일만 변경 시 볼륨 마운트로 자동 반영됩니다 (재빌드 불필요).
