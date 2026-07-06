-- Shadow v35 — Supabase table setup
-- Run in Supabase SQL Editor before testing v35.
-- Schema derived directly from index.html read/write calls (the frontend contract).
-- All tables: RLS disabled (single-user app, UID = 'abdulrahman').

-- ============ shadow_profile ============
-- Frontend: insert {user_id, data}; update {journal_pin}; select * order by updated_at.
-- delete().neq('id',0) => integer id. UID='abdulrahman' => user_id is TEXT.
create table if not exists shadow_profile (
  id          bigint generated always as identity primary key,
  user_id     text,
  data        jsonb,
  journal_pin text,
  updated_at  timestamptz default now()
);
alter table shadow_profile disable row level security;

-- ============ shadow_feedback ============
-- Frontend: insert {user_id, context, rating, comment}; select * order by created_at.
create table if not exists shadow_feedback (
  id         bigint generated always as identity primary key,
  user_id    text,
  context    text,
  rating     text,
  comment    text,
  created_at timestamptz default now()
);
alter table shadow_feedback disable row level security;

-- ============ shadow_trades ============
-- Frontend: insert {user_id, run_id, stage, status, detail}. Audit trail per Trade Desk run.
create table if not exists shadow_trades (
  id         bigint generated always as identity primary key,
  user_id    text,
  run_id     text,
  stage      text,
  status     text,
  detail     text,
  created_at timestamptz default now()
);
alter table shadow_trades disable row level security;
