export const categories = ['ROAD_DAMAGE', 'WASTE_MANAGEMENT', 'STREETLIGHT', 'WATER_SUPPLY', 'DRAINAGE', 'PUBLIC_SAFETY', 'OTHER'] as const;
export type Category = typeof categories[number];
export type Status = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED';
export type ComplaintCreate = {
  title: string;
  description: string;
  category: Category;
  zone_id: string;
  location: { latitude: number; longitude: number; address: string };
  image_ids: string[];
};
export type Complaint = ComplaintCreate & {
  id: string;
  status: Status;
  priority_score: number | null;
  created_at: string;
  updated_at: string;
};
export type ComplaintList = { items: Complaint[]; skip: number; limit: number; total: number };

export type IncidentStatus = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED';
export type Incident = {
  id: string;
  city_id: string;
  zone_id: string;
  category: Category;
  title: string;
  description: string;
  status: IncidentStatus;
  priority_score: number | null;
  complaint_count: number;
  created_at: string;
  updated_at: string;
};
export type IncidentList = { items: Incident[]; total: number };

export type DashboardSummary = {
  open_incidents: number;
  in_progress_incidents: number;
  resolved_incidents: number;
  waiting_too_long_incidents: number;
};

export type CityOverview = {
  summary: DashboardSummary;
  zone_pressure: { zone_id: string; zone_name: string; open_incidents: number; available_teams: number; deployed_teams: number; total_teams: number; pressure_level: string; boundary: Record<string, unknown> | null }[];
  incident_trends: { date: string; reported: number; resolved: number }[];
  period: string | null;
  from_date: string;
  to_date: string;
  timezone: string;
  data_as_of: string;
};

export type ZoneOverview = {
  data: {
    zone: { id: string; name: string; city_id: string; pressure_level: string };
    summary: DashboardSummary;
    incident_types: { incident_type_id: string; name: string; incident_count: number }[];
    incident_trends: { date: string; reported: number; resolved: number }[];
    assignment_queue: {
      total_count: number;
      items: { incident_id: string; incident_type_id: string; incident_type: string; priority: string | null; created_at: string; waiting_too_long: boolean }[];
    };
    response_health: { available_teams: number; deployed_teams: number; total_teams: number; pressure_level: string };
  };
  meta: { period: string | null; from_date: string; to_date: string; timezone: string; data_as_of: string };
};

export type Zone = {
  id: string;
  city_id: string;
  name: string;
  population: number;
  boundary: Record<string, unknown> | null;
  created_at: string;
};
export type ZoneList = { items: Zone[]; total: number };

export type CitizenHeader = {
  brandName: string;
  portalLabel: string;
  navigation: { label: string; action: string }[];
  profileInitials?: string;
};

export type CitizenComplaintSummary = {
  complaintId: string;
  referenceNumber: string;
  title: string;
  category: string;
  categoryLabel: string;
  categoryCode?: string;
  location: { address: string };
  reportedAt: string;
  status: string;
  statusLabel: string;
};

export type Homepage = {
  header: CitizenHeader;
  welcomeSection: {
    greeting: string;
    description: string;
    primaryAction: { label: string; subtitle: string; action: string };
  };
  summaryCards: { key: string; title: string; count: number; description: string }[];
  complaintsSection: {
    title: string;
    description: string;
    viewAllLabel: string;
    filters: { key: string; label: string }[];
    tableHeaders: string[];
    viewActionLabel: string;
  };
  complaints: CitizenComplaintSummary[];
  informationNote: string;
  helpSection: {
    title: string;
    description: string;
    phoneLabel: string;
    phoneNumber: string;
    hours: string;
  };
  footerText: string;
};

export type ComplaintFormField = {
  name: string;
  label: string;
  type: string;
  placeholder?: string;
  required: boolean;
  options?: { value: string; label: string }[];
  minLength?: number;
  maxLength?: number;
  helperText?: string;
  acceptedFormats?: string[];
  minFiles?: number;
  maxFiles?: number;
};

export type ComplaintFormContent = {
  header: CitizenHeader;
  introText: string;
  breadcrumbs: { label: string; action: string | null }[];
  pageTitle: string;
  pageDescription: string;
  form: {
    sectionTitle: string;
    fields: ComplaintFormField[];
    mapPreview: { placeholder: string };
    privacyNote: string;
    submitButton: { label: string; action: string };
    cancelButton: { label: string; action: string };
  };
  nextSteps: { title: string; steps: { step: number; text: string }[] };
};

export type LocationSearchResult = {
  name: string;
  label: string;
  latitude: number;
  longitude: number;
};

export type LocationStatus = {
  inServiceArea: boolean;
  cityName: string;
  zoneId?: string;
  zoneName?: string;
};

export type CitizenComplaintCreated = {
  complaintId: string;
  referenceNumber: string;
  message: string;
};

export type CitizenComplaintCreate = {
  category: string;
  description: string;
  location: { address: string; landmark?: string; latitude: number; longitude: number };
  attachments: { fileId: string }[];
};

export type CitizenComplaintDetail = {
  pageContent: {
    introText: string;
    breadcrumb: { parentLabel: string; currentLabel: string };
    similarComplaintsTitle: string;
    similarComplaintsDescription: string;
    sameIssueLabel: string;
    privateReporterLabel: string;
    informationSection: { title: string; description: string; actionLabel: string; action: string };
  };
  complaint: {
    complaintId: string;
    referenceNumber: string;
    title: string;
    categoryLabel: string;
    location: { address: string; landmark?: string | null };
    description: string;
    status: string;
    statusLabel: string;
    reportedAt: string;
    lastUpdatedAt: string;
    attachments: { attachmentId: string; contentType: string; url: string }[];
  };
  progressSection: {
    title: string;
    events: { eventId: string; title: string; timestamp: string; description: string; status: string }[];
  };
  similarComplaints: {
    complaintId: string;
    referenceNumber: string;
    title: string;
    location: { address: string };
    reportedAt: string;
    status: string;
    statusLabel: string;
  }[];
};

export type CitizenComplaintList = {
  pageContent: {
    introText: string;
    breadcrumb: { parentLabel: string; currentLabel: string };
    pageTitle: string;
    registerButton: { label: string; action: string };
    searchPlaceholder: string;
    filterTitle: string;
    viewDetailsLabel: string;
  };
  summary: { totalCount: number; statusCounts: { status: string; label: string; count: number }[] };
  complaints: CitizenComplaintSummary[];
  pagination: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
    hasPrevious: boolean;
    hasNext: boolean;
    displayText: string;
  };
};

