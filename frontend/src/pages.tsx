import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { complaintsApi } from './api';
import { categories, type Category, type Complaint, type Status } from './types';

const registerSchema = z.object({
  category: z.enum(categories, {
    errorMap: () => ({ message: 'Select an issue category' }),
  }),
  description: z.string().min(10, 'Please add more detail'),
  address: z.string().min(3, 'Add a street, area, or landmark'),
  zone_id: z.string().min(1, 'Zone is required'),
  latitude: z.coerce.number().min(-90).max(90),
  longitude: z.coerce.number().min(-180).max(180),
});
type RegisterFormValues = z.infer<typeof registerSchema>;

function titleFromDescription(description: string) {
  const line = description.trim().split(/\n/)[0] ?? description.trim();
  return line.length > 160 ? `${line.slice(0, 157)}…` : line;
}

type StatusFilter = 'all' | 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'NEEDS_ATTENTION';
const PAGE_SIZE = 5;

const categoryInitials: Record<Category, string> = {
  ROAD_DAMAGE: 'RD',
  WASTE: 'WM',
  WATER_SUPPLY: 'WS',
  STREETLIGHT: 'SL',
  DRAINAGE: 'DR',
  OTHER: 'OT',
};

const categoryDisplay: Record<Category, string> = {
  ROAD_DAMAGE: 'Road damage',
  WASTE: 'Waste management',
  WATER_SUPPLY: 'Water supply',
  STREETLIGHT: 'Streetlight',
  DRAINAGE: 'Drainage',
  OTHER: 'Other',
};

/** Map API status to Figma status labels. CLOSED stands in for "Needs attention" until the API has that state. */
function displayStatus(status: Status): { key: string; text: string } {
  if (status === 'IN_PROGRESS') return { key: 'in-progress', text: 'In progress' };
  if (status === 'RESOLVED') return { key: 'resolved', text: 'Resolved' };
  if (status === 'CLOSED') return { key: 'needs-attention', text: 'Needs attention' };
  return { key: 'reported', text: 'Reported' };
}

function complaintRef(id: string, createdAt?: string) {
  const year = createdAt ? new Date(createdAt).getFullYear() : new Date().getFullYear();
  const digits = id.replace(/\D/g, '');
  const short = (digits.slice(-4) || id.slice(0, 4)).padStart(4, '0').toUpperCase();
  return `CS-${year}-${short}`;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

function formatTimelineStamp(iso: string) {
  const date = new Date(iso);
  const day = date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
  const time = date.toLocaleTimeString('en-GB', { hour: 'numeric', minute: '2-digit', hour12: true });
  return `${day} · ${time}`;
}

function progressTimeline(item: Complaint) {
  const created = formatTimelineStamp(item.created_at);
  const updated = formatTimelineStamp(item.updated_at);
  const steps = [
    {
      title: 'Report received',
      stamp: created,
      description: 'Your complaint was submitted.',
    },
    {
      title: 'Reviewed by the team',
      stamp: created,
      description: 'The issue was reviewed.',
    },
    {
      title: 'Team assigned',
      stamp: updated,
      description: 'A civic team was assigned.',
    },
    {
      title: item.status === 'RESOLVED' ? 'Resolved' : 'Work in progress',
      stamp: updated,
      description:
        item.status === 'RESOLVED'
          ? 'The issue has been marked as fixed.'
          : item.status === 'CLOSED'
            ? 'More information or follow-up may be needed.'
            : 'The team has started work.',
    },
  ];
  const activeIndex =
    item.status === 'OPEN' ? 0 : item.status === 'RESOLVED' ? 4 : 3;
  return steps.map((step, index) => ({
    ...step,
    state: index < activeIndex ? 'done' : index === activeIndex ? 'current' : 'upcoming',
  }));
}

function greetingForNow() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

function matchesFilter(item: Complaint, filter: StatusFilter) {
  if (filter === 'all') return true;
  if (filter === 'NEEDS_ATTENTION') return item.status === 'CLOSED';
  if (filter === 'OPEN') return item.status === 'OPEN';
  if (filter === 'RESOLVED') return item.status === 'RESOLVED';
  return item.status === filter;
}

function statusCounts(items: Complaint[]) {
  return {
    all: items.length,
    reported: items.filter((i) => i.status === 'OPEN').length,
    inProgress: items.filter((i) => i.status === 'IN_PROGRESS').length,
    resolved: items.filter((i) => i.status === 'RESOLVED').length,
    needsAttention: items.filter((i) => i.status === 'CLOSED').length,
  };
}

export function Home() {
  const [filter, setFilter] = useState<StatusFilter>('all');
  const query = useQuery({ queryKey: ['complaints'], queryFn: complaintsApi.list });
  const items = query.data?.items ?? [];

  const stats = useMemo(() => {
    const total = items.length;
    const inProgress = items.filter((i) => i.status === 'IN_PROGRESS').length;
    const resolved = items.filter((i) => i.status === 'RESOLVED').length;
    const needsAttention = items.filter((i) => i.status === 'CLOSED').length;
    return { total, inProgress, resolved, needsAttention };
  }, [items]);

  const visible = useMemo(
    () => items.filter((item) => matchesFilter(item, filter)).slice(0, 4),
    [items, filter],
  );

  return (
    <section className="dashboard">
      <div className="dashboard-hero">
        <div>
          <h1>
            {greetingForNow()}, Piyush
          </h1>
          <p className="dashboard-subtitle">
            Report civic issues in your area and follow their progress.
          </p>
        </div>
        <Link className="report-cta" to="/complaints/new">
          <span className="report-cta-plus" aria-hidden>
            +
          </span>
          <span>
            <strong>Report an issue</strong>
            <small>Takes about 2 minutes</small>
          </span>
        </Link>
      </div>

      <div className="summary-grid">
        <article className="summary-card accent-teal">
          <p className="metric-label">Total complaints</p>
          <p className="metric-value">{query.isLoading ? '—' : stats.total}</p>
          <p className="metric-helper">All reports you submitted</p>
        </article>
        <article className="summary-card accent-blue">
          <p className="metric-label">In progress</p>
          <p className="metric-value">{query.isLoading ? '—' : stats.inProgress}</p>
          <p className="metric-helper">Teams are working on these</p>
        </article>
        <article className="summary-card accent-green">
          <p className="metric-label">Resolved</p>
          <p className="metric-value">{query.isLoading ? '—' : stats.resolved}</p>
          <p className="metric-helper">Issues marked as fixed</p>
        </article>
        <article className="summary-card accent-amber">
          <p className="metric-label">Needs attention</p>
          <p className="metric-value">{query.isLoading ? '—' : stats.needsAttention}</p>
          <p className="metric-helper">Updates or details requested</p>
        </article>
      </div>

      <div className="section-heading">
        <div>
          <h2>Your recent complaints</h2>
          <p>Track each report and see what happens next.</p>
        </div>
        <Link className="text-link" to="/complaints">
          View all complaints →
        </Link>
      </div>

      <div className="filter-row" role="tablist" aria-label="Filter complaints">
        {(
          [
            ['all', 'All complaints'],
            ['IN_PROGRESS', 'In progress'],
            ['RESOLVED', 'Resolved'],
            ['NEEDS_ATTENTION', 'Needs attention'],
          ] as const
        ).map(([key, text]) => (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={filter === key}
            className={`filter-chip${filter === key ? ' active' : ''}`}
            onClick={() => setFilter(key)}
          >
            {text}
          </button>
        ))}
      </div>

      <div className="complaints-table">
        <div className="table-header" aria-hidden>
          <span>Issue</span>
          <span>Location</span>
          <span>Reported</span>
          <span>Status</span>
          <span />
        </div>

        {query.isLoading && <p className="table-state">Loading reports…</p>}
        {query.isError && <p className="table-state error">Reports are temporarily unavailable.</p>}
        {!query.isLoading && !query.isError && visible.length === 0 && (
          <p className="table-state">No reports yet. Be the first to raise an issue.</p>
        )}

        {visible.map((item) => {
          const status = displayStatus(item.status);
          return (
            <Link key={item.id} className="table-row" to={`/complaints/${item.id}`}>
              <div className="issue-cell">
                <span className="issue-tile">{categoryInitials[item.category]}</span>
                <span>
                  <strong>{item.title}</strong>
                  <small>
                    {complaintRef(item.id, item.created_at)} · {categoryDisplay[item.category]}
                  </small>
                </span>
              </div>
              <span className="location-cell">{item.location.address}</span>
              <span className="date-cell">{formatDate(item.created_at)}</span>
              <span className={`status-chip ${status.key}`}>{status.text}</span>
              <span className="view-link">View →</span>
            </Link>
          );
        })}
      </div>

      <div className="privacy-note">
        <span className="info-icon" aria-hidden>
          i
        </span>
        <p>
          Your reports help your local teams understand what needs attention. Similar reports may be
          grouped internally to coordinate repairs.
        </p>
      </div>
    </section>
  );
}

export function ComplaintForm() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [photoNames, setPhotoNames] = useState<string[]>([]);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      zone_id: 'zone_01',
      latitude: 13.0827,
      longitude: 80.2707,
    },
  });
  const mutation = useMutation({
    mutationFn: (values: RegisterFormValues) => {
      const { address, latitude, longitude, description, category, zone_id } = values;
      return complaintsApi.create({
        title: titleFromDescription(description),
        description,
        category,
        zone_id,
        location: { address, latitude, longitude },
      });
    },
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ['complaints'] });
      navigate(`/complaints/${data.id}`);
    },
  });

  return (
    <section className="register-page">
      <p className="register-lede">
        Tell us what is happening. Your report helps the local team understand what needs attention.
      </p>
      <p className="breadcrumb">
        <Link to="/complaints">My complaints</Link>
        <span> / </span>
        <span>Register a complaint</span>
      </p>
      <h1>Register a complaint</h1>
      <p className="register-intro">Share the details below. Fields marked * are required.</p>

      <div className="register-layout">
        <form
          className="register-card"
          onSubmit={handleSubmit((values) => mutation.mutate(values))}
          noValidate
        >
          <h2>Issue details</h2>

          <label className="field">
            <span>Category *</span>
            <select defaultValue="" {...register('category')}>
              <option value="" disabled>
                Select an issue category
              </option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {categoryDisplay[c]}
                </option>
              ))}
            </select>
            {errors.category && <small className="error">{String(errors.category.message)}</small>}
          </label>

          <label className="field">
            <span>Describe the issue *</span>
            <textarea
              rows={3}
              placeholder="What happened? Include useful details…"
              {...register('description')}
            />
            {errors.description && (
              <small className="error">{String(errors.description.message)}</small>
            )}
          </label>

          <label className="field">
            <span>Location / landmark *</span>
            <input placeholder="Street, area, nearby landmark" {...register('address')} />
            {errors.address && <small className="error">{String(errors.address.message)}</small>}
          </label>
          <p className="field-hint">Pinpoint the issue as accurately as possible.</p>

          <div className="map-placeholder" role="img" aria-label="Map preview">
            Map preview · Select location
          </div>
          <input type="hidden" {...register('latitude')} />
          <input type="hidden" {...register('longitude')} />
          <input type="hidden" {...register('zone_id')} />

          <div className="field">
            <span>Photos (optional)</span>
            <label className="photo-upload">
              <span className="photo-plus" aria-hidden>
                +
              </span>
              <span>
                {photoNames.length > 0
                  ? `${photoNames.length} photo${photoNames.length === 1 ? '' : 's'} selected`
                  : 'Add photos · JPG or PNG'}
              </span>
              <input
                type="file"
                accept="image/jpeg,image/png"
                multiple
                onChange={(event) => {
                  const files = Array.from(event.target.files ?? []).slice(0, 5);
                  setPhotoNames(files.map((file) => file.name));
                }}
              />
            </label>
          </div>
          <p className="field-hint privacy">
            Avoid including sensitive personal information in photos or descriptions.
          </p>

          {mutation.isError && (
            <p className="error">We could not submit your report. Please try again.</p>
          )}

          <div className="register-actions">
            <button className="button submit-complaint" type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? 'Submitting…' : 'Submit complaint'}
            </button>
            <Link className="button-secondary" to="/complaints">
              Cancel
            </Link>
          </div>
        </form>

        <aside className="next-steps-card">
          <h2>What happens next</h2>
          <ol>
            <li>
              <span>1</span>
              <p>We receive your report</p>
            </li>
            <li>
              <span>2</span>
              <p>The team reviews the issue</p>
            </li>
            <li>
              <span>3</span>
              <p>You can track progress here</p>
            </li>
          </ol>
        </aside>
      </div>
    </section>
  );
}

export function ComplaintListPage() {
  const [filter, setFilter] = useState<StatusFilter>('all');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const query = useQuery({ queryKey: ['complaints'], queryFn: complaintsApi.list });
  const items = query.data?.items ?? [];
  const counts = useMemo(() => statusCounts(items), [items]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return items.filter((item) => {
      if (!matchesFilter(item, filter)) return false;
      if (!q) return true;
      const haystack = [
        item.title,
        item.description,
        item.location.address,
        categoryDisplay[item.category],
        complaintRef(item.id, item.created_at),
      ]
        .join(' ')
        .toLowerCase();
      return haystack.includes(q);
    });
  }, [items, filter, search]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, pageCount);
  const pageItems = filtered.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);
  const rangeStart = filtered.length === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1;
  const rangeEnd = Math.min(currentPage * PAGE_SIZE, filtered.length);

  return (
    <section className="all-complaints-page">
      <p className="register-lede">
        Review every report you have submitted and check its latest status.
      </p>
      <p className="breadcrumb">
        <Link to="/">My complaints</Link>
        <span> / </span>
        <span>All complaints</span>
      </p>

      <div className="all-complaints-heading">
        <div>
          <h1>All complaints</h1>
          <p className="complaints-count">
            {query.isLoading ? '…' : `${filtered.length} complaint${filtered.length === 1 ? '' : 's'}`}
          </p>
        </div>
        <Link className="button register-cta" to="/complaints/new">
          + Register a complaint
        </Link>
      </div>

      <label className="search-field">
        <span className="search-icon" aria-hidden>
          ⌕
        </span>
        <input
          type="search"
          placeholder="Search by reference, issue, or location"
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            setPage(1);
          }}
        />
      </label>

      <p className="filter-label">Filter by status</p>
      <div className="filter-row" role="tablist" aria-label="Filter by status">
        {(
          [
            ['all', `All (${counts.all})`],
            ['OPEN', `Reported (${counts.reported})`],
            ['IN_PROGRESS', `In progress (${counts.inProgress})`],
            ['RESOLVED', `Resolved (${counts.resolved})`],
            ['NEEDS_ATTENTION', `Needs attention (${counts.needsAttention})`],
          ] as const
        ).map(([key, text]) => (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={filter === key}
            className={`filter-chip${filter === key ? ' active' : ''}`}
            onClick={() => {
              setFilter(key);
              setPage(1);
            }}
          >
            {text}
          </button>
        ))}
      </div>

      <div className="all-complaints-list">
        {query.isLoading && <p className="table-state">Loading reports…</p>}
        {query.isError && <p className="table-state error">Reports are temporarily unavailable.</p>}
        {!query.isLoading && !query.isError && pageItems.length === 0 && (
          <p className="table-state">No complaints match your search.</p>
        )}
        {pageItems.map((item) => {
          const status = displayStatus(item.status);
          return (
            <Link key={item.id} className="all-complaint-row" to={`/complaints/${item.id}`}>
              <div className="all-complaint-main">
                <strong>{item.title}</strong>
                <small>
                  {complaintRef(item.id, item.created_at)} · {categoryDisplay[item.category]}
                </small>
              </div>
              <div className="all-complaint-mid">
                <span className="location-cell">{item.location.address}</span>
                <span className={`status-chip ${status.key}`}>{status.text}</span>
              </div>
              <div className="all-complaint-side">
                <span className="date-cell">{formatDate(item.created_at)}</span>
                <span className="view-link">View details →</span>
              </div>
            </Link>
          );
        })}
      </div>

      <div className="pagination">
        <span>
          Showing {rangeStart}–{rangeEnd} of {filtered.length}
        </span>
        <div className="pagination-controls">
          <button
            type="button"
            disabled={currentPage <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            ← Previous
          </button>
          {Array.from({ length: pageCount }, (_, index) => index + 1).map((number) => (
            <button
              key={number}
              type="button"
              className={number === currentPage ? 'active' : undefined}
              onClick={() => setPage(number)}
            >
              {number}
            </button>
          ))}
          <button
            type="button"
            disabled={currentPage >= pageCount}
            onClick={() => setPage((p) => Math.min(pageCount, p + 1))}
          >
            Next →
          </button>
        </div>
      </div>
    </section>
  );
}

export function ComplaintDetail() {
  const { id = '' } = useParams();
  const query = useQuery({
    queryKey: ['complaint', id],
    queryFn: () => complaintsApi.get(id),
    enabled: Boolean(id),
  });
  const listQuery = useQuery({ queryKey: ['complaints'], queryFn: complaintsApi.list });

  if (query.isLoading) return <p className="state">Loading report…</p>;
  if (query.isError)
    return (
      <section className="state">
        <h1>Report not found</h1>
        <Link to="/complaints">Return to reports</Link>
      </section>
    );

  const item = query.data!;
  const ref = complaintRef(item.id, item.created_at);
  const status = displayStatus(item.status);
  const timeline = progressTimeline(item);
  const similar = (listQuery.data?.items ?? [])
    .filter((candidate) => candidate.id !== item.id && candidate.category === item.category)
    .slice(0, 2);

  return (
    <section className="detail-page">
      <p className="register-lede">Track the status and updates for your submitted complaint.</p>
      <p className="breadcrumb">
        <Link to="/complaints">My complaints</Link>
        <span> / </span>
        <span>{ref}</span>
      </p>

      <h1>{item.title}</h1>
      <p className="detail-ref">
        Complaint {ref} · Submitted {formatDate(item.created_at)}
      </p>
      <span className={`status-chip detail-status ${status.key}`}>{status.text.toUpperCase()}</span>

      <div className="detail-layout">
        <article className="detail-card">
          <h2>Complaint details</h2>
          <div className="detail-field">
            <small>Category</small>
            <p>{categoryDisplay[item.category]}</p>
          </div>
          <div className="detail-field">
            <small>Location</small>
            <p>{item.location.address}</p>
          </div>
          <div className="detail-field">
            <small>Description</small>
            <p>{item.description}</p>
          </div>
          <div className="evidence-preview" role="img" aria-label="Evidence preview">
            {item.image_ids && item.image_ids.length > 0 ? 'Photo attached' : 'No photo attached'}
          </div>
          <div className="detail-timestamps">
            <div className="detail-field">
              <small>Reported on</small>
              <p>{formatDateTime(item.created_at)}</p>
            </div>
            <div className="detail-field">
              <small>Last updated</small>
              <p>{formatDateTime(item.updated_at)}</p>
            </div>
          </div>
        </article>

        <aside className="progress-card">
          <h2>Progress updates</h2>
          <ol className="progress-timeline">
            {timeline.map((step) => (
              <li key={step.title} className={step.state}>
                <span className="timeline-dot" aria-hidden />
                <div>
                  <strong>{step.title}</strong>
                  <small>{step.stamp}</small>
                  <p>{step.description}</p>
                </div>
              </li>
            ))}
          </ol>
        </aside>
      </div>

      <section className="similar-card">
        <div className="similar-heading">
          <h2>Similar complaints</h2>
          {similar.length > 0 && <span className="same-issue-badge">Same issue</span>}
        </div>
        <p className="similar-copy">
          These reports were grouped with your complaint because they appear to describe the same
          local issue. Progress is tracked together.
        </p>
        {similar.length === 0 ? (
          <p className="similar-empty">No similar complaints are linked yet.</p>
        ) : (
          similar.map((candidate) => {
            const candidateStatus = displayStatus(candidate.status);
            return (
              <Link
                key={candidate.id}
                className="similar-row"
                to={`/complaints/${candidate.id}`}
              >
                <span className="similar-ref">{complaintRef(candidate.id, candidate.created_at)}</span>
                <span className="similar-main">
                  <strong>{candidate.title}</strong>
                  <small>{candidate.location.address}</small>
                </span>
                <span className="date-cell">{formatDate(candidate.created_at)}</span>
                <span className={`status-chip compact ${candidateStatus.key}`}>
                  {candidateStatus.text}
                </span>
                <span className="similar-privacy">Reporter details are private</span>
              </Link>
            );
          })
        )}
      </section>

      <p className="detail-footnote">
        Status reflects the latest update available from the responsible civic team.
      </p>

      <div className="help-card">
        <div>
          <h2>Need to add information?</h2>
          <p>Contact the civic team if the location or issue details need to be corrected.</p>
        </div>
        <a className="button-secondary" href="#help">
          Get help
        </a>
      </div>
    </section>
  );
}
