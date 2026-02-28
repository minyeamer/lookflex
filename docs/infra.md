# LookFlex 아키텍처 & 프로젝트 구조

---

## 목차

1. [모노레포 전략](#1-모노레포-전략)
2. [Docker Compose vs Kubernetes 선택 근거](#2-docker-compose-vs-kubernetes-선택-근거)
3. [전체 폴더 구조](#3-전체-폴더-구조)
4. [서비스별 Docker 이미지 설계](#4-서비스별-docker-이미지-설계)
5. [Docker Compose 서비스 구성](#5-docker-compose-서비스-구성)
6. [데이터베이스 초기화 및 마이그레이션 전략](#6-데이터베이스-초기화-및-마이그레이션-전략)
7. [Redis 역할 및 구성](#7-redis-역할-및-구성)
8. [네트워크 및 볼륨 설계](#8-네트워크-및-볼륨-설계)
9. [환경 변수 관리](#9-환경-변수-관리)
10. [개발 vs 운영 환경 분리](#10-개발-vs-운영-환경-분리)
11. [Git 브랜치 전략](#11-git-브랜치-전략)

---

## 1. 모노레포 전략

하나의 Git 저장소에 프론트엔드·백엔드·인프라 설정을 모두 관리합니다.

**선택 이유**

- 소규모 팀(1명~수명)에서 여러 레포를 관리하는 오버헤드 제거
- 프론트·백엔드 동시 변경 시 하나의 PR/커밋으로 추적 가능
- Docker Compose, Nginx, 환경변수 등 인프라 설정이 코드와 함께 버전 관리됨
- `docs/` 폴더에서 API 명세, 인프라 설계, 의사결정 로그 등 문서를 일괄 관리

**패키지 매니저 통합은 하지 않습니다.** (Turborepo, Nx 등 미사용)
프론트엔드는 `npm`, 백엔드는 `pip`로 독립적으로 관리하며,
각 앱은 자신의 `Dockerfile`로 완전히 독립된 이미지를 빌드합니다.

---

## 2. Docker Compose vs Kubernetes 선택 근거

### 현재 단계: Docker Compose 채택

| 항목 | Docker Compose | Minikube / K8s |
|---|---|---|
| 학습 비용 | 낮음 (YAML 1개) | 높음 (kubectl, helm, manifest 다수) |
| 로컬 서버 리소스 | 가벼움 | Minikube 자체가 VM을 띄워 메모리 1~2GB 추가 소모 |
| 100명 미만 서비스 | 충분 | 오버엔지니어링 |
| 배포 방법 | `docker compose up -d` | `kubectl apply -f ...` |
| 서비스 간 통신 | 내부 DNS 자동 (서비스명으로 접근) | Service/ClusterIP 설정 필요 |
| 롤링 업데이트 | 기본 미지원 (다운타임 수초) | 기본 지원 |
| 자동 재시작 | `restart: unless-stopped` | 기본 지원 |

### Kubernetes로 이전을 고려할 시점

아래 조건 중 하나라도 해당되면 K8s 마이그레이션을 검토합니다.

- SaaS로 전환하여 멀티테넌트 및 동시 사용자 수백 명 이상
- 무중단 배포(zero-downtime)가 비즈니스 요건이 되는 시점
- 여러 대의 서버(노드)에 수평 확장이 필요한 시점

Docker Compose 기반으로 잘 작성된 `docker-compose.yml`은 K8s 마이그레이션 시 `kompose convert` 명령으로 K8s manifest로 자동 변환이 가능하므로, 지금의 설계가 나중을 막지 않습니다.

---

## 3. 전체 폴더 구조

```
lookflex/
│
├── apps/
│   ├── backend/                        # FastAPI 백엔드
│   │   ├── app/
│   │   │   ├── api/                    # 라우터 (도메인별 파일)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── users.py
│   │   │   │   ├── groups.py
│   │   │   │   ├── dashboards.py
│   │   │   │   ├── pages.py
│   │   │   │   ├── charts.py
│   │   │   │   ├── datasources.py
│   │   │   │   ├── filters.py
│   │   │   │   ├── conditional_formats.py
│   │   │   │   ├── notifications.py
│   │   │   │   └── admin.py
│   │   │   ├── core/
│   │   │   │   ├── config.py           # 환경변수 설정 (Pydantic BaseSettings)
│   │   │   │   ├── security.py         # JWT, bcrypt
│   │   │   │   ├── dependencies.py     # 공통 FastAPI Depends (현재 사용자, 권한 등)
│   │   │   │   └── exceptions.py       # 커스텀 예외 및 핸들러
│   │   │   ├── db/
│   │   │   │   ├── base.py             # SQLAlchemy Base
│   │   │   │   ├── session.py          # AsyncSession 팩토리
│   │   │   │   └── models/             # SQLAlchemy 모델 (도메인별 파일)
│   │   │   │       ├── __init__.py     # 모든 모델 import (Alembic이 감지할 수 있도록)
│   │   │   │       ├── user.py
│   │   │   │       ├── group.py
│   │   │   │       ├── dashboard.py
│   │   │   │       ├── page.py
│   │   │   │       ├── chart.py
│   │   │   │       ├── datasource.py
│   │   │   │       ├── filter.py
│   │   │   │       ├── conditional_format.py
│   │   │   │       ├── notification.py
│   │   │   │       └── audit_log.py
│   │   │   ├── schemas/                # Pydantic 요청/응답 스키마 (도메인별)
│   │   │   │   ├── auth.py
│   │   │   │   ├── user.py
│   │   │   │   └── ...
│   │   │   ├── services/               # 비즈니스 로직 (DB에 직접 접근하지 않음)
│   │   │   │   ├── auth_service.py
│   │   │   │   ├── user_service.py
│   │   │   │   ├── datasource_service.py
│   │   │   │   ├── query_service.py    # 외부 DB 쿼리 실행 (BigQuery, PG 등)
│   │   │   │   ├── export_service.py   # XLSX/CSV 내보내기
│   │   │   │   ├── email_service.py    # SMTP 이메일 발송
│   │   │   │   └── cache_service.py    # Redis 캐시 추상화
│   │   │   ├── repositories/           # DB CRUD 추상화 (service ↔ model 사이)
│   │   │   │   ├── user_repo.py
│   │   │   │   └── ...
│   │   │   └── main.py                 # FastAPI 앱 진입점, 라우터 등록
│   │   ├── alembic/                    # DB 마이그레이션
│   │   │   ├── env.py
│   │   │   ├── script.py.mako
│   │   │   └── versions/               # 마이그레이션 파일 (자동 생성)
│   │   │       └── 0001_initial.py
│   │   ├── tests/
│   │   │   ├── conftest.py
│   │   │   ├── test_auth.py
│   │   │   └── ...
│   │   ├── alembic.ini
│   │   ├── Dockerfile
│   │   ├── Dockerfile.dev              # 개발용 (hot-reload)
│   │   ├── pyproject.toml              # 의존성 및 프로젝트 메타데이터
│   │   └── .env.example
│   │
│   └── frontend/                       # Next.js 프론트엔드
│       ├── app/                        # App Router
│       │   ├── (auth)/
│       │   │   ├── login/
│       │   │   └── register/
│       │   ├── (dashboard)/
│       │   │   ├── layout.tsx
│       │   │   ├── page.tsx            # 대시보드 목록
│       │   │   └── [dashboardId]/
│       │   │       └── [pageId]/
│       │   ├── admin/
│       │   └── layout.tsx
│       ├── components/
│       │   ├── table/                  # TanStack Table 기반 컴포넌트
│       │   ├── chart/                  # ECharts 래퍼
│       │   ├── filter/                 # 필터 UI 컴포넌트
│       │   ├── conditional-format/     # 조건부 서식 편집기
│       │   └── ui/                     # shadcn/ui 공통 컴포넌트
│       ├── lib/
│       │   ├── api/                    # API 클라이언트 (fetch 래퍼, 각 도메인별)
│       │   ├── store/                  # Zustand 스토어
│       │   └── utils/                  # 유틸리티 함수
│       ├── types/                      # TypeScript 공통 타입 정의
│       ├── public/
│       ├── Dockerfile
│       ├── Dockerfile.dev
│       ├── next.config.ts
│       ├── tailwind.config.ts
│       ├── tsconfig.json
│       ├── package.json
│       └── .env.example
│
├── infra/
│   ├── nginx/
│   │   ├── nginx.conf                  # 로컬/운영 공통 베이스 설정
│   │   ├── conf.d/
│   │   │   ├── local.conf              # 로컬 HTTP 설정
│   │   │   └── prod.conf               # 운영 HTTPS 설정 (certbot 인증서 경로 포함)
│   │   └── Dockerfile                  # nginx 이미지 (conf 포함하여 빌드)
│   │
│   ├── postgres/
│   │   ├── init/                       # 컨테이너 최초 실행 시 자동 실행되는 SQL
│   │   │   └── 00_create_extensions.sql  # uuid-ossp, pgcrypto 등 확장 활성화
│   │   └── postgresql.conf             # 커스텀 PostgreSQL 설정 (선택)
│   │
│   └── redis/
│       └── redis.conf                  # Redis 설정 (비밀번호, 메모리 정책 등)
│
├── docs/                               # 프로젝트 문서 모음
│   ├── api.md                          # REST API 명세
│   ├── api-plan.md                     # API 기획 초안 (참고용)
│   ├── infra.md                        # 인프라 & 개발 운영 설계
│   └── chat.log                        # 주요 기술 의사결정 로그
├── docker-compose.yml                  # 운영 공통 기반 (이미지 지정)
├── docker-compose.dev.yml              # 로컬 개발 오버라이드 (볼륨 마운트, hot-reload)
├── docker-compose.prod.yml             # 운영 오버라이드 (리소스 제한, 로깅 등)
├── .env.example                        # 루트 환경변수 예시 (docker-compose가 읽음)
├── .env                                # 실제 환경변수 (gitignore)
├── .gitignore
├── LICENSE
└── README.md                           # 루트 유지 (GitHub 컨벤션)
```

---

## 4. 서비스별 Docker 이미지 설계

### 4-1. Backend (FastAPI)

```dockerfile
# apps/backend/Dockerfile  (운영용 — 멀티스테이지)

FROM python:3.11-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

FROM base AS builder
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install --no-cache-dir .

FROM base AS runner
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin
COPY ./app ./app
COPY alembic.ini ./
COPY alembic ./alembic
# 운영 서버는 uvicorn 단독이 아닌 gunicorn + uvicorn workers 사용
CMD ["gunicorn", "app.main:app", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

```dockerfile
# apps/backend/Dockerfile.dev  (개발용 — hot-reload)

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install --no-cache-dir -e ".[dev]"
# 소스는 볼륨으로 마운트하므로 COPY 생략
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### 4-2. Frontend (Next.js)

```dockerfile
# apps/frontend/Dockerfile  (운영용 — standalone 빌드)

FROM node:20-alpine AS base

FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
```

```dockerfile
# apps/frontend/Dockerfile.dev  (개발용 — hot-reload)

FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
# 소스는 볼륨으로 마운트
EXPOSE 3000
CMD ["npm", "run", "dev"]
```

> **참고:** Next.js `standalone` 빌드를 사용하면 `node_modules` 없이 최소한의 파일만으로 실행 가능한 이미지를 만들 수 있습니다. `next.config.ts`에 `output: 'standalone'`을 설정해야 합니다.

### 4-3. Nginx

```dockerfile
# infra/nginx/Dockerfile

FROM nginx:1.27-alpine
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/
```

---

## 5. Docker Compose 서비스 구성

### 5-1. 기반 파일: `docker-compose.yml`

```yaml
# docker-compose.yml  —  서비스 정의 기반 (직접 실행하지 않음)

services:
  # ── 데이터베이스 ──────────────────────────────────────
  postgres:
    image: postgres:16-alpine
    container_name: lookflex-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infra/postgres/init:/docker-entrypoint-initdb.d:ro
      #  ↑ 이 폴더의 .sql, .sh 파일은 DB 최초 생성 시 알파벳 순으로 자동 실행됩니다.
      #    Alembic 마이그레이션과 역할이 다릅니다 (아래 6장 참고).
    networks:
      - internal
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── 캐시 ────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    container_name: lookflex-redis
    command: redis-server /usr/local/etc/redis/redis.conf
    volumes:
      - redis_data:/data
      - ./infra/redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
    networks:
      - internal
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ── 백엔드 ────────────────────────────────────────────
  backend:
    container_name: lookflex-backend
    build:
      context: ./apps/backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379/0
      SECRET_KEY: ${SECRET_KEY}
      SMTP_HOST: ${SMTP_HOST}
      SMTP_PORT: ${SMTP_PORT}
      SMTP_USER: ${SMTP_USER}
      SMTP_PASSWORD: ${SMTP_PASSWORD}
    networks:
      - internal
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  # ── 프론트엔드 ───────────────────────────────────────
  frontend:
    container_name: lookflex-frontend
    build:
      context: ./apps/frontend
      dockerfile: Dockerfile
    environment:
      NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL}
    networks:
      - internal
    depends_on:
      - backend
    restart: unless-stopped

  # ── 리버스 프록시 ─────────────────────────────────────
  nginx:
    container_name: lookflex-nginx
    build:
      context: ./infra/nginx
    ports:
      - "80:80"
    networks:
      - internal
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:

networks:
  internal:
    driver: bridge
```

### 5-2. 개발 오버라이드: `docker-compose.dev.yml`

```yaml
# 실행 방법: docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

services:
  postgres:
    ports:
      - "5432:5432"          # 로컬에서 DBeaver 등으로 직접 접근 가능

  redis:
    ports:
      - "6379:6379"          # 로컬에서 Redis CLI 직접 접근 가능

  backend:
    build:
      dockerfile: Dockerfile.dev
    volumes:
      - ./apps/backend:/app  # 소스 마운트 → 코드 변경 시 자동 재시작
    ports:
      - "8000:8000"          # FastAPI /docs 직접 접근 가능

  frontend:
    build:
      dockerfile: Dockerfile.dev
    volumes:
      - ./apps/frontend:/app
      - /app/node_modules    # node_modules는 컨테이너 것을 사용 (덮어쓰기 방지)
    ports:
      - "3000:3000"          # Next.js dev server 직접 접근 가능
    environment:
      WATCHPACK_POLLING: "true"  # macOS 파일시스템 이벤트 대응
```

### 5-3. 운영 오버라이드: `docker-compose.prod.yml`

```yaml
# 실행 방법: docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

services:
  nginx:
    ports:
      - "80:80"
      - "443:443"            # HTTPS
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt:ro   # certbot 인증서
      - /var/www/certbot:/var/www/certbot:ro

  backend:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  postgres:
    deploy:
      resources:
        limits:
          memory: 512M
```

### 5-4. 서비스 간 통신 구조

```
브라우저
  │ HTTP :80 / HTTPS :443
  ▼
[nginx]  (내부 네트워크: internal)
  ├── /api/*   → http://backend:8000
  └── /*       → http://frontend:3000

[backend]
  ├── postgresql+asyncpg://postgres:5432
  └── redis://redis:6379

외부 (백엔드에서 아웃바운드)
  └── BigQuery API  →  googleapis.com
```

컨테이너끼리는 **서비스명이 DNS 호스트명**이 됩니다.
`postgres`, `redis`, `backend`, `frontend`로 서로를 직접 참조합니다.

---

## 6. 데이터베이스 초기화 및 마이그레이션 전략

### 전략 개요

DB 초기화는 **두 단계**로 나뉩니다.

```
[1단계] Docker 최초 실행 시
  infra/postgres/init/*.sql 자동 실행
  → PostgreSQL 확장 기능 활성화 (uuid-ossp, pgcrypto)
  → 읽기전용 계정 생성 등 인프라 수준 초기 설정

[2단계] 백엔드 컨테이너 시작 시
  Alembic 마이그레이션 자동 실행
  → 실제 테이블 생성 및 스키마 관리
  → OWNER 계정 시드 데이터 삽입
```

### infra/postgres/init/ 파일 역할

```sql
-- infra/postgres/init/00_create_extensions.sql
-- 이 파일은 Alembic이 아닌 postgres 컨테이너가 직접 실행합니다.
-- 컨테이너 볼륨이 비어있을 때 한 번만 실행되며, 재실행되지 않습니다.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";    -- UUID 생성 함수
CREATE EXTENSION IF NOT EXISTS "pgcrypto";     -- gen_random_uuid() 등
CREATE EXTENSION IF NOT EXISTS "pg_trgm";      -- LIKE 검색 성능 향상 (선택)
```

> **주의:** `infra/postgres/init/`의 파일은 PostgreSQL 데이터 볼륨이 **비어있을 때만** 실행됩니다.
> 기존 데이터가 있는 경우 (볼륨이 존재하는 경우) 실행되지 않습니다.
> 스키마 변경은 반드시 Alembic 마이그레이션으로 관리해야 합니다.

### Alembic 마이그레이션 플로우

```
# 새 마이그레이션 파일 생성 (모델 변경 후)
docker compose exec backend alembic revision --autogenerate -m "add_user_table"

# 마이그레이션 실행 (최신으로)
docker compose exec backend alembic upgrade head

# 하나 롤백
docker compose exec backend alembic downgrade -1

# 현재 적용 상태 확인
docker compose exec backend alembic current
```

### 백엔드 컨테이너 시작 시 자동 마이그레이션

`apps/backend/app/main.py`의 startup 이벤트 또는 별도 entrypoint 스크립트에서 처리합니다.

```python
# apps/backend/entrypoint.sh  (Dockerfile CMD 대신 사용)

#!/bin/sh
echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting FastAPI server..."
exec gunicorn app.main:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 마이그레이션 파일 버전 관리

```
alembic/versions/
├── 0001_initial_schema.py          # 전체 초기 테이블 생성
├── 0002_add_chart_groups.py        # 기능 추가 시마다 파일 생성
└── 0003_add_audit_log_index.py
```

- 마이그레이션 파일은 항상 Git에 커밋합니다.
- 한 번 운영 DB에 적용된 마이그레이션 파일은 수정하지 않습니다. (새 파일 추가)

---

## 7. Redis 역할 및 구성

Redis는 **임시 데이터를 빠르게 읽고 쓰는 인메모리 저장소**입니다.
디스크 기반인 PostgreSQL에 비해 응답 속도가 수십~수백 배 빠릅니다.
재시작 시 데이터 유실을 허용하는 임시 데이터에만 사용하고,
중요한 영구 데이터는 모두 PostgreSQL에 저장합니다.

### LookFlex에서 Redis를 사용하는 곳

| 용도 | 키 패턴 예시 | TTL | 설명 |
|---|---|---|---|
| 이메일 인증 코드 | `verify:user@example.com` | 10분 | 회원가입 이메일 OTP |
| 비밀번호 재설정 토큰 | `pwreset:<token>` | 1시간 | 재설정 링크 유효성 |
| Refresh Token 블랙리스트 | `blacklist:<jti>` | 토큰 잔여 만료시간 | 로그아웃한 토큰 무효화 |
| 쿼리 결과 캐시 | `query:<chart_id>:<filter_hash>` | 5~30분 | 외부 DB 쿼리 결과 캐싱 |
| 관리자 알림 카운터 | `notify:unread:<user_id>` | 없음 | 빠른 알림 배지 카운트 |

### Redis 설정 (`infra/redis/redis.conf`)

```conf
# infra/redis/redis.conf

# 비밀번호 설정 (환경변수로 주입하기 어려우므로 파일에서 관리)
requirepass your_redis_password_here

# 최대 메모리 사용량 (서버 RAM에 맞게 조정)
maxmemory 256mb

# 메모리 초과 시 정책: LRU(최근 미사용) 기준으로 TTL 있는 키부터 제거
maxmemory-policy allkeys-lru

# 데이터 영속성: AOF 비활성화 (임시 데이터만 저장하므로 재시작 시 유실 허용)
appendonly no

# RDB 스냅샷도 비활성화 (임시 데이터 특성상 불필요)
save ""
```

### Redis 사용 패턴 예시 (Python)

```python
# apps/backend/app/services/cache_service.py

import json
from redis.asyncio import Redis

class CacheService:
    def __init__(self, redis: Redis):
        self.redis = redis

    # 이메일 인증 코드 저장 (10분 TTL)
    async def set_verify_code(self, email: str, code: str) -> None:
        await self.redis.setex(f"verify:{email}", 600, code)

    async def get_verify_code(self, email: str) -> str | None:
        return await self.redis.get(f"verify:{email}")

    # 차트 쿼리 결과 캐싱
    async def set_query_cache(self, key: str, data: dict, ttl: int = 300) -> None:
        await self.redis.setex(f"query:{key}", ttl, json.dumps(data))

    async def get_query_cache(self, key: str) -> dict | None:
        cached = await self.redis.get(f"query:{key}")
        return json.loads(cached) if cached else None
```

---

## 8. 네트워크 및 볼륨 설계

### 네트워크

```
internal (bridge network)
  ├── nginx         (포트 80/443만 외부 노출)
  ├── backend       (외부 직접 접근 불가, nginx 경유)
  ├── frontend      (외부 직접 접근 불가, nginx 경유)
  ├── postgres      (외부 직접 접근 불가)
  └── redis         (외부 직접 접근 불가)
```

개발 환경에서는 `docker-compose.dev.yml`로 `postgres:5432`, `redis:6379`,
`backend:8000`, `frontend:3000`을 로컬호스트에 직접 노출합니다.

### 볼륨

```
postgres_data    → /var/lib/postgresql/data  (PostgreSQL 데이터 영구 저장)
redis_data       → /data                     (선택: RDB 스냅샷 저장 시 사용)
```

운영 환경에서는 `postgres_data` 볼륨 디렉터리를 정기적으로 백업합니다.

```bash
# 백업 예시 (crontab에 등록)
docker exec lookflex-postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB \
  | gzip > /backup/lookflex_$(date +%Y%m%d).sql.gz
```

---

## 9. 환경 변수 관리

루트의 `.env` 파일 하나를 Docker Compose가 자동으로 읽습니다.
각 서비스에 필요한 변수를 `docker-compose.yml`의 `environment` 블록에서 개별 주입합니다.

```bash
# .env.example  (이 파일은 Git에 포함, 실제 값 없이 키만 나열)

# PostgreSQL
POSTGRES_DB=lookflex
POSTGRES_USER=lookflex_user
POSTGRES_PASSWORD=

# Redis
REDIS_PASSWORD=

# Backend
SECRET_KEY=                      # openssl rand -hex 32 로 생성
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_NAME=LookFlex
SMTP_FROM_EMAIL=

# BigQuery (서비스 계정 JSON 키 파일 경로)
GOOGLE_APPLICATION_CREDENTIALS=/secrets/bigquery-key.json

# Frontend
NEXT_PUBLIC_API_URL=http://localhost/api/v1
```

**민감 정보 파일 (BigQuery 서비스 계정 키)**

BigQuery 서비스 계정 키 JSON은 환경변수로 직접 주입하기 어려우므로
파일로 관리하며 볼륨 마운트로 컨테이너에 주입합니다.

```yaml
# docker-compose.yml에 추가
services:
  backend:
    volumes:
      - ./secrets/bigquery-key.json:/secrets/bigquery-key.json:ro
```

```
# .gitignore에 반드시 포함
.env
secrets/
```

---

## 10. 개발 vs 운영 환경 분리

### 실행 명령

```bash
# 개발 환경 (hot-reload, 포트 직접 노출)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 운영 환경
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 전체 중지
docker compose down

# 데이터 포함 완전 초기화 (주의!)
docker compose down -v
```

편의를 위해 루트에 `Makefile`을 두는 것을 권장합니다.

```makefile
# Makefile

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

dev-down:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down

prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

prod-down:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

migrate:
	docker compose exec backend alembic upgrade head

makemigration:
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

logs:
	docker compose logs -f $(service)

ps:
	docker compose ps
```

```bash
# 사용 예시
make dev                          # 개발 서버 시작
make migrate                      # 마이그레이션 실행
make makemigration msg="add_index" # 새 마이그레이션 파일 생성
make logs service=backend         # 백엔드 로그 스트리밍
```

---

## 11. Git 브랜치 전략

### 브랜치 모델: GitHub Flow (단순화된 Git Flow)

혼자 또는 소규모로 개발하는 환경에서 Git Flow(develop/release/hotfix 등)는 관리 포인트가 너무 많습니다.
**메인 브랜치 2개 + 작업 브랜치** 구조의 GitHub Flow를 사용합니다.

```
main         ─────●─────────●─────────●──────────►  (운영 배포)
                  │         ↑         ↑
                  │    merge│    merge│
                  │         │         │
dev          ─────●────●────●────●────●────●──────►  (개발 통합)
                       │         │
                  feature/   fix/
                  브랜치     브랜치
```

### 브랜치 정의

| 브랜치 | 역할 | 보호 규칙 |
|---|---|---|
| `main` | 운영 서버에 배포되는 안정 브랜치 | 직접 push 금지, PR + 리뷰 병합 |
| `dev` | 개발 중인 기능이 통합되는 브랜치 | 직접 push 금지 (권고), PR 병합 |
| `feature/*` | 새 기능 개발 | `dev`에서 분기, `dev`로 병합 |
| `fix/*` | 버그 수정 | `dev`에서 분기, `dev`로 병합 |
| `hotfix/*` | 운영 긴급 수정 | `main`에서 분기, `main`과 `dev` 모두 병합 |
| `chore/*` | 문서, 설정, 리팩터링 등 비기능 변경 | `dev`에서 분기, `dev`로 병합 |

### 브랜치 네이밍 규칙

```
feature/{도메인}-{작업 요약}
fix/{도메인}-{버그 요약}
hotfix/{버전 또는 이슈}-{요약}
chore/{작업 요약}

# 예시
feature/auth-register-flow
feature/dashboard-conditional-format
feature/datasource-bigquery-connector
fix/chart-null-field-rendering
fix/auth-refresh-token-expiry
hotfix/1.0.1-login-500-error
chore/update-api-docs
chore/docker-compose-redis-config
```

### 작업 흐름

```bash
# 1. dev 최신 상태로 업데이트
git checkout dev
git pull origin dev

# 2. 작업 브랜치 생성
git checkout -b feature/auth-register-flow

# 3. 작업 및 커밋
git add .
git commit -m "feat(auth): add email verification on register"

# 4. dev에 PR 생성 후 병합
#    → GitHub에서 PR 생성: feature/auth-register-flow → dev

# 5. 기능 충분히 검증 후 dev → main PR 생성 (배포)
#    → GitHub에서 PR 생성: dev → main
#    → main 병합 시 docker compose 재시작으로 배포
```

### 커밋 메시지 규칙 (Conventional Commits)

```
<type>(<scope>): <요약>

type:
  feat      새 기능
  fix       버그 수정
  docs      문서 변경
  style     코드 포맷 (로직 변경 없음)
  refactor  리팩터링
  test      테스트 추가/수정
  chore     빌드, 설정, 패키지 등

scope (선택):
  auth | user | dashboard | chart | datasource | filter | infra | ci

# 예시
feat(auth): add JWT refresh token rotation
fix(chart): handle null value in conditional formatting
docs(api): update datasource permission endpoint
chore(infra): add redis maxmemory config
refactor(datasource): extract query builder to separate class
```

### 태깅 및 배포 버전 관리

`main` 브랜치에 병합할 때마다 태그를 붙여 배포 시점을 추적합니다.

```bash
# dev → main 병합 후 태그 생성
git tag -a v1.0.0 -m "Initial release: auth + dashboard MVP"
git push origin v1.0.0
```

버전 규칙 (Semantic Versioning):

```
v{MAJOR}.{MINOR}.{PATCH}

MAJOR: 하위 호환 불가 변경 (DB 마이그레이션 필수, API Breaking Change)
MINOR: 하위 호환 새 기능 추가 (새 API 엔드포인트, 새 필드)
PATCH: 버그 수정, 문서, 설정 변경
```

### `.gitignore` 핵심 항목

```gitignore
# 환경변수 및 시크릿
.env
.env.local
secrets/

# Python
__pycache__/
*.pyc
.venv/
*.egg-info/

# Node.js
node_modules/
.next/
.turbo/

# 빌드 결과물
dist/
build/

# IDE
.vscode/settings.json
.idea/

# 로컬 개발 임시 파일
*.log
*.sql.gz
```

---

*최종 업데이트: 2026-02-28*
