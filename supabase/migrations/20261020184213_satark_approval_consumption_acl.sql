-- Fail closed: no trusted response executor has passed its release gate yet.
-- The current system deliberately constrains approvals to simulation.* actions.
-- A direct authenticated call to the consumption RPC could burn an approval
-- without executing a provider action, so neither the public wrapper nor the
-- private implementation is callable by API roles until an executor-specific
-- server-only identity and end-to-end audit path are implemented.
revoke execute on function public.satark_consume_response_approval(uuid,uuid,uuid,text,text) from public, anon, authenticated, service_role;
revoke execute on function satark_private.consume_response_approval(uuid,uuid,uuid,text,text) from public, anon, authenticated, service_role;
