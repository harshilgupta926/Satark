-- Keep response approval consumption unavailable until a trusted executor exists.
-- Direct client calls could consume an approval without completing provider action.
revoke execute on function public.satark_consume_response_approval(uuid,uuid,uuid,text,text) from public, anon, authenticated, service_role;
revoke execute on function satark_private.consume_response_approval(uuid,uuid,uuid,text,text) from public, anon, authenticated, service_role;
