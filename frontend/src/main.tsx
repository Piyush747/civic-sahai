import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { BrowserRouter, Link, NavLink, Navigate, Outlet, Route, Routes } from 'react-router-dom';
import { AdminLayout, AdminPlaceholder, AdminWorkflow } from './admin';
import { AdminCityOverview } from './admin-city';
import { AdminZoneOverview } from './admin-zone';
import { AdminIncidentDetails } from './admin-incident';
import { AdminIncidentList } from './admin-incident-list';
import { AdminComplaintDetails } from './admin-complaint';
import { AdminAllocationReview } from './admin-allocation';
import { citizenApi } from './api';
import { ComplaintForm, ComplaintDetail, ComplaintListPage, Home } from './pages';
import { citizenPaths, DEFAULT_CITIZEN_USER_ID, useCitizenPaths, useCitizenUserId } from './paths';
import './styles.css';

const queryClient = new QueryClient();

const fallbackHelp = {
  title: 'Need help?',
  description:
    'Call the civic helpline if you have questions about a report, or if location or issue details need to be corrected.',
  phoneLabel: 'Civic helpline',
  phoneNumber: '1800-123-1916',
  hours: 'Monday to Saturday, 8:00 AM – 8:00 PM',
};

function telHref(phoneNumber: string) {
  return `tel:${phoneNumber.replace(/\D/g, '')}`;
}

function CitizenLayout() {
  const paths = useCitizenPaths();
  const userId = useCitizenUserId();
  const homepage = useQuery({
    queryKey: ['citizen-homepage', userId],
    queryFn: () => citizenApi.homepage(userId),
  });
  const header = homepage.data?.header;
  const help = homepage.data?.helpSection ?? fallbackHelp;
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
      <footer id="help" className="site-footer">
        <div className="help-block">
          <h2>{help.title}</h2>
          <p>{help.description}</p>
          <p className="help-phone">
            <span>{help.phoneLabel}</span>
            <a href={telHref(help.phoneNumber)}>{help.phoneNumber}</a>
          </p>
          <p className="help-hours">{help.hours}</p>
        </div>
        <p className="footer-tagline">
          {homepage.data?.footerText ?? 'Civic SahAI · Clear reports. Better civic services.'}
        </p>
      </footer>
    </>
  );
}

const defaultCitizenHome = citizenPaths(DEFAULT_CITIZEN_USER_ID).home;

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to={defaultCitizenHome} replace />} />
      <Route path="/admin/workflow" element={<AdminWorkflow />} />
      <Route path="/admin/home" element={<AdminCityOverview />} />
      <Route path="/admin/city-overview" element={<Navigate to="/admin/home" replace />} />
      <Route path="/admin/zone-overview" element={<AdminZoneOverview />} />
      <Route path="/admin/incident-list" element={<AdminIncidentList />} />
      <Route path="/admin/incident-details/:incidentId" element={<AdminIncidentDetails />} />
      <Route path="/admin/incident-details" element={<AdminIncidentDetails />} />
      <Route path="/admin/complaint-details/:complaintId" element={<AdminComplaintDetails />} />
      <Route path="/admin/complaint-details" element={<AdminComplaintDetails />} />
      <Route path="/admin/allocation-review" element={<AdminAllocationReview />} />
      <Route path="/admin" element={<AdminLayout />}>
        <Route index element={<Navigate to="/admin/home" replace />} />
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
