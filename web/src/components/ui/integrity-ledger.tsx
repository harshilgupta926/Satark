'use client';

import { useEffect, useState } from 'react';
import { RotateCcw } from 'lucide-react';

type Row = { id: string; text: string; altered: string; sealed: string; current: string };

// Synthetic records. Each "altered" version changes only a word or two,
// which is enough to change the SHA-256 seal completely.
const RECORDS = [
  { id: 'EV-001', text: 'Lookalike-domain email asks Priya to verify her password', altered: 'Internal email asks Priya to verify her password' },
  { id: 'EV-002', text: 'Sign-in from a new browser in an unfamiliar location', altered: 'Sign-in from a known browser in an unfamiliar location' },
  { id: 'EV-003', text: 'New authenticator app registered on the account', altered: 'No authenticator change on the account' },
  { id: 'EV-004', text: 'Inbox rule forwards all mail to an external address', altered: 'Inbox rule forwards all mail to an internal address' },
];

async function sha256(text: string) {
  const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return Array.from(new Uint8Array(bytes)).map(b => b.toString(16).padStart(2, '0')).join('');
}
const short = (hash: string) => hash ? hash.slice(0, 10) + '…' + hash.slice(-6) : '··········';

/** Hero demo: real SHA-256 seals, computed in the browser. Change a record and its seal breaks. */
export default function IntegrityLedger() {
  const [rows, setRows] = useState<Row[]>(() => RECORDS.map(r => ({ ...r, sealed: '', current: '' })));
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let live = true;
    Promise.all(RECORDS.map(async r => {
      const seal = await sha256(JSON.stringify({ id: r.id, summary: r.text }));
      return { ...r, sealed: seal, current: seal };
    })).then(sealed => { if (live) { setRows(sealed); setReady(true); } }).catch(() => undefined);
    return () => { live = false; };
  }, []);

  async function toggle(id: string) {
    const next = await Promise.all(rows.map(async row => {
      if (row.id !== id) return row;
      const changed = row.current === row.sealed;
      const text = changed ? row.altered : RECORDS.find(r => r.id === id)!.text;
      return { ...row, text, current: await sha256(JSON.stringify({ id: row.id, summary: text })) };
    }));
    setRows(next);
  }
  async function restore() {
    setRows(rows.map(row => ({ ...row, text: RECORDS.find(r => r.id === row.id)!.text, current: row.sealed })));
  }

  const changed = rows.filter(r => r.current !== r.sealed);
  return (
    <section className="ledger border-beam" aria-labelledby="ledger-title">
      <div className="ledger-head">
        <div>
          <strong id="ledger-title">Evidence ledger</strong>
          <small>Synthetic case · sealed with SHA-256 in your browser</small>
        </div>
        <span className={changed.length ? 'risk-chip' : 'safe-chip'}>{changed.length ? 'Integrity broken' : 'All seals intact'}</span>
      </div>
      <ul className="ledger-rows">
        {rows.map(row => {
          const isChanged = row.current !== row.sealed;
          return (
            <li key={row.id} className={'ledger-row' + (isChanged ? ' is-changed' : '')}>
              <span className="ledger-id">{row.id}</span>
              <span className="ledger-text">{row.text}</span>
              <span className="ledger-hash" aria-label={isChanged ? 'Seal no longer matches' : 'Seal matches'}>
                {isChanged ? <><del>{short(row.sealed)}</del>{short(row.current)}</> : short(row.sealed)}
              </span>
              <span className="ledger-state">
                <button type="button" className="mini-btn" disabled={!ready} onClick={() => { void toggle(row.id); }}
                  aria-label={(isChanged ? 'Undo the edit to ' : 'Edit ') + row.id}>
                  {isChanged ? 'Undo' : 'Edit'}
                </button>
              </span>
            </li>
          );
        })}
      </ul>
      <div className="ledger-foot">
        <p aria-live="polite" key={changed.length} className="verdict-flash">
          {changed.length
            ? <><b className="bad">{changed.map(r => r.id).join(', ')} changed after sealing.</b> FIRSTLIGHT sets these aside before drawing findings.</>
            : <><b>{rows.length} of {rows.length} seals verified.</b> Try editing a record.</>}
        </p>
        {changed.length > 0 && <button type="button" className="mini-btn" onClick={() => { void restore(); }}><RotateCcw size={13} aria-hidden="true" /> Restore</button>}
      </div>
    </section>
  );
}
