import assert from 'node:assert/strict';
import test from 'node:test';
import { buildFirstlightFindings, getTrustedFirstlightEvidence } from '../src/lib/firstlight-investigation.mjs';

test('tampered records are quarantined from findings and references', () => {
  const evidence = [
    { id: 'EV-TRUSTED', kind: 'sign_in', summary: 'Successful sign-in from a new browser profile.', digest: 'baseline' },
    { id: 'EV-TAMPERED', kind: 'rule_change', summary: 'A new inbox forwarding rule was created.', digest: 'baseline', tampered: true },
  ];

  assert.deepEqual(getTrustedFirstlightEvidence(evidence).map(item => item.id), ['EV-TRUSTED']);
  const findings = buildFirstlightFindings(evidence);
  assert.equal(findings.some(item => item.title === 'Unfamiliar sign-in context'), true);
  assert.equal(findings.some(item => item.title === 'Mailbox forwarding or rule change'), false);
  assert.ok(findings.every(item => !item.refs.includes('EV-TAMPERED')));
});

test('no finding is produced solely from tampered evidence', () => {
  const evidence = [
    { id: 'EV-TAMPERED', kind: 'mfa_change', summary: 'Multi-factor authentication settings were changed.', tampered: true },
    { id: 'EV-TAMPERED-2', kind: 'message', summary: 'Urgent password confirmation from a lookalike domain.', tampered: true },
  ];

  assert.deepEqual(getTrustedFirstlightEvidence(evidence), []);
  assert.deepEqual(buildFirstlightFindings(evidence), []);
});

test('valid evidence keeps expected references for a rule match', () => {
  const evidence = [
    { id: 'EV-1', kind: 'rule_change', summary: 'A new inbox forwarding rule was created.' },
    { id: 'EV-2', kind: 'message', summary: 'Routine internal notice.' },
  ];
  const finding = buildFirstlightFindings(evidence).find(item => item.title === 'Mailbox forwarding or rule change');
  assert.ok(finding);
  assert.deepEqual(finding.refs, ['EV-1']);
});
