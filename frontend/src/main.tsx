import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Link, Route, Routes } from 'react-router-dom';
import { ComplaintForm, ComplaintDetail, ComplaintListPage, Home } from './pages';
import './styles.css';

const queryClient = new QueryClient();
function Layout() { return <><header><Link className="brand" to="/">Civic SahAI</Link><nav><Link to="/complaints">Reports</Link><Link className="button small" to="/complaints/new">Report an issue</Link></nav></header><main><Routes><Route path="/" element={<Home />} /><Route path="/complaints" element={<ComplaintListPage />} /><Route path="/complaints/new" element={<ComplaintForm />} /><Route path="/complaints/:id" element={<ComplaintDetail />} /></Routes></main><footer>Built for clearer, faster civic action.</footer></>; }
createRoot(document.getElementById('root')!).render(<StrictMode><QueryClientProvider client={queryClient}><BrowserRouter><Layout /></BrowserRouter></QueryClientProvider></StrictMode>);

