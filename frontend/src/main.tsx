import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { BrowserRouter, Link, NavLink, Navigate, Outlet, Route, Routes } from 'react-router-dom';
import { AdminLayout, AdminOverview, AdminPlaceholder } from './admin';
import { citizenApi } from './api';
import { ComplaintForm, ComplaintDetail, ComplaintListPage, Home } from './pages';
import { citizenPaths, DEFAULT_CITIZEN_USER_ID, useCitizenPaths, useCitizenUserId } from './paths';
import './styles.css';

const queryClient = new QueryClient();

function CitizenLayout() {
  const paths = useCitizenPaths();
  const userId = useCitizenUserId();
  const homepage = useQuery({
    queryKey: ['citizen-homepage', userId],
    queryFn: () => citizenApi.homepage(userId),
  });
  const header = homepage.data?.header;
  const navigation = header?.navigation ?? [
    { label: 'My complaints', action: 'VIEW_COMPLAINTS' },
    { label: 'Help', action: 'HELP' },
  ];
  return (
    <>
      <header className="site-header">
        <div className="brand-block">
          <Link className="brand" to={paths.home}>
            {header?.brandName ?? 'Civic SahAI'}
          </Link>
          <span className="portal-badge">{header?.portalLabel ?? 'Citizen portal'}</span>
        </div>
        <nav>
          {navigation.map((item) =>
            item.action === 'HELP' ? (
              <a key={item.action} href="#help" className="nav-muted">
                {item.label}
              </a>
            ) : (
              <NavLink
                key={item.action}
                to={paths.complaints}
                className={({ isActive }) => (isActive ? 'nav-active' : undefined)}
              >
                {item.label}
              </NavLink>
            ),
          )}
          <span className="avatar" aria-hidden>
            {header?.profileInitials ?? 'PJ'}
          </span>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
      <footer id="help">{homepage.data?.footerText ?? 'Civic SahAI · Clear reports. Better civic services.'}</footer>
    </>
  );
}

const defaultCitizenHome = citizenPaths(DEFAULT_CITIZEN_USER_ID).home;

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to={defaultCitizenHome} replace />} />
      <Route path="/admin" element={<AdminLayout />}>
        <Route index element={<Navigate to="home" replace />} />
        <Route path="home" element={<AdminOverview />} />
        <Route path="incidents" element={<AdminPlaceholder title="Incidents" />} />
        <Route path="clusters" element={<AdminPlaceholder title="Incident clusters" />} />
        <Route path="allocation" element={<AdminPlaceholder title="Resource allocation" />} />
        <Route path="zones" element={<AdminPlaceholder title="Zones & burden" />} />
        <Route path="teams" element={<AdminPlaceholder title="Teams & capacity" />} />
        <Route path="reports" element={<AdminPlaceholder title="Reports & analytics" />} />
      </Route>
      <Route path="/citizen" element={<CitizenLayout />}>
        <Route index element={<Navigate to={defaultCitizenHome} replace />} />
        <Route path="home/:userRef" element={<Home />} />
        <Route path="complaints/new/:userRef" element={<ComplaintForm />} />
        <Route path="complaints/:userRef" element={<ComplaintListPage />} />
        <Route path="complaints/:id/:userRef" element={<ComplaintDetail />} />
      </Route>
    </Routes>
  );
}

const rootElement = document.getElementById('root');
if (rootElement) {
  createRoot(rootElement).render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>
    </StrictMode>,
  );
}
