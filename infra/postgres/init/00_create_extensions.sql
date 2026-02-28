-- 이 파일은 postgres 컨테이너 최초 실행 시 자동으로 1회 실행됩니다.
-- 볼륨이 이미 존재하면 재실행되지 않습니다.
-- 스키마 변경은 Alembic 마이그레이션으로 관리하세요.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- UUID 생성 함수
CREATE EXTENSION IF NOT EXISTS "pgcrypto";    -- gen_random_uuid() 등
CREATE EXTENSION IF NOT EXISTS "pg_trgm";     -- LIKE 검색 성능 향상
