import React, { useEffect, useState } from 'react';
import { Activity, Ambulance, BusFront, ChevronRight, Gauge, LogIn, LogOut, MapPin, Menu, Moon, RefreshCw, Route, Sun, TriangleAlert, Wifi, X } from 'lucide-react';
import { api, isMock } from './services/api';
import Dashboard from './pages/Dashboard';
import Alerts from './pages/Alerts';
import CityMap from './pages/Map';
import Buses from './pages/Buses';
import Analytics from './pages/Analytics';
import AlertDetails from './pages/AlertDetails';
import Emergency from './pages/Emergency';
const navigation = [['dashboard', 'Command Center', Activity], ['map', 'City Map', MapPin], ['alerts', 'Incidents', TriangleAlert], ['buses', 'Fleet', BusFront], ['emergency', 'Emergency', Ambulance], ['analytics', 'Analytics', Gauge]];
const readRoute = () => location.hash.slice(1) || 'dashboard';
const decodeId = value => {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
};
export default function App() {
  const [route, setRoute] = useState(readRoute);
  const [revision, setRevision] = useState(0);
  const [status, setStatus] = useState({
    updated: null,
    error: ''
  });
  const [dark, setDark] = useState(true),
    [menu, setMenu] = useState(false);
  const [authenticated, setAuthenticated] = useState(false),
    [showLogin, setShowLogin] = useState(false);
  const [password, setPassword] = useState(''),
    [loginError, setLoginError] = useState(''),
    [signingIn, setSigningIn] = useState(false);
  useEffect(() => {
    const change = () => {
      setRoute(readRoute());
      setMenu(false);
    };
    window.addEventListener('hashchange', change);
    return () => window.removeEventListener('hashchange', change);
  }, []);
  useEffect(() => {
    api.getSession().then(result => setAuthenticated(result.authenticated)).catch(() => setAuthenticated(false));
  }, [revision]);
  useEffect(() => {
    setStatus({
      updated: null,
      error: ''
    });
  }, [route]);
  const navigate = value => {
    location.hash = value;
  };
  const refresh = () => setRevision(value => value + 1);
  const issueId = route.startsWith('issue/') ? decodeId(route.slice(6)) : null;
  const page = navigation.find(([key]) => key === route)?.[1] || (issueId ? 'Issue details' : 'Command Center');
  const common = {
    revision,
    onStatus: update => setStatus(previous => ({
      ...previous,
      ...update
    })),
    onSelect: id => navigate('issue/' + encodeURIComponent(id)),
    onSessionExpired: () => setAuthenticated(false)
  };
  const connection = isMock ? 'DEMO FIXTURES' : status.error ? 'UPDATES INTERRUPTED' : status.updated ? 'BACKEND CONNECTED' : 'CONNECTING';
  async function signIn(event) {
    event.preventDefault();
    setSigningIn(true);
    setLoginError('');
    try {
      const result = await api.login(password);
      setAuthenticated(result.authenticated);
      setShowLogin(false);
      setPassword('');
    } catch (error) {
      setLoginError(error.message);
    } finally {
      setSigningIn(false);
    }
  }
  async function signOut() {
    try {
      await api.logout();
      setAuthenticated(false);
    } catch (error) {
      setStatus(previous => ({
        ...previous,
        error: error.message
      }));
    }
  }
  return <div className={'app ' + (dark ? 'dark' : 'light')}>
    <aside className={'sidebar ' + (menu ? 'expanded' : '')}>
      <a className="brand" href="#dashboard"><div className="brand-mark"><Route size={23} /></div><div><strong>CODYSSEY</strong><span>URBAN INTELLIGENCE</span></div></a>
      <div className={'system-state ' + (status.error ? 'stale' : '')}><span className="pulse" /><div><strong>{connection}</strong><small>{status.updated ? 'Updated ' + status.updated.toLocaleTimeString('en-IN') : 'Waiting for city intelligence'}</small></div><Wifi size={15} /></div>
      <nav aria-label="Main navigation"><span className="nav-label">OPERATIONS</span>{navigation.map(([key, label, Icon]) => <a key={key} href={'#' + key} className={'nav-item ' + (route === key || issueId && key === 'alerts' ? 'active' : '')}><Icon size={18} /><span>{label}</span><ChevronRight size={15} className="nav-chevron" /></a>)}</nav>
      <div className="sidebar-bottom"><div className="coverage"><div className="coverage-head"><span>Reviewer prototype</span><strong>LOCAL</strong></div><p>Recorded footage · Simulated GPS</p><small>Detection, shared alerts and operator review.</small></div><div className="profile"><div className="avatar">CO</div><div><strong>CODYSSEY Ops</strong><small>{authenticated ? 'Operator signed in' : 'Observer access'}</small></div></div></div>
    </aside>
    <main className="main">
      <header className="topbar"><button className="icon-btn menu-toggle" aria-label="Toggle navigation" aria-expanded={menu} onClick={() => setMenu(!menu)}><Menu size={20} /></button><div className="mobile-brand"><Route size={20} /> CODYSSEY</div><div className="crumbs"><span>OPERATIONS</span><ChevronRight size={13} /><strong>{page.toUpperCase()}</strong></div><div className="top-actions"><button className="icon-btn" aria-label="Refresh data" onClick={refresh}><RefreshCw size={17} /></button><button className="icon-btn" aria-label="Toggle theme" onClick={() => setDark(!dark)}>{dark ? <Sun size={18} /> : <Moon size={18} />}</button><button className="secondary-btn operator-button" onClick={authenticated ? signOut : () => setShowLogin(true)}>{authenticated ? <LogOut size={16} /> : <LogIn size={16} />}<span>{authenticated ? 'Sign out' : 'Operator sign in'}</span></button></div></header>
      <section className="content">
        <div className="hero"><div><span className="eyebrow">BENGALURU · ROAD OBSERVATIONS</span><h1>{page === 'Command Center' ? <>City intelligence, <em>in motion.</em></> : page}</h1><p>{issueId ? 'Inspect the reports, review the location and record the outcome.' : 'Every bus becomes a mobile sensor. Detect locally, bring reports together, and review what needs attention.'}</p></div><div className="hero-actions"><button className="primary-btn" onClick={refresh}><RefreshCw size={16} /> Refresh intelligence</button></div></div>
        {isMock && <div className="demo-banner">Demo mode: shared fixture data. Changes stay in this browser session.</div>}
        {issueId ? <AlertDetails {...common} issueId={issueId} onBack={() => navigate('alerts')} authenticated={authenticated} onLogin={() => setShowLogin(true)} onChanged={refresh} /> : route === 'alerts' ? <Alerts {...common} /> : route === 'map' ? <CityMap {...common} /> : route === 'buses' ? <Buses {...common} /> : route === 'analytics' ? <Analytics {...common} /> : route === 'emergency' ? <Emergency {...common} /> : <Dashboard {...common} onNavigate={navigate} />}
        <footer><span>CODYSSEY · {connection.toLowerCase()}</span><span>Inference on this device · Compact alert reports · GPS sources labeled</span></footer>
      </section>
    </main>
    {showLogin && <div className="modal-backdrop" onClick={() => !signingIn && setShowLogin(false)}><section className="login-modal" role="dialog" aria-modal="true" aria-label="Operator sign in" onClick={event => event.stopPropagation()}><button className="icon-button modal-close" aria-label="Close sign in" disabled={signingIn} onClick={() => setShowLogin(false)}><X size={18} /></button><span className="eyebrow">OPERATOR ACCESS</span><h2>Sign in to review issues</h2><p>Use your local operator password to mark an issue resolved.</p><form onSubmit={signIn}><label>Operator password<input autoFocus type="password" autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} required={!isMock} /></label>{loginError && <p role="alert" className="form-error">{loginError}</p>}<button className="primary-button" disabled={signingIn}>{signingIn ? 'Signing in…' : isMock ? 'Enter demo operator mode' : 'Sign in'}</button></form></section></div>}
  </div>;
}
