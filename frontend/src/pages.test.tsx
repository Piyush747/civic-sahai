import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { expect, test, vi } from 'vitest';
import { ComplaintDetail, ComplaintForm, Home } from './pages';

const { homepageMock, complaintMock, complaintFormMock, locationSearchMock, locationStatusMock } = vi.hoisted(() => {
  const homepage = {
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
  summaryCards: [
    { key: 'TOTAL', title: 'Total complaints', count: 0, description: 'All reports you submitted' },
    { key: 'IN_PROGRESS', title: 'In progress', count: 0, description: 'Teams are working on these' },
    { key: 'RESOLVED', title: 'Resolved', count: 0, description: 'Issues marked as fixed' },
    { key: 'NEEDS_ATTENTION', title: 'Needs attention', count: 0, description: 'Updates or details requested' },
  ],
  complaintsSection: {
    title: 'Your recent complaints',
    description: 'Track each report and see what happens next.',
    viewAllLabel: 'View all complaints',
    filters: [{ key: 'ALL', label: 'All complaints' }],
    tableHeaders: ['ISSUE', 'LOCATION', 'REPORTED', 'STATUS'],
    viewActionLabel: 'View',
  },
  complaints: [],
  informationNote: 'Your reports help your local teams understand what needs attention.',
  helpSection: {
    title: 'Need help?',
    description:
      'Call the civic helpline if you have questions about a report, or if location or issue details need to be corrected.',
    phoneLabel: 'Civic helpline',
    phoneNumber: '1800-123-1916',
    hours: 'Monday to Saturday, 8:00 AM – 8:00 PM',
  },
  footerText: 'Civic SahAI · Clear reports. Better civic services.',
};
  return {
    homepageMock: vi.fn().mockResolvedValue(homepage),
    complaintFormMock: vi.fn().mockResolvedValue({
      breadcrumbs: [{ label: 'My complaints' }, { label: 'Register a complaint' }],
      form: {
        sectionTitle: 'Issue details',
        fields: [],
        mapPreview: { placeholder: 'Map preview' },
        privacyNote: 'Avoid sensitive details.',
        submitButton: { label: 'Submit complaint', action: 'SUBMIT_COMPLAINT' },
        cancelButton: { label: 'Cancel', action: 'CANCEL' },
      },
      nextSteps: { title: 'What happens next', steps: [] },
    }),
    locationSearchMock: vi.fn().mockResolvedValue({ places: [] }),
    locationStatusMock: vi.fn().mockResolvedValue({ inServiceArea: true, cityName: 'Chennai', zoneId: 'zone_01', zoneName: 'Central' }),
    complaintMock: vi.fn().mockResolvedValue({
      pageContent: {
        introText: 'Track the status and updates for your submitted complaint.',
        breadcrumb: { parentLabel: 'My complaints', currentLabel: 'CS-2026-0001' },
        similarComplaintsTitle: 'Similar complaints',
        similarComplaintsDescription: 'Grouped with your complaint.',
        sameIssueLabel: 'SAME ISSUE',
        privateReporterLabel: 'Reporter details are private',
        informationSection: {
          title: 'Need to add information?',
          description: 'Contact the civic team if the location or issue details need to be corrected.',
          actionLabel: 'Contact civic team',
          action: 'CONTACT_CIVIC_TEAM',
        },
      },
      complaint: {
        complaintId: 'complaint_photo',
        referenceNumber: 'CS-2026-0001',
        title: 'Pothole near bus stop',
        categoryLabel: 'Road damage',
        location: { address: 'Anna Salai' },
        description: 'Large pothole causing traffic issues near the bus stop.',
        status: 'SUBMITTED',
        statusLabel: 'REPORTED',
        reportedAt: '2026-10-01T09:00:00Z',
        lastUpdatedAt: '2026-10-01T09:00:00Z',
        attachments: [
          {
            attachmentId: 'att-1',
            contentType: 'image/png',
            url: 'http://localhost:8000/api/v1/complaint-images/abc123.png',
          },
        ],
      },
      progressSection: { title: 'Progress updates', events: [] },
      similarComplaints: [],
    }),
  };
});

vi.mock('./api', () => ({
  citizenApi: {
    homepage: homepageMock,
    complaint: complaintMock,
    complaints: vi.fn(),
    complaintForm: complaintFormMock,
    createComplaint: vi.fn(),
    locationSearch: locationSearchMock,
    locationStatus: locationStatusMock,
  },
  complaintsApi: { uploadImage: vi.fn() },
}));

vi.mock('leaflet', () => {
  const layer = () => {
    const item = {
      addTo: () => item,
      on: () => item,
      bindTooltip: () => item,
      setLatLng: () => item,
      addLayer: () => item,
      clearLayers: () => undefined,
    };
    return item;
  };
  return {
    default: {
      map: () => {
        const map = {
          setView: () => map,
          on: () => map,
          remove: () => undefined,
          invalidateSize: () => undefined,
          panTo: () => undefined,
        };
        return map;
      },
      tileLayer: layer,
      circleMarker: layer,
      layerGroup: layer,
    },
  };
});

function renderHome() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

test('complaint detail loads attached photos for the path user', async () => {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/citizen/complaints/complaint_photo/usr-id=101']}>
        <Routes>
          <Route path="/citizen/complaints/:id/:userRef" element={<ComplaintDetail />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );

  const photo = await screen.findByRole('img', { name: 'Complaint photo' });
  expect(photo).toHaveAttribute('src', 'http://localhost:8000/api/v1/complaint-images/abc123.png');
  expect(complaintMock).toHaveBeenCalledWith('101', 'complaint_photo');
});

test('home dashboard presents the report action from the Figma design', async () => {
  renderHome();
  expect(await screen.findByRole('heading', { name: /good afternoon, piyush/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /report an issue/i })).toHaveAttribute(
    'href',
    '/citizen/complaints/new/usr-id=1001',
  );
  expect(await screen.findByText(/your recent complaints/i)).toBeInTheDocument();
  expect(homepageMock).toHaveBeenCalledWith('1001');
});

test('complaint form requires a photo before submit', async () => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const view = render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/citizen/complaints/new/usr-id=user_citizen_01']}>
        <Routes>
          <Route path="/citizen/complaints/new/:userRef" element={<ComplaintForm />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );

  const submit = await screen.findByRole('button', { name: /submit complaint/i });
  await waitFor(() => expect(submit).toBeEnabled());
  expect(screen.getByText(/photos \*/i)).toBeInTheDocument();
  fireEvent.click(submit);
  expect(await screen.findByText(/add at least one photo/i)).toBeInTheDocument();
  view.unmount();
});

test('complaint form searches places as the location is typed', async () => {
  locationSearchMock.mockResolvedValue({
    places: [
      {
        name: 'Marina Beach',
        label: 'Marina Beach, Chennai',
        latitude: 13.05,
        longitude: 80.2824,
      },
    ],
  });
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/citizen/complaints/new/usr-id=user_citizen_01']}>
        <Routes>
          <Route path="/citizen/complaints/new/:userRef" element={<ComplaintForm />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );

  expect(screen.queryByRole('heading', { name: 'Landmarks' })).not.toBeInTheDocument();
  expect(screen.queryByRole('heading', { name: 'Nearby places' })).not.toBeInTheDocument();
  fireEvent.change(screen.getByPlaceholderText(/street, area, or place/i), { target: { value: 'Marina' } });
  const match = await screen.findByRole('button', { name: /marina beach, chennai/i });
  fireEvent.click(match);
  expect(screen.getByPlaceholderText(/street, area, or place/i)).toHaveValue('Marina Beach, Chennai');
  expect(document.querySelector('input[name="latitude"]')).toHaveValue('13.05');
  expect(screen.queryByRole('button', { name: /marina beach, chennai/i })).not.toBeInTheDocument();
});
