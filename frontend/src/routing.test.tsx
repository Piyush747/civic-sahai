import { cleanup, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { afterEach, expect, test, vi } from 'vitest';
import { adminDashboardApi, complaintsApi, incidentsApi, zonesApi } from './api';
import { App } from './main';
import type { Complaint, Incident, Zone } from './types';

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
    get: vi.fn(),
    list: vi.fn(),
  },
  incidentsApi: {
    list: vi.fn().mockResolvedValue({ items: [], total: 0 }),
    get: vi.fn(),
  },
  zonesApi: { list: vi.fn().mockResolvedValue({ items: [], total: 0 }) },
  adminDashboardApi: {
    overview: vi.fn(),
    zoneOverview: vi.fn(),
  },
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

test('admin workflow explains citizen complaint to city action', async () => {
  renderAt('/admin/workflow');
  expect(await screen.findByRole('heading', { name: 'From citizen voice to city action' })).toBeInTheDocument();
  expect(screen.getByText('Citizen reports an issue')).toBeInTheDocument();
  expect(screen.getByText('Match or create incident')).toBeInTheDocument();
  expect(screen.getByText('City sees the pressure')).toBeInTheDocument();
  expect(screen.getByText('Recommend resources')).toBeInTheDocument();
  expect(screen.getByText('Admin decides & tracks')).toBeInTheDocument();
  expect(screen.getByText('Administrator outcome')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Overview' })).toHaveAttribute('href', '/admin/home');
  expect(screen.getByRole('link', { name: 'Zones' })).toHaveAttribute('href', '/admin/zones');
  expect(screen.getByRole('link', { name: 'Resource allocation' })).toHaveAttribute('href', '/admin/allocation');
  expect(screen.getByRole('link', { name: 'Incidents' })).toHaveAttribute('href', '/admin/incidents');
  expect(screen.queryByRole('link', { name: /citizen portal/i })).not.toBeInTheDocument();
});

const eastZone: Zone = {
  id: 'east',
  city_id: 'city',
  name: 'East Zone',
  population: 1,
  boundary: null,
  created_at: '2026-10-01T00:00:00Z',
};

function incident(overrides: Partial<Incident> & Pick<Incident, 'id' | 'category' | 'status'>): Incident {
  return {
    city_id: 'city',
    zone_id: 'east',
    title: overrides.category,
    description: 'Reported by a resident',
    priority_score: 70,
    complaint_count: 2,
    created_at: '2026-10-14T09:42:00Z',
    updated_at: '2026-10-14T09:42:00Z',
    ...overrides,
  };
}

test('admin city overview is a separate Bengaluru operations page', async () => {
  vi.mocked(adminDashboardApi.overview).mockResolvedValue({
    summary: { open_incidents: 124, in_progress_incidents: 63, resolved_incidents: 48, waiting_too_long_incidents: 19 },
    zone_pressure: [
      {
        zone_id: 'east',
        zone_name: 'East Zone',
        open_incidents: 28,
        available_teams: 2,
        deployed_teams: 6,
        total_teams: 8,
        pressure_level: 'overloaded',
        boundary: null,
      },
    ],
    incident_trends: [{ date: '2026-10-01', reported: 16, resolved: 10 }],
    period: '15d',
    from_date: '2026-10-01',
    to_date: '2026-10-15',
    timezone: 'Asia/Kolkata',
    data_as_of: '2026-10-15T10:00:00Z',
  });
  renderAt('/admin/city-overview');
  expect(await screen.findByRole('heading', { name: 'What is happening across the city?' })).toBeInTheDocument();
  expect(await screen.findByText('124')).toBeInTheDocument();
  expect(screen.getByText('East Zone')).toBeInTheDocument();
  expect(screen.getByText('Are things getting better?')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'City Overview' })).toHaveAttribute('href', '/admin/home');
  expect(screen.getByRole('link', { name: 'View details →' })).toHaveAttribute('href', '/admin/zone-overview?zone=east');
});

test('admin zone overview is a separate East Zone page', async () => {
  vi.mocked(zonesApi.list).mockResolvedValue({ items: [eastZone], total: 1 });
  vi.mocked(adminDashboardApi.zoneOverview).mockResolvedValue({
    data: {
      zone: { id: 'east', name: 'East Zone', city_id: 'city', pressure_level: 'overloaded' },
      summary: { open_incidents: 28, in_progress_incidents: 12, resolved_incidents: 5, waiting_too_long_incidents: 7 },
      incident_types: [{ incident_type_id: 'ROAD_DAMAGE', name: 'Road Damage', incident_count: 8 }],
      incident_trends: [{ date: '2026-10-14', reported: 4, resolved: 1 }],
      assignment_queue: {
        total_count: 1,
        items: [
          {
            incident_id: 'INC-EAST-0248',
            incident_type_id: 'WATER_SUPPLY',
            incident_type: 'Water supply disruption',
            priority: 'critical',
            created_at: '2026-10-14T06:00:00Z',
            waiting_too_long: true,
          },
        ],
      },
      response_health: { available_teams: 2, deployed_teams: 6, total_teams: 8, pressure_level: 'overloaded' },
    },
    meta: {
      period: '15d',
      from_date: '2026-10-01',
      to_date: '2026-10-15',
      timezone: 'Asia/Kolkata',
      data_as_of: '2026-10-15T10:00:00Z',
    },
  });
  renderAt('/admin/zone-overview?zone=east');
  expect(await screen.findByRole('heading', { name: 'East Zone overview' })).toBeInTheDocument();
  expect(await screen.findByText('Most reported incidents in East Zone')).toBeInTheDocument();
  expect(screen.getByText('Incidents needing team assignment')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Review →' })).toHaveAttribute('href', '/admin/incident-details/INC-EAST-0248');
  expect(screen.getByRole('link', { name: 'Zones' })).toHaveAttribute('href', '/admin/zone-overview');
  expect(screen.getByRole('link', { name: 'City Overview' })).toHaveAttribute('href', '/admin/home');
});

test('admin incident details is a separate road-damage page', async () => {
  vi.mocked(zonesApi.list).mockResolvedValue({ items: [eastZone], total: 1 });
  vi.mocked(incidentsApi.get).mockResolvedValue(
    incident({
      id: 'INC-EAST-0248',
      category: 'ROAD_DAMAGE',
      status: 'OPEN',
      title: 'Road damage near the bus stop',
      description: 'Pothole / damaged road surface reported by nearby residents.',
      complaint_count: 8,
    }),
  );
  renderAt('/admin/incident-details/INC-EAST-0248');
  expect(await screen.findByRole('heading', { name: 'Incident details' })).toBeInTheDocument();
  expect(await screen.findByText('INC-EAST-0248')).toBeInTheDocument();
  expect(screen.getByText('Individual complaints')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /back to east zone/i })).toHaveAttribute('href', '/admin/zone-overview?zone=east');
  expect(screen.getByRole('link', { name: 'Incidents' })).toHaveAttribute('href', '/admin/incident-list');
});

test('admin complaint details shows the original citizen submission', async () => {
  const complaint: Complaint = {
    id: 'CS-1042',
    title: 'Road damage',
    description: 'There is a deep pothole near the bus stop. Vehicles are swerving around it.',
    category: 'ROAD_DAMAGE',
    location: { latitude: 12.9876, longitude: 77.6543, address: 'East Zone bus stop' },
    zone_id: 'east',
    status: 'OPEN',
    priority_score: 70,
    created_at: '2026-10-14T05:12:00Z',
    updated_at: '2026-10-14T05:12:00Z',
    image_ids: [],
  };
  vi.mocked(complaintsApi.get).mockResolvedValue(complaint);
  vi.mocked(zonesApi.list).mockResolvedValue({ items: [eastZone], total: 1 });
  renderAt('/admin/complaint-details/CS-1042');
  expect(await screen.findByRole('heading', { name: 'Citizen complaint details' })).toBeInTheDocument();
  expect(await screen.findByText(/deep pothole near the bus stop/i)).toBeInTheDocument();
  expect(screen.getByText('Open')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /back to incidents/i })).toHaveAttribute('href', '/admin/incident-list');
});

test('admin allocation review shows the East Zone recommendation', async () => {
  renderAt('/admin/allocation-review');
  expect(await screen.findByRole('heading', { name: 'Review resource allocation recommendation' })).toBeInTheDocument();
  expect(screen.getByText(/move 2 road-maintenance crew members/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /accept recommendation/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Reject' })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: 'Resource Allocation' })).toHaveAttribute('href', '/admin/allocation-review');
});

const listedIncidents: Incident[] = [
  incident({ id: 'INC-EZ-0248', category: 'ROAD_DAMAGE', status: 'OPEN', title: 'Road damage near East Zone Bus Stop' }),
  incident({ id: 'INC-EZ-0243', category: 'ROAD_DAMAGE', status: 'IN_PROGRESS', title: 'Road surface damage' }),
  incident({ id: 'INC-EZ-0239', category: 'ROAD_DAMAGE', status: 'OPEN', title: 'Pothole cluster on service lane', priority_score: 40 }),
  incident({ id: 'INC-EZ-0216', category: 'ROAD_DAMAGE', status: 'IN_PROGRESS', title: 'Road damage near school crossing', priority_score: 40 }),
  incident({ id: 'INC-EZ-0231', category: 'WASTE_MANAGEMENT', status: 'IN_PROGRESS', title: 'Garbage not collected', priority_score: 40 }),
  incident({ id: 'INC-EZ-0209', category: 'WASTE_MANAGEMENT', status: 'RESOLVED', title: 'Overflowing community waste point', priority_score: 10 }),
  incident({ id: 'INC-EZ-0228', category: 'STREETLIGHT', status: 'RESOLVED', title: 'Streetlight outage', priority_score: 10 }),
  incident({ id: 'INC-EZ-0222', category: 'WATER_SUPPLY', status: 'OPEN', title: 'Water supply disruption' }),
];

function mockEastZoneIncidents() {
  vi.mocked(zonesApi.list).mockResolvedValue({ items: [eastZone], total: 1 });
  vi.mocked(incidentsApi.list).mockResolvedValue({ items: listedIncidents, total: listedIncidents.length });
}

test('admin incident list shows East Zone records', async () => {
  mockEastZoneIncidents();
  renderAt('/admin/incident-list?zone=east');
  expect(await screen.findByRole('heading', { name: 'East Zone incidents' })).toBeInTheDocument();
  expect(screen.getByText('INC-EZ-0248')).toBeInTheDocument();
  expect(screen.getByText('Showing 8 of 8 incidents')).toBeInTheDocument();
  expect(screen.getAllByRole('link', { name: 'View →' })[0]).toHaveAttribute('href', '/admin/incident-details/INC-EZ-0248');
  expect(screen.getByRole('link', { name: 'Incidents' })).toHaveAttribute('href', '/admin/incident-list');
});

test('road damage filter shows the four matching East Zone incidents', async () => {
  mockEastZoneIncidents();
  renderAt('/admin/incident-list?zone=east&type=road-damage');
  expect(await screen.findByRole('combobox', { name: /incident type/i })).toHaveValue('road-damage');
  expect(await screen.findByText('INC-EZ-0248')).toBeInTheDocument();
  expect(screen.getByText('INC-EZ-0216')).toBeInTheDocument();
  expect(screen.queryByText('INC-EZ-0231')).not.toBeInTheDocument();
  expect(screen.getByText('Showing road damage reports in East Zone · select an incident to view full details')).toBeInTheDocument();
  expect(screen.getByText('Showing 4 matching incidents')).toBeInTheDocument();
});

test('garbage filter shows the two matching East Zone incidents', async () => {
  mockEastZoneIncidents();
  renderAt('/admin/incident-list?zone=east&type=garbage');
  expect(await screen.findByRole('combobox', { name: /incident type/i })).toHaveValue('garbage');
  expect(await screen.findByText('INC-EZ-0231')).toBeInTheDocument();
  expect(screen.getByText('INC-EZ-0209')).toBeInTheDocument();
  expect(screen.queryByText('INC-EZ-0248')).not.toBeInTheDocument();
  expect(screen.getByText('Showing garbage not collected reports in East Zone · select an incident to view full details')).toBeInTheDocument();
  expect(screen.getByText('Showing 2 matching incidents')).toBeInTheDocument();
});

test('streetlight filter shows the one matching East Zone incident', async () => {
  mockEastZoneIncidents();
  renderAt('/admin/incident-list?zone=east&type=streetlight');
  expect(await screen.findByRole('combobox', { name: /incident type/i })).toHaveValue('streetlight');
  expect(await screen.findByText('INC-EZ-0228')).toBeInTheDocument();
  expect(screen.queryByText('INC-EZ-0248')).not.toBeInTheDocument();
  expect(screen.getByText('Showing streetlight outage reports in East Zone · select an incident to view full details')).toBeInTheDocument();
  expect(screen.getByText('Showing 1 matching incident')).toBeInTheDocument();
});

test('water supply filter shows the one matching East Zone incident', async () => {
  mockEastZoneIncidents();
  renderAt('/admin/incident-list?zone=east&type=water');
  expect(await screen.findByRole('combobox', { name: /incident type/i })).toHaveValue('water');
  expect(await screen.findByText('INC-EZ-0222')).toBeInTheDocument();
  expect(screen.queryByText('INC-EZ-0228')).not.toBeInTheDocument();
  expect(screen.getByText('Showing water supply disruption reports in East Zone · select an incident to view full details')).toBeInTheDocument();
  expect(screen.getByText('Showing 1 matching incident')).toBeInTheDocument();
});

test('admin home is the Figma city overview', async () => {
  renderAt('/admin');
  expect(await screen.findByRole('heading', { name: 'What is happening across the city?' })).toBeInTheDocument();
  expect(screen.getByTestId('path')).toHaveTextContent('/admin/home');
  expect(screen.getByRole('link', { name: 'City Overview' })).toHaveAttribute('href', '/admin/home');
});
