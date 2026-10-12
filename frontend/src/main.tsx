import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Link, NavLink, Route, Routes } from 'react-router-dom';
import { ComplaintForm, ComplaintDetail, ComplaintListPage, Home } from './pages';
import './styles.css';

const queryClient = new QueryClient();

function Layout() {
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
          <a href="#help" className="nav-muted">
            Help
          </a>
          <span className="avatar" aria-hidden>
            PJ
          </span>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/complaints" element={<ComplaintListPage />} />
          <Route path="/complaints/new" element={<ComplaintForm />} />
          <Route path="/complaints/:id" element={<ComplaintDetail />} />
        </Routes>
      </main>
      <footer id="help">Civic SahAI · Clear reports. Better civic services.</footer>
    </>
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
