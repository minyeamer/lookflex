# Users API 테스트 가이드

Users API (§2, 9개 엔드포인트)를 전수 테스트합니다.

---

## 사전 준비

- Docker 컨테이너 실행 중 (postgres, redis, backend)
- admin@example.com (OWNER) 계정 존재
- alice@example.com (EDITOR) 계정 존재 (01-auth 테스트에서 생성)

---

## 1. 토큰 준비

```bash
# OWNER 토큰
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"AdminPass1!"}' \
  | jq -r '.data.access_token')

# EDITOR 토큰 (alice)
ALICE_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"TestPass1!"}' \
  | jq -r '.data.access_token')

echo "ADMIN_TOKEN: $ADMIN_TOKEN"
echo "ALICE_TOKEN: $ALICE_TOKEN"
```

---

## 2. 내 프로필 조회 (GET /users/me)

```bash
# alice 계정으로 조회
curl -s http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $ALICE_TOKEN" | jq
```

기대 응답 (`200`):

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "alice@example.com",
    "name": "Alice",
    "profile_image_url": null,
    "role": "EDITOR",
    "groups": [],
    "joined_at": "2026-03-01T..."
  },
  "error": null
}
```

---

## 3. 내 프로필 수정 (PATCH /users/me)

```bash
# alice가 이름 변경
curl -s -X PATCH http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Kim"}' | jq

# 프로필 이미지 URL 추가
curl -s -X PATCH http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"profile_image_url": "https://example.com/avatar.jpg"}' | jq
```

기대 응답 (`200`): 변경된 프로필 전체 반환.

---

## 4. 프로필 이미지 업로드 (POST /users/me/profile-image)

```bash
# 임시 이미지 파일 생성 (테스트용)
echo "fake image data" > /tmp/test_avatar.jpg

# 업로드
curl -s -X POST http://localhost:8000/api/v1/users/me/profile-image \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -F "file=@/tmp/test_avatar.jpg" | jq
```

기대 응답 (`200`):

```json
{
  "success": true,
  "data": {
    "url": "https://storage.example.com/profiles/uuid/test_avatar.jpg"
  },
  "error": null
}
```

> **참고:** 현재 구현은 실제 파일 저장 없이 임시 URL만 반환합니다. (S3 연동 필요)

---

## 5. 내 비밀번호 변경 (PATCH /users/me/password)

```bash
# alice 비밀번호 변경TestPass1! → NewPass1!
curl -s -X PATCH http://localhost:8000/api/v1/users/me/password \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "TestPass1!",
    "new_password": "NewPass1!"
  }' | jq

# 새 비밀번호로 로그인 확인
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"NewPass1!"}' | jq

# 다시 원래 비밀번호로 변경 (이후 테스트 일관성)
ALICE_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"NewPass1!"}' \
  | jq -r '.data.access_token')

curl -s -X PATCH http://localhost:8000/api/v1/users/me/password \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "NewPass1!",
    "new_password": "TestPass1!"
  }' | jq
```

오류 케이스:

```bash
# 현재 비밀번호 불일치
curl -s -X PATCH http://localhost:8000/api/v1/users/me/password \
  -H "Authorization: Bearer $ALICE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "WrongPass!",
    "new_password": "NewPass1!"
  }' | jq
# → 400 INVALID_PASSWORD
```

---

## 6. 사용자 목록 조회 (GET /users) — ADMIN 전용

```bash
# 전체 목록 (admin 토큰 사용)
curl -s "http://localhost:8000/api/v1/users?page=1&limit=20" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

# 이름 검색 (Alice)
curl -s "http://localhost:8000/api/v1/users?search=Alice" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq

# 역할 필터 (EDITOR)
curl -s "http://localhost:8000/api/v1/users?role=EDITOR" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq
```

기대 응답 (`200`):

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "email": "alice@example.com",
        "name": "Alice Kim",
        "profile_image_url": "...",
        "role": "EDITOR",
        "groups": [],
        "is_active": true,
        "joined_at": "2026-03-01T..."
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 2
  },
  "error": null
}
```

권한 테스트:

```bash
# alice(EDITOR)가 사용자 목록 조회 시도
curl -s "http://localhost:8000/api/v1/users" \
  -H "Authorization: Bearer $ALICE_TOKEN" | jq
# → 403 FORBIDDEN
```

---

## 7. 사용자 단건 조회 (GET /users/:user_id) — ADMIN 전용

```bash
# alice의 user_id 추출
ALICE_ID=$(curl -s "http://localhost:8000/api/v1/users?search=alice" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq -r '.data.items[0].id')

echo $ALICE_ID

# alice 상세 조회
curl -s "http://localhost:8000/api/v1/users/$ALICE_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq
```

기대 응답 (`200`): UserProfile 구조 (2.1과 동일).

오류 케이스:

```bash
# 존재하지 않는 user_id
curl -s "http://localhost:8000/api/v1/users/00000000-0000-0000-0000-000000000000" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq
# → 404 USER_NOT_FOUND
```

---

## 8. 테스트 사용자 추가 생성

다중 역할/그룹 수정 테스트를 위해 추가 사용자를 생성합니다.

```bash
# bob@example.com 회원가입 (간략 버전 — send-verification → verify-email → register)
curl -s -X POST http://localhost:8000/api/v1/auth/send-verification \
  -H "Content-Type: application/json" \
  -d '{"email":"bob@example.com"}' | jq

# Redis에서 OTP 조회
BOB_CODE=$(docker exec -it flooks-redis redis-cli -a devredis123 --no-auth-warning GET "otp:bob@example.com" | tr -d '\r')
echo "Bob OTP: $BOB_CODE"

# 이메일 인증
curl -s -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"bob@example.com\",\"code\":\"$BOB_CODE\"}" | jq

# 회원가입
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"bob@example.com",
    "name":"Bob",
    "password":"BobPass1!",
    "requested_role":"VIEWER"
  }' | jq

# 승인 요청 ID 추출
BOB_REQUEST_ID=$(curl -s "http://localhost:8000/api/v1/auth/register-requests?status=PENDING" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq -r '.data.items[] | select(.email=="bob@example.com") | .id')

echo "Bob Request ID: $BOB_REQUEST_ID"

# 승인 (VIEWER 역할)
curl -s -X PATCH "http://localhost:8000/api/v1/auth/register-requests/$BOB_REQUEST_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"APPROVED","assigned_role":"VIEWER"}' | jq

# Bob ID 추출
BOB_ID=$(curl -s "http://localhost:8000/api/v1/users?search=bob" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq -r '.data.items[0].id')

echo "Bob ID: $BOB_ID"
```

---

## 9. 다중 사용자 역할 수정 (PATCH /users/roles) — ADMIN 전용

```bash
# Alice(EDITOR) → VIEWER, Bob(VIEWER) → EDITOR로 변경
curl -s -X PATCH http://localhost:8000/api/v1/users/roles \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"updates\": [
      {\"user_id\": \"$ALICE_ID\", \"role\": \"VIEWER\"},
      {\"user_id\": \"$BOB_ID\", \"role\": \"EDITOR\"}
    ]
  }" | jq
```

기대 응답 (`200`):

```json
{
  "success": true,
  "data": {
    "success_count": 2,
    "failed": null
  },
  "error": null
}
```

검증:

```bash
# Alice 역할 확인 (VIEWER로 변경됨)
curl -s "http://localhost:8000/api/v1/users/$ALICE_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq '.data.role'

# Bob 역할 확인 (EDITOR로 변경됨)
curl -s "http://localhost:8000/api/v1/users/$BOB_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq '.data.role'
```

오류 케이스:

```bash
# OWNER 역할 부여 시도
curl -s -X PATCH http://localhost:8000/api/v1/users/roles \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"updates\": [{\"user_id\": \"$ALICE_ID\", \"role\": \"OWNER\"}]
  }" | jq
# → 422 Validation Error (스키마 validator에서 차단)

# admin 본인 역할 변경 시도
ADMIN_ID=$(curl -s "http://localhost:8000/api/v1/users?search=admin" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq -r '.data.items[0].id')

curl -s -X PATCH http://localhost:8000/api/v1/users/roles \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"updates\": [{\"user_id\": \"$ADMIN_ID\", \"role\": \"VIEWER\"}]
  }" | jq
# → 200 성공하지만 failed 배열에 "본인의 역할은 변경할 수 없습니다." 포함
```

---

## 10. 다중 사용자 그룹/프로필 수정 (PATCH /users/profiles) — ADMIN 전용

```bash
# alice 이름 변경, bob 이름 + 프로필 이미지 변경
curl -s -X PATCH http://localhost:8000/api/v1/users/profiles \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"updates\": [
      {
        \"user_id\": \"$ALICE_ID\",
        \"name\": \"Alice Park\"
      },
      {
        \"user_id\": \"$BOB_ID\",
        \"name\": \"Bob Lee\",
        \"profile_image_url\": \"https://example.com/bob.jpg\"
      }
    ]
  }" | jq
```

기대 응답 (`200`):

```json
{
  "success": true,
  "data": {
    "success_count": 2,
    "failed": null
  },
  "error": null
}
```

검증:

```bash
curl -s "http://localhost:8000/api/v1/users/$ALICE_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq '.data.name'
# → "Alice Park"

curl -s "http://localhost:8000/api/v1/users/$BOB_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq '.data | {name, profile_image_url}'
# → {"name": "Bob Lee", "profile_image_url": "https://example.com/bob.jpg"}
```

---

## 11. 사용자 비활성화 (DELETE /users/:user_id) — ADMIN 전용

```bash
# bob 비활성화
curl -s -X DELETE "http://localhost:8000/api/v1/users/$BOB_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
# → HTTP 204 (응답 본문 없음)

# 비활성화 확인
curl -s "http://localhost:8000/api/v1/users/$BOB_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  | jq '.data.is_active'
# → false
```

오류 케이스:

```bash
# OWNER 계정 비활성화 시도
curl -s -X DELETE "http://localhost:8000/api/v1/users/$ADMIN_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq
# → 403 CANNOT_DEACTIVATE_OWNER

# alice가 bob 비활성화 시도 (alice는 VIEWER)
curl -s -X DELETE "http://localhost:8000/api/v1/users/$BOB_ID" \
  -H "Authorization: Bearer $ALICE_TOKEN" | jq
# → 403 FORBIDDEN
```

---

## 12. DB 직접 확인

```bash
# 사용자 목록 (is_active 포함)
docker exec -it flooks-postgres psql -U flooks_user -d flooks \
  -c "SELECT id, email, name, role, is_active FROM users ORDER BY joined_at;"

# bob이 비활성화 상태인지 확인
docker exec -it flooks-postgres psql -U flooks_user -d flooks \
  -c "SELECT email, is_active FROM users WHERE email='bob@example.com';"
```

---

## 13. 복원 (테스트 후 정리)

```bash
# alice 역할 복원 (VIEWER → EDITOR)
curl -s -X PATCH http://localhost:8000/api/v1/users/roles \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"updates\":[{\"user_id\":\"$ALICE_ID\",\"role\":\"EDITOR\"}]}" | jq

# bob 활성화 (DB 직접 수정)
docker exec -it flooks-postgres psql -U flooks_user -d flooks \
  -c "UPDATE users SET is_active=true WHERE email='bob@example.com';"
```

---

## 요약

| 엔드포인트 | 메서드 | 권한 | 테스트 결과 |
|---|---|---|---|
| `/users/me` | GET | All | ✅ |
| `/users/me` | PATCH | All | ✅ |
| `/users/me/profile-image` | POST | All | ✅ (파일 저장 로직은 미구현) |
| `/users/me/password` | PATCH | All | ✅ |
| `/users` | GET | ADMIN | ✅ |
| `/users/:user_id` | GET | ADMIN | ✅ |
| `/users/roles` | PATCH | ADMIN | ✅ |
| `/users/profiles` | PATCH | ADMIN | ✅ |
| `/users/:user_id` | DELETE | ADMIN | ✅ |

**총 9개 엔드포인트 전수 테스트 완료.**
