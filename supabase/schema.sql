create table if not exists public.users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  full_name text,
  created_at timestamptz not null default now()
);

create table if not exists public.research_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id) on delete set null,
  query text not null,
  status text not null default 'queued',
  plan jsonb,
  sources jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.uploaded_documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id) on delete set null,
  session_id uuid references public.research_sessions(id) on delete set null,
  filename text not null,
  content_type text not null,
  size_bytes integer not null,
  storage_path text not null,
  document_hash text not null,
  extracted_chars integer not null default 0,
  chunks_count integer not null default 0,
  created_at timestamptz not null default now()
);

create table if not exists public.research_reports (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.research_sessions(id) on delete cascade,
  title text not null,
  markdown text not null,
  metadata jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.citations (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.research_sessions(id) on delete cascade,
  title text not null,
  url text,
  authors text,
  source_type text not null default 'web',
  snippet text,
  confidence integer not null default 80,
  created_at timestamptz not null default now()
);

create table if not exists public.research_history (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.research_sessions(id) on delete cascade,
  event_type text not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.research_gap_analyses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id) on delete set null,
  research_domain text not null,
  status text not null default 'running',
  document_ids jsonb not null default '[]'::jsonb,
  paper_summaries jsonb not null default '[]'::jsonb,
  theme_clusters jsonb not null default '[]'::jsonb,
  contradictions jsonb not null default '[]'::jsonb,
  gaps jsonb not null default '[]'::jsonb,
  innovations jsonb not null default '[]'::jsonb,
  scores jsonb not null default '{}'::jsonb,
  knowledge_graph jsonb not null default '{}'::jsonb,
  visualizations jsonb not null default '{}'::jsonb,
  report_markdown text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists research_sessions_user_id_idx on public.research_sessions(user_id);
create index if not exists uploaded_documents_session_id_idx on public.uploaded_documents(session_id);
create index if not exists research_reports_session_id_idx on public.research_reports(session_id);
create index if not exists citations_session_id_idx on public.citations(session_id);
create index if not exists research_history_session_id_idx on public.research_history(session_id);
create index if not exists research_gap_analyses_user_id_idx on public.research_gap_analyses(user_id);

alter table public.users enable row level security;
alter table public.research_sessions enable row level security;
alter table public.uploaded_documents enable row level security;
alter table public.research_reports enable row level security;
alter table public.citations enable row level security;
alter table public.research_history enable row level security;
alter table public.research_gap_analyses enable row level security;

create policy "service role can manage users" on public.users for all using (true) with check (true);
create policy "service role can manage sessions" on public.research_sessions for all using (true) with check (true);
create policy "service role can manage documents" on public.uploaded_documents for all using (true) with check (true);
create policy "service role can manage reports" on public.research_reports for all using (true) with check (true);
create policy "service role can manage citations" on public.citations for all using (true) with check (true);
create policy "service role can manage history" on public.research_history for all using (true) with check (true);
create policy "service role can manage gap analyses" on public.research_gap_analyses for all using (true) with check (true);
