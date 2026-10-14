import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { expect, test, vi } from 'vitest';
import { ComplaintDetail, Home } from './pages';

const { homepageMock, complaintMock } = vi.hoisted(() => {
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
  footerText: 'Civic SahAI · Clear reports. Better civic services.',
};
  return {
    homepageMock: vi.fn().mockResolvedValue(homepage),
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
    complaintForm: vi.fn(),
    createComplaint: vi.fn(),
  },
  complaintsApi: { uploadImage: vi.fn() },
}));

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
    '/citizen/complaints/new/usr-id=101',
  );
  expect(await screen.findByText(/your recent complaints/i)).toBeInTheDocument();
  expect(homepageMock).toHaveBeenCalledWith('101');
});
