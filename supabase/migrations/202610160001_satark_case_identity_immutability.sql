-- Keep case identity and creation metadata immutable even for direct PostgREST callers.
-- The application API already excludes these fields from PATCH; RLS should not be the
-- only control because membership-based UPDATE policies otherwise permit column changes.
create or replace function public.satark_guard_case_identity()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  if new.id is distinct from old.id
    or new.tenant_id is distinct from old.tenant_id
    or new.created_by is distinct from old.created_by
    or new.created_at is distinct from old.created_at
    or new.updated_at is distinct from old.updated_at then
    raise exception 'SATARK case identity and timestamps are immutable'
      using errcode = '42501';
  end if;
  return new;
end;
$$;

revoke all on function public.satark_guard_case_identity() from public, anon, authenticated;
drop trigger if exists satark_case_identity_immutable on public.satark_cases;
create trigger satark_case_identity_immutable
  before update on public.satark_cases
  for each row execute function public.satark_guard_case_identity();
