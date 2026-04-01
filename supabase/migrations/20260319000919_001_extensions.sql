-- Enable required extensions
-- gen_random_uuid() is built into PostgreSQL 13+ (no extension needed)
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
