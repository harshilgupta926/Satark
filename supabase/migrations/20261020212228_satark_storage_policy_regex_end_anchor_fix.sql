-- Fix storage object path validation: PostgreSQL POSIX regex uses $ for end-of-string.
-- The previous \\Z suffix was treated as a literal backslash/Z pair and rejected valid paths.
-- Preserve the tenant membership checks and role split for ordinary vs. Wazuh evidence.

drop policy if exists satark_evidence_object_insert on storage.objects;
create policy satark_evidence_object_insert
on storage.objects
for insert
to authenticated
with check (
  bucket_id = 'satark-evidence'
  and split_part(name, '/', 1) ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
  and split_part(name, '/', 2) ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
  and (
    (
      array_length(string_to_array(name, '/'), 1) = 3
      and split_part(name, '/', 3) ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}_[A-Za-z0-9._-]{1,100}$'
    )
    or
    (
      array_length(string_to_array(name, '/'), 1) = 4
      and split_part(name, '/', 3) = 'wazuh'
      and length(split_part(name, '/', 4)) = 69
      and split_part(name, '/', 4) ~* '^[0-9a-f]{64}[.]json$'
    )
  )
  and satark_private.has_membership(
    split_part(name, '/', 1)::uuid,
    array['owner', 'responder', 'analyst']::text[]
  )
  and exists (
    select 1
    from public.satark_cases c
    where c.id = split_part(objects.name, '/', 2)::uuid
      and c.tenant_id = split_part(objects.name, '/', 1)::uuid
      and satark_private.has_membership(
        c.tenant_id,
        array['owner', 'responder', 'analyst']::text[]
      )
  )
);

drop policy if exists satark_evidence_object_read on storage.objects;
create policy satark_evidence_object_read
on storage.objects
for select
to authenticated
using (
  bucket_id = 'satark-evidence'
  and split_part(name, '/', 1) ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
  and split_part(name, '/', 2) ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
  and (
    (
      array_length(string_to_array(name, '/'), 1) = 3
      and split_part(name, '/', 3) ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}_[A-Za-z0-9._-]{1,100}$'
    )
    or
    (
      array_length(string_to_array(name, '/'), 1) = 4
      and split_part(name, '/', 3) = 'wazuh'
      and length(split_part(name, '/', 4)) = 69
      and split_part(name, '/', 4) ~* '^[0-9a-f]{64}[.]json$'
    )
  )
  and satark_private.has_membership(
    split_part(name, '/', 1)::uuid,
    array['owner', 'responder', 'analyst', 'viewer']::text[]
  )
  and exists (
    select 1
    from public.satark_cases c
    where c.id = split_part(objects.name, '/', 2)::uuid
      and c.tenant_id = split_part(objects.name, '/', 1)::uuid
      and (
        (
          array_length(string_to_array(objects.name, '/'), 1) = 4
          and split_part(objects.name, '/', 3) = 'wazuh'
          and length(split_part(objects.name, '/', 4)) = 69
          and split_part(objects.name, '/', 4) ~* '^[0-9a-f]{64}[.]json$'
          and satark_private.has_membership(
            c.tenant_id,
            array['owner', 'responder', 'analyst']::text[]
          )
        )
        or
        (
          array_length(string_to_array(objects.name, '/'), 1) = 3
          and split_part(objects.name, '/', 3) ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}_[A-Za-z0-9._-]{1,100}$'
          and satark_private.has_membership(
            c.tenant_id,
            array['owner', 'responder', 'analyst', 'viewer']::text[]
          )
        )
      )
  )
);
