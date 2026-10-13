import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Link, NavLink, Outlet, Route, Routes } from 'react-router-dom';
import { AdminLayout, AdminOverview, AdminPlaceholder } from './admin';
import { ComplaintForm, ComplaintDetail, ComplaintListPage, Home } from './pages';
import './styles.css';

const queryClient = new QueryClient();

function CitizenLayout() {
  return (
    <>
      <header className="site-header">
        <div className="brand-block">
          <Link className="brand" to="/">
            Civic SahAI
          </Link>
          <span className="portal-badge">Citizen portal</span>
        </div>
        <nav>
          <NavLink to="/complaints" className={({ isActive }) => (isActive ? 'nav-active' : undefined)}>
            My complaints
          </NavLink>
          <Link to="/admin" className="nav-muted">
            Admin
          </Link>
          <a href="#help" className="nav-muted">
            Help
          </a>
          <span className="avatar" aria-hidden>
            PJ
          </span>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
      <footer id="help">Civic SahAI · Clear reports. Better civic services.</footer>
    </>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/admin" element={<AdminLayout />}>
        <Route index element={<AdminOverview />} />
        <Route path="incidents" element={<AdminPlaceholder title="Incidents" />} />
        <Route path="clusters" element={<AdminPlaceholder title="Incident clusters" />} />
        <Route path="allocation" element={<AdminPlaceholder title="Resource allocation" />} />
        <Route path="zones" element={<AdminPlaceholder title="Zones & burden" />} />
        <Route path="teams" element={<AdminPlaceholder title="Teams & capacity" />} />
        <Route path="reports" element={<AdminPlaceholder title="Reports & analytics" />} />
      </Route>
      <Route element={<CitizenLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/complaints" element={<ComplaintListPage />} />
        <Route path="/complaints/new" element={<ComplaintForm />} />
        <Route path="/complaints/:id" element={<ComplaintDetail />} />
      </Route>
    </Routes>
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
