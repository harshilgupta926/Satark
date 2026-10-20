type Ev = { id: string; time: string; kind: string; summary: string; tampered?: boolean };
type Fd = { title: string; severity: string; refs: string[] };

/** Tremor-style summaries for the findings view: findings by severity and evidence integrity. */
export function FindingsInsights({ findings, evidence }: { findings: Fd[]; evidence: Ev[] }) {
  const counts = new Map<string, number>();
  for (const f of findings) counts.set(f.severity, (counts.get(f.severity) ?? 0) + 1);
  const rows = [...counts.entries()].sort((a, b) => b[1] - a[1]);
  const max = Math.max(1, ...rows.map(r => r[1]));
  const verified = evidence.filter(e => !e.tampered).length;
  const quarantined = evidence.length - verified;
  const pct = (n: number) => (evidence.length ? (n / evidence.length) * 100 : 0);
  return (
    <div className="fl-insights">
      <section className="fl-insight" aria-label="Findings by severity">
        <h3>Findings by severity</h3>
        {rows.length ? (
          <ul className="bar-list">
            {rows.map(([severity, count]) => (
              <li key={severity} className={/high|critical/i.test(severity) ? 'tone-danger' : 'tone-warn'}>
                <i style={{ width: (count / max) * 100 + '%' }} aria-hidden="true" />
                <span>{severity}</span><span>{count}</span>
              </li>
            ))}
          </ul>
        ) : <p className="hint">No local pattern matched.</p>}
      </section>
      <section className="fl-insight" aria-label="Evidence integrity">
        <h3>Evidence integrity</h3>
        <div className="kpi-value" style={{ marginTop: 0 }}>{verified}<small>of {evidence.length} records verified</small></div>
        <div className="category-bar" style={{ marginTop: 12 }} aria-hidden="true">
          {verified > 0 && <span style={{ width: pct(verified) + '%', background: 'var(--ok)' }} />}
          {quarantined > 0 && <span style={{ width: pct(quarantined) + '%', background: 'var(--danger)' }} />}
        </div>
        <div className="category-bar-labels"><span>{verified} verified</span><span>{quarantined} quarantined</span></div>
      </section>
    </div>
  );
}

/** Tremor-style tracker: one block per event, coloured by what we know about it. */
export function EventTracker({ timeline, findings }: { timeline: Ev[]; findings: Fd[] }) {
  const flagged = new Set(findings.flatMap(f => f.refs));
  return (
    <div className="fl-insight" style={{ margin: '18px 0 8px' }}>
      <h3>Event sequence</h3>
      <div className="tracker" role="img" aria-label={timeline.length + ' events; ' + timeline.filter(e => e.tampered).length + ' changed after sealing, ' + timeline.filter(e => !e.tampered && flagged.has(e.id)).length + ' linked to findings'}>
        {timeline.map(e => (
          <span key={e.id} className={e.tampered ? 'danger' : flagged.has(e.id) ? 'warn' : 'ok'}
            title={e.id + ' · ' + new Date(e.time).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }) + ' · ' + (e.tampered ? 'changed after sealing' : flagged.has(e.id) ? 'linked to a finding' : 'no finding')} />
        ))}
      </div>
      <div className="tracker-legend">
        <span><i style={{ background: 'var(--ok)' }} />No finding</span>
        <span><i style={{ background: 'var(--warn)' }} />Linked to a finding</span>
        <span><i style={{ background: 'var(--danger)' }} />Changed after sealing</span>
      </div>
    </div>
  );
}
