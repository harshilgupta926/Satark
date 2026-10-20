begin;

select plan(5);

select ok(
  '00000000-0000-4000-8000-000000000000_evidence.bin'
    ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}_[A-Za-z0-9._-]{1,100}$',
  'ordinary evidence filename accepts a valid UUID-prefixed name'
);

select ok(
  '0000000000000000000000000000000000000000000000000000000000000000.json'
    ~ '^[0-9a-f]{64}[.]json$',
  'Wazuh evidence filename accepts a SHA-256 JSON name'
);

select ok(
  not ('0000000000000000000000000000000000000000000000000000000000000000.json.extra'
    ~ '^[0-9a-f]{64}[.]json$'),
  'Wazuh evidence filename rejects trailing path content'
);

select ok(
  exists (
    select 1 from pg_policies
    where schemaname = 'storage'
      and tablename = 'objects'
      and policyname = 'satark_evidence_object_insert'
      and with_check like '%satark_private.has_membership%'
  ),
  'evidence insert policy continues to require the private membership helper'
);

select ok(
  exists (
    select 1 from pg_policies
    where schemaname = 'storage'
      and tablename = 'objects'
      and policyname = 'satark_evidence_object_read'
      and qual like '%satark_private.has_membership%'
  ),
  'evidence read policy continues to require the private membership helper'
);

select * from finish();
rollback;
