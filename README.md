# LookFlex — 커스텀 비즈니스 대시보드 플랫폼

> Google Looker Studio의 한계를 극복하고, 커머스 도메인에 최적화된 사내 전용 데이터 시각화 플랫폼

---

## 목차

1. [프로젝트 배경 및 목표](#1-프로젝트-배경-및-목표)
2. [해결하려는 문제](#2-해결하려는-문제)
3. [시스템 개요](#3-시스템-개요)
4. [기술 스택](#4-기술-스택)
5. [아키텍처 설계](#5-아키텍처-설계)
6. [디렉터리 구조](#6-디렉터리-구조)
7. [주요 기능 목록](#7-주요-기능-목록)
8. [데이터 흐름](#8-데이터-흐름)
9. [배포 전략](#9-배포-전략)
10. [개발 로드맵](#10-개발-로드맵)

---

## 1. 프로젝트 배경 및 목표

LookFlex는 Google Looker Studio를 대체하기 위해 시작된 사내 전용 대시보드 플랫폼입니다.
BigQuery에 적재된 매출 및 광고 데이터를 기반으로, 구성원 각자가 원하는 방식으로 데이터를 조회하고 시각화할 수 있는 환경을 제공합니다.

**핵심 목표**

- 테이블 중심의 데이터 조회 및 분석 환경 제공
- 사용자별 뷰/메트릭 커스터마이징 설정 저장 및 복원
- 조건부 서식, 정렬, 필터링을 UI뿐만 아니라 설정 파일로도 관리
- 100명 미만 규모의 사내 구성원 대상, 역할 기반 접근 제어
- 로컬 서버 우선 운영, 이후 인터넷 공개 배포 가능한 구조

---

## 2. 해결하려는 문제

| 문제 | Looker Studio 현황 | LookFlex 목표 |
|---|---|---|
| 레이아웃 자유도 부족 | 그리드 간격이 넓어 표 배치가 부자연스러움 | px 단위 자유 배치 + 그리드 설정 옵션 제공 |
| 메트릭 변경 UX 불편 | 조회 권한 사용자가 헤더 아이콘을 찾아 클릭해야 함 | 사이드바 또는 상단 컨트롤 패널로 직관적 전환 |
| 조건부 서식 설정 비효율 | 열 단위로 마우스 UI 조작 반복 | JSON/YAML 설정으로 일괄 적용, UI에서도 편집 가능 |
| 뷰 저장/공유 불가 | 개인 설정이 저장되지 않음 | 사용자별 커스텀 뷰를 DB에 저장하고 복원 |
| 역할 기반 접근 제어 미흡 | 보기/편집 권한이 단순함 | Admin / Editor / Viewer 역할 분리 |

---

## 3. 시스템 개요

```
[BigQuery]
    │  배치 ETL (예: 매일 새벽 집계)
    ▼
[FastAPI 백엔드]  ←──────────────────────────────┐
    │  REST API (JWT 인증)                       │
    ▼                                           │
[Next.js 프론트엔드]  ←→  [사용자 브라우저]       │
                                                │
[PostgreSQL]  ←── 사용자 계정, 대시보드 설정 저장  │
[Redis]       ←── 쿼리 결과 캐시 (선택)  ─────────┘
```

---

## 4. 기술 스택

### 4-1. 프론트엔드

| 항목 | 선택 | 이유 |
|---|---|---|
| 프레임워크 | **Next.js 14+ (App Router)** | SSR/SSG 지원, API Route 활용 가능, 배포 유연성 |
| 언어 | **TypeScript** | 타입 안전성, 유지보수성 |
| 스타일링 | **Tailwind CSS + shadcn/ui** | 빠른 UI 구성, 컴포넌트 커스터마이징 용이 |
| 테이블 | **TanStack Table v8** | 정렬·필터·가상 스크롤·조건부 서식·컬럼 커스터마이징을 코드 레벨에서 완전 제어 |
| 차트 | **Apache ECharts (echarts-for-react)** | 복잡한 커스터마이징, 대용량 데이터 렌더링 성능 우수 |
| 서버 상태 관리 | **TanStack Query (React Query)** | 캐싱, 백그라운드 갱신, 로딩/에러 상태 관리 |
| 클라이언트 상태 | **Zustand** | 경량, 단순한 전역 상태 관리 |
| 폼 | **React Hook Form + Zod** | 유효성 검사, 타입 추론 |
| 날짜 | **date-fns** | 경량 날짜 유틸리티 |

### 4-2. 백엔드

| 항목 | 선택 | 이유 |
|---|---|---|
| 프레임워크 | **FastAPI (Python 3.11+)** | 비동기 지원, 자동 OpenAPI 문서, BigQuery 등 데이터 생태계와 동일 언어 |
| ORM | **SQLAlchemy 2.0 (async)** | PostgreSQL과의 비동기 통합, 마이그레이션 관리 용이 |
| 마이그레이션 | **Alembic** | SQLAlchemy와 통합된 DB 스키마 버전 관리 |
| 인증 | **JWT (python-jose) + bcrypt (passlib)** | Stateless 인증, 로컬/인터넷 환경 모두 적합 |
| 데이터 검증 | **Pydantic v2** | FastAPI와 네이티브 통합, 빠른 직렬화 |
| BigQuery 연동 | **google-cloud-bigquery** | 공식 Python 클라이언트, pandas 연동 지원 |
| 배치 스케줄러 | **APScheduler** (또는 외부 cron) | 정해진 시간에 BigQuery → PostgreSQL ETL 실행 |

### 4-3. 데이터베이스 / 인프라

| 항목 | 선택 | 이유 |
|---|---|---|
| 주 DB | **PostgreSQL 16** | 사용자 계정, 대시보드 구성, 커스텀 설정 저장 |
| 캐시 (선택) | **Redis 7** | BigQuery 쿼리 결과 캐싱, 세션 토큰 관리 |
| 컨테이너 | **Docker + Docker Compose** | 로컬 서버 일관성 있는 실행 환경, 이후 클라우드 이전 용이 |
| 리버스 프록시 | **Nginx** | 프론트·백엔드 단일 도메인 라우팅, 향후 HTTPS 적용 |
| 환경 변수 관리 | **.env + python-dotenv / Next.js env** | 로컬/프로덕션 환경 분리 |

### 4-4. 기술 스택 요약 다이어그램

```
┌─────────────────────────────────────────────────────┐
│                    Browser                          │
│  Next.js (TypeScript)                               │
│  TanStack Table │ ECharts │ TanStack Query │ Zustand │
└────────────────────────┬────────────────────────────┘
                         │ HTTPS / REST API
┌────────────────────────▼────────────────────────────┐
│                  Nginx (Reverse Proxy)               │
└──────┬─────────────────────────────────┬────────────┘
       │                                 │
┌──────▼──────┐                 ┌────────▼───────┐
│  FastAPI    │                 │   Next.js      │
│  (Python)   │                 │   (Static/SSR) │
│  Port 8000  │                 │   Port 3000    │
└──────┬──────┘                 └────────────────┘
       │
┌──────▼──────────────────┐
│   PostgreSQL  │  Redis   │
└──────┬──────────────────┘
       │
┌──────▼──────┐
│  BigQuery   │  (Google Cloud — 읽기 전용)
└─────────────┘
```

---

## 5. 아키텍처 설계

### 5-1. 인증 흐름

```
1. 사용자 → POST /api/auth/login (email + password)
2. FastAPI → bcrypt 비밀번호 검증
3. FastAPI → JWT Access Token (15분) + Refresh Token (7일) 발급
4. 프론트 → Access Token을 메모리에 저장, Refresh Token은 HttpOnly Cookie
5. 만료 시 → /api/auth/refresh 로 자동 갱신
```

### 5-2. 역할(Role) 설계

| 역할 | 권한 |
|---|---|
| `Admin` | 사용자 관리, 데이터소스 연결, 대시보드 생성·편집·삭제 |
| `Editor` | 대시보드 편집, 뷰 저장, 조건부 서식 설정 |
| `Viewer` | 대시보드 조회, 개인 뷰 저장 (다른 사람에게는 비공개) |

### 5-3. 대시보드 설정 저장 구조 (PostgreSQL)

사용자별 커스터마이징 설정은 JSONB 컬럼으로 유연하게 저장합니다.

```sql
-- 대시보드
CREATE TABLE dashboards (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL,
    owner_id    UUID REFERENCES users(id),
    config      JSONB,          -- 레이아웃, 위젯 배치 정보
    is_public   BOOLEAN DEFAULT false,
    created_at  TIMESTAMPTZ DEFAULT now(),
    updated_at  TIMESTAMPTZ DEFAULT now()
);

-- 사용자별 뷰 오버라이드 (개인 커스터마이징)
CREATE TABLE user_view_configs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    dashboard_id    UUID REFERENCES dashboards(id),
    widget_id       VARCHAR(100),
    config          JSONB,      -- 메트릭 선택, 조건부 서식, 정렬 등
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE (user_id, dashboard_id, widget_id)
);
```

**`config` JSONB 예시 (테이블 위젯)**

```json
{
  "metrics": ["settlement_amount", "margin", "roi"],
  "sort": { "column": "settlement_amount", "direction": "desc" },
  "conditionalFormatting": [
    {
      "column": "roi",
      "rules": [
        { "condition": "lt", "value": 0, "style": { "backgroundColor": "#fee2e2", "color": "#dc2626" } },
        { "condition": "gte", "value": 50, "style": { "backgroundColor": "#dcfce7", "color": "#16a34a" } }
      ]
    }
  ],
  "columnWidths": { "brand": 120, "roi": 80 },
  "frozenColumns": ["brand"]
}
```

---

## 6. 디렉터리 구조

```
lookflex/
├── apps/
│   ├── frontend/                  # Next.js 앱
│   │   ├── app/                   # App Router
│   │   │   ├── (auth)/            # 로그인/회원가입 페이지
│   │   │   ├── dashboard/         # 대시보드 뷰
│   │   │   └── admin/             # 관리자 페이지
│   │   ├── components/
│   │   │   ├── table/             # TanStack Table 기반 컴포넌트
│   │   │   ├── chart/             # ECharts 래퍼 컴포넌트
│   │   │   └── ui/                # shadcn/ui 공통 컴포넌트
│   │   ├── lib/
│   │   │   ├── api/               # API 클라이언트 (axios/fetch)
│   │   │   └── store/             # Zustand 스토어
│   │   └── ...
│   │
│   └── backend/                   # FastAPI 앱
│       ├── app/
│       │   ├── api/
│       │   │   ├── auth.py        # 인증 라우터
│       │   │   ├── dashboards.py  # 대시보드 CRUD
│       │   │   ├── data.py        # BigQuery 데이터 조회
│       │   │   └── users.py       # 사용자 관리
│       │   ├── core/
│       │   │   ├── config.py      # 환경변수, 설정
│       │   │   └── security.py    # JWT, bcrypt
│       │   ├── db/
│       │   │   ├── models.py      # SQLAlchemy 모델
│       │   │   └── session.py     # DB 세션
│       │   ├── services/
│       │   │   ├── bigquery.py    # BigQuery 쿼리 서비스
│       │   │   └── etl.py         # 배치 ETL 로직
│       │   └── main.py
│       └── alembic/               # DB 마이그레이션
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── nginx/
│   └── nginx.conf
└── README.md
```

---

## 7. 주요 기능 목록

### Phase 1 — 핵심 기반 (MVP)

- [ ] 사용자 인증 (로그인 / 로그아웃 / JWT 갱신)
- [ ] 역할 기반 접근 제어 (Admin / Editor / Viewer)
- [ ] BigQuery 연결 및 데이터 조회 API
- [ ] 테이블 위젯: 정렬, 필터, 페이지네이션
- [ ] 대시보드 레이아웃 저장/불러오기
- [ ] 사용자별 메트릭 선택 저장 (개인 뷰)

### Phase 2 — 테이블 고도화

- [ ] 조건부 서식: JSON 설정 및 UI 편집기 지원
- [ ] 컬럼 고정(freeze), 컬럼 너비 조정 저장
- [ ] 행 그룹핑 및 소계/합계 행
- [ ] 드릴다운 (브랜드 → 상품 → SKU)
- [ ] CSV / Excel 내보내기

### Phase 3 — 차트 및 UX

- [ ] 꺾은선 그래프, 막대 그래프, 누적 막대 (ECharts)
- [ ] 날짜 범위 필터 (전역 컨트롤 패널)
- [ ] 필터 값 URL 파라미터 동기화 (링크 공유)
- [ ] 대시보드 북마크 / 즐겨찾기

### Phase 4 — 운영 및 확장

- [ ] Admin 페이지: 사용자 초대, 역할 변경
- [ ] 감사 로그 (누가 언제 어떤 데이터 조회)
- [ ] 배치 ETL 모니터링 (마지막 실행 시간, 실패 알림)
- [ ] HTTPS / 외부 인터넷 배포 지원

---

## 8. 데이터 흐름

### 8-1. 배치 ETL (BigQuery → PostgreSQL 집계 캐시, 선택)

소규모 사내 환경에서는 BigQuery를 직접 조회해도 무방하지만, 응답 속도 및 비용 최적화가 필요하면 집계 결과를 PostgreSQL에 캐싱합니다.

```
매일 새벽 N시 (APScheduler / cron)
  → FastAPI ETL 서비스 실행
  → BigQuery에서 일별 집계 쿼리 실행
  → 결과를 PostgreSQL `daily_aggregates` 테이블에 upsert
  → Redis 캐시 무효화
```

### 8-2. 실시간 조회 흐름 (직접 쿼리 모드)

```
브라우저 → GET /api/data/sales?date=2026-02-02&brand=닥터트루
  → FastAPI → google-cloud-bigquery 클라이언트로 쿼리 실행
  → 결과 JSON 반환 → TanStack Query가 캐싱 (staleTime 설정)
  → TanStack Table로 렌더링
```

---

## 9. 배포 전략

### 로컬 서버 (현재)

```bash
# 전체 스택 실행
docker compose up -d

# 서비스 구성
# - frontend:  http://localhost:3000
# - backend:   http://localhost:8000
# - nginx:     http://localhost:80  (단일 진입점)
# - postgres:  localhost:5432
# - redis:     localhost:6379
```

### 인터넷 공개 배포 (향후)

| 항목 | 방안 |
|---|---|
| 서버 | 사내 서버에 공인 IP 할당 또는 AWS EC2 / GCP Compute Engine |
| HTTPS | Let's Encrypt + Nginx certbot |
| 도메인 | 사내 도메인 또는 서브도메인 설정 |
| CI/CD | GitHub Actions → Docker 이미지 빌드 → 서버 SSH 배포 |
| 백업 | PostgreSQL pg_dump 일 1회 cron + GCS/S3 업로드 |

Docker Compose 기반으로 개발하면 로컬 → 클라우드 마이그레이션 시 `docker-compose.prod.yml` 오버라이드만으로 환경 전환이 가능합니다.

---

## 10. 개발 로드맵

```
2026 Q1  ───────────────────────────────────────────────────────►
  │
  ├─ [Week 1-2]  프로젝트 골격 세팅
  │               Docker Compose, PostgreSQL, FastAPI 초기화
  │               Next.js 프로젝트 세팅, 인증 UI
  │
  ├─ [Week 3-4]  인증 완성 + BigQuery 연결
  │               JWT 발급/검증, 역할 미들웨어
  │               BigQuery 서비스 계정 연동, 데이터 API
  │
  ├─ [Week 5-6]  MVP 테이블 위젯
  │               TanStack Table 기반 매출 요약 테이블
  │               메트릭 선택, 정렬, 기본 필터
  │
  ├─ [Week 7-8]  설정 저장 + 조건부 서식
  │               사용자별 뷰 config DB 저장/불러오기
  │               조건부 서식 UI 편집기 + JSON 파싱
  │
2026 Q2
  ├─ [Week 9-12]  차트 위젯 + 대시보드 레이아웃
  │
  └─ [Week 13+]   운영 기능, 외부 배포 준비
```

---

## 기여 및 개발 환경 설정

> 상세 내용은 각 앱의 README를 참고하세요.
> - [apps/frontend/README.md](apps/frontend/README.md)
> - [apps/backend/README.md](apps/backend/README.md)

```bash
# 저장소 클론
git clone https://github.com/cuz/lookflex.git
cd lookflex

# 환경 변수 복사
cp .env.example .env
# .env 파일에서 BigQuery 서비스 계정 키 경로, DB 비밀번호 등 설정

# 전체 스택 실행
docker compose up -d
```

---

*LookFlex — Built to replace Looker Studio, one table at a time.*
