'use client';

import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';
import SiteHeader from '../site-header';
import { completePasswordReset } from '../../lib/satark-auth';

export default function ResetPasswordPage() {
  const [accessToken, setAccessToken] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [linkReady, setLinkReady] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.hash.slice(1));
    const token = params.get('access_token') || '';
    const type = params.get('type');
    if (type === 'recovery' && token && token.length <= 8192) {
      setAccessToken(token);
      setLinkReady(true);
    } else {
      setError('This recovery link is missing or expired. Request a new link from the sign-in page.');
    }
    // Remove credentials from the visible URL/history as soon as they are read.
    window.history.replaceState(null, '', window.location.pathname + window.location.search);
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    setNotice('');
    if (!linkReady || !accessToken) {
      setError('This recovery link is invalid or expired. Request a new one.');
      return;
    }
    if (password.length < 8 || password.length > 128) {
      setError('Use a password between 8 and 128 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('The passwords do not match.');
      return;
    }
    setBusy(true);
    try {
      await completePasswordReset(accessToken, password);
      setAccessToken('');
      setPassword('');
      setConfirmPassword('');
      setLinkReady(false);
      setNotice('Your password has been updated. You can now sign in with your new password.');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Password reset failed. Request a new recovery link.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="shell">
      <SiteHeader />
      <main id="main-content" className="container">
        <section className="auth-layout">
          <div className="auth-aside">
            <div className="eyebrow">Account recovery</div>
            <h1>Secure access, <span>restored.</span></h1>
            <p className="lead">Use the recovery link sent to your email to choose a new password. Recovery links are time-limited and can only be used while valid.</p>
            <Link className="btn btn-secondary" href="/login">Back to sign in</Link>
          </div>
          <section className="form-panel auth-card" aria-labelledby="reset-title">
            <div className="card-head"><span>Identity</span><span className="pill">Password reset</span></div>
            <h2 id="reset-title">Choose a new password</h2>
            <form onSubmit={submit}>
              <label className="field-label" htmlFor="password">New password</label>
              <input id="password" type="password" autoComplete="new-password" required minLength={8} maxLength={128} value={password} onChange={e => setPassword(e.target.value)} disabled={!linkReady || busy} />
              <label className="field-label" htmlFor="confirm-password">Confirm new password</label>
              <input id="confirm-password" type="password" autoComplete="new-password" required minLength={8} maxLength={128} value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} disabled={!linkReady || busy} />
              <button className="btn btn-primary" type="submit" disabled={!linkReady || busy}>{busy ? 'Updating…' : 'Update password'}</button>
            </form>
            {error && <p className="error-message" role="alert">{error}</p>}
            {notice && <p className="success-message" role="status">{notice}</p>}
          </section>
        </section>
      </main>
    </div>
  );
}
