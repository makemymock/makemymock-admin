import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { authService } from '../../services/authService';
import { tokenStorage } from '../../utils/token';
import styles from './AdminShell.module.css';

// Inline icons keep us off icon-font dependencies.
const Icon = {
  Home: (p) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
         strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M3 11l9-8 9 8" /><path d="M5 10v10h14V10" />
    </svg>
  ),
  Users: (p) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
         strokeLinecap="round" strokeLinejoin="round" {...p}>
      <circle cx="9" cy="8" r="4" />
      <path d="M2 21c1-4 4-6 7-6s6 2 7 6" />
      <circle cx="17" cy="9" r="3" /><path d="M22 21c-.6-2.5-2.4-4-5-4" />
    </svg>
  ),
  Mail: (p) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
         strokeLinecap="round" strokeLinejoin="round" {...p}>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="M3 7l9 6 9-6" />
    </svg>
  ),
  Book: (p) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
         strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M4 4h13a3 3 0 0 1 3 3v13" />
      <path d="M4 4v16h13a3 3 0 0 0 3-3" />
      <path d="M8 8h7M8 12h7" />
    </svg>
  ),
  Trophy: (p) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
         strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M8 21h8" /><path d="M12 17v4" />
      <path d="M7 4h10v5a5 5 0 0 1-10 0V4z" />
      <path d="M17 5h3v3a3 3 0 0 1-3 3" />
      <path d="M7 5H4v3a3 3 0 0 0 3 3" />
    </svg>
  ),
  Logout: (p) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
         strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M10 17l5-5-5-5" /><path d="M15 12H4" /><path d="M21 4v16" />
    </svg>
  ),
};

const NAV = [
  { to: '/dashboard', label: 'Dashboard', Icon: Icon.Home, end: true },
  { to: '/users', label: 'Users', Icon: Icon.Users },
  { to: '/email', label: 'Email', Icon: Icon.Mail },
  { to: '/questions', label: 'Questions', Icon: Icon.Book },
  { to: '/contests', label: 'Contests', Icon: Icon.Trophy },
];

const AdminShell = () => {
  const navigate = useNavigate();
  const user = tokenStorage.getUser();
  const initials = (user?.email || 'A').slice(0, 1).toUpperCase();

  const handleLogout = () => {
    authService.logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar} aria-label="Primary">
        <div className={styles.brand}>
          <span className={styles.brandMark}>MM</span>
          <div className={styles.brandText}>
            <p className={styles.brandTitle}>MakeMyMock</p>
            <p className={styles.brandSub}>Admin Console</p>
          </div>
        </div>

        <nav className={styles.nav}>
          {NAV.map(({ to, label, Icon: I, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.navItemActive : ''}`
              }
            >
              <I className={styles.navIcon} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className={styles.sidebarFooter}>
          <div className={styles.userChip}>
            <span className={styles.avatar}>{initials}</span>
            <div className={styles.userText}>
              <p className={styles.userName}>Admin</p>
              <p className={styles.userEmail}>{user?.email || '—'}</p>
            </div>
          </div>
          <button type="button" className={styles.logoutBtn} onClick={handleLogout}>
            <Icon.Logout className={styles.navIcon} />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
};

export default AdminShell;
