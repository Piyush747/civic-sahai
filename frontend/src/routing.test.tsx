import { cleanup, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { afterEach, expect, test, vi } from 'vitest';
import { App } from './main';

vi.mock('./api', () => ({
  citizenApi: {
    homepage: vi.fn().mockResolvedValue({
      header: {
        brandName: 'Civic SahAI',
        portalLabel: 'CITIZEN PORTAL',
        navigation: [
          { label: 'My complaints', action: 'VIEW_COMPLAINTS' },
          { label: 'Help', action: 'HELP' },
        ],
        profileInitials: 'PJ',
      },
      welcomeSection: {
        greeting: 'Good afternoon, Piyush',
        description: 'Report civic issues in your area and follow their progress.',
        primaryAction: { label: 'Report an issue', subtitle: 'Takes about 2 minutes', action: 'SUBMIT_COMPLAINT' },
      },
      summaryCards: [],
      complaintsSection: {
        title: 'Your recent complaints',
        description: 'Track each report and see what happens next.',
        viewAllLabel: 'View all complaints',
        filters: [],
        tableHeaders: ['ISSUE', 'LOCATION', 'REPORTED', 'STATUS'],
        viewActionLabel: 'View',
      },
      complaints: [],
      informationNote: '',
      footerText: 'Civic SahAI · Clear reports. Better civic services.',
      helpSection: {
        title: 'Need help?',
        description:
          'Call the civic helpline if you have questions about a report, or if location or issue details need to be corrected.',
        phoneLabel: 'Civic helpline',
        phoneNumber: '1800-123-1916',
        hours: 'Monday to Saturday, 8:00 AM – 8:00 PM',
      },
    }),
    complaint: vi.fn(),
    complaints: vi.fn(),
    complaintForm: vi.fn().mockResolvedValue(undefined),
    createComplaint: vi.fn(),
    locationSearch: vi.fn().mockResolvedValue({ places: [] }),
    locationStatus: vi.fn().mockResolvedValue({ inServiceArea: true, cityName: 'Chennai' }),
  },
  complaintsApi: {
    uploadImage: vi.fn(),
  },
  incidentsApi: { list: vi.fn().mockResolvedValue({ items: [] }) },
  zonesApi: { list: vi.fn().mockResolvedValue({ items: [] }) },
  complaintImageUrl: (imageId: string) => imageId,
}));

afterEach(() => {
  cleanup();
});

function LocationProbe() {
  const { pathname } = useLocation();
  return <span data-testid="path">{pathname}</span>;
}

function renderAt(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[path]}>
        <LocationProbe />
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

test('Help scrolls to the footer helpline details', async () => {
  renderAt('/citizen/home/usr-id=101');
  expect(await screen.findByRole('link', { name: 'Help' })).toHaveAttribute('href', '#help');
  expect(document.getElementById('help')).toBeTruthy();
  expect(await screen.findByRole('heading', { name: 'Need help?' })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: '1800-123-1916' })).toHaveAttribute('href', 'tel:18001231916');
  expect(screen.getByText(/monday to saturday, 8:00 am – 8:00 pm/i)).toBeInTheDocument();
});

test('citizen home uses the usr-id path and hides the admin link', async () => {
  renderAt('/citizen/home/usr-id=101');
  expect(screen.queryByRole('link', { name: 'Admin' })).not.toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'My complaints' })).toHaveAttribute(
    'href',
    '/citizen/complaints/usr-id=101',
  );
  expect(await screen.findByRole('link', { name: /report an issue/i })).toHaveAttribute(
    'href',
    '/citizen/complaints/new/usr-id=101',
  );
});

test('the site root opens the citizen home for user 1001', async () => {
  renderAt('/');
  expect(await screen.findByRole('heading', { name: /good (morning|afternoon|evening), piyush/i })).toBeInTheDocument();
  expect(screen.getByTestId('path')).toHaveTextContent('/citizen/home/usr-id=1001');
  expect(screen.queryByRole('link', { name: 'Admin' })).not.toBeInTheDocument();
});

test('admin home is /admin/home', async () => {
  renderAt('/admin');
  expect(await screen.findByRole('heading', { name: 'City overview' })).toBeInTheDocument();
  expect(screen.getByTestId('path')).toHaveTextContent('/admin/home');
  expect(screen.getByRole('link', { name: 'Overview' })).toHaveAttribute('href', '/admin/home');
  expect(screen.getByRole('link', { name: /citizen portal/i })).toHaveAttribute(
    'href',
    '/citizen/home/usr-id=1001',
  );
});
