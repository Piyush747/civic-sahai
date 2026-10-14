import { useEffect, useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import axios from 'axios';
import { citizenApi, complaintsApi } from './api';
import { LocationPicker } from './location-picker';
import { useCitizenPaths, useCitizenUserId } from './paths';
import type { ComplaintFormField, LocationSearchResult } from './types';

const registerSchema = z.object({
  category: z.string().min(1, 'Select an issue category'),
  description: z.string().min(10, 'Please add more detail').max(2000),
  address: z.string().min(3, 'Add a street, area, or landmark').max(300),
  landmark: z.string().max(160).optional(),
  latitude: z.coerce.number().min(-90).max(90),
  longitude: z.coerce.number().min(-180).max(180),
});
type RegisterFormValues = z.infer<typeof registerSchema>;

const PAGE_SIZE = 5;
const fallbackCategories = [
  { value: 'ROAD_DAMAGE', label: 'Road damage' },
  { value: 'WASTE_MANAGEMENT', label: 'Waste management' },
  { value: 'STREETLIGHT', label: 'Streetlight' },
  { value: 'WATER_SUPPLY', label: 'Water supply' },
  { value: 'DRAINAGE', label: 'Drainage' },
  { value: 'PUBLIC_SAFETY', label: 'Public safety' },
  { value: 'OTHER', label: 'Other' },
];

function statusClass(status: string) {
  if (status === 'IN_PROGRESS') return 'in-progress';
  if (status === 'RESOLVED') return 'resolved';
  if (status === 'NEEDS_ATTENTION') return 'needs-attention';
  return 'reported';
}

function summaryAccent(key: string) {
  if (key === 'IN_PROGRESS') return 'accent-blue';
  if (key === 'RESOLVED') return 'accent-green';
  if (key === 'NEEDS_ATTENTION') return 'accent-amber';
  return 'accent-teal';
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

function fieldByName(fields: ComplaintFormField[] | undefined, name: string) {
  return fields?.find((field) => field.name === name);
}

export function Home() {
  const paths = useCitizenPaths();
  const userId = useCitizenUserId();
  const [filter, setFilter] = useState('ALL');
  const query = useQuery({
    queryKey: ['citizen-homepage', userId],
    queryFn: () => citizenApi.homepage(userId),
  });
  const page = query.data;
  const items = page?.complaints ?? [];
  const visible = useMemo(
    () => items.filter((item) => filter === 'ALL' || item.status === filter).slice(0, 4),
    [items, filter],
  );

  if (query.isLoading) return <p className="state">Loading reports…</p>;
  if (query.isError || !page) return <p className="table-state error">Reports are temporarily unavailable.</p>;

  return (
    <section className="dashboard">
      <div className="dashboard-hero">
        <div>
          <h1>{page.welcomeSection.greeting}</h1>
          <p className="dashboard-subtitle">{page.welcomeSection.description}</p>
        </div>
        <Link className="report-cta" to={paths.newComplaint}>
          <span className="report-cta-plus" aria-hidden>
            +
          </span>
          <span>
            <strong>{page.welcomeSection.primaryAction.label}</strong>
            <small>{page.welcomeSection.primaryAction.subtitle}</small>
          </span>
        </Link>
      </div>

      <div className="summary-grid">
        {page.summaryCards.map((card) => (
          <article key={card.key} className={`summary-card ${summaryAccent(card.key)}`}>
            <p className="metric-label">{card.title}</p>
            <p className="metric-value">{card.count}</p>
            <p className="metric-helper">{card.description}</p>
          </article>
        ))}
      </div>

      <div className="section-heading">
        <div>
          <h2>{page.complaintsSection.title}</h2>
          <p>{page.complaintsSection.description}</p>
        </div>
        <Link className="text-link" to={paths.complaints}>
          {page.complaintsSection.viewAllLabel} →
        </Link>
      </div>

      <div className="filter-row" role="tablist" aria-label="Filter complaints">
        {page.complaintsSection.filters.map((item) => (
          <button
            key={item.key}
            type="button"
            role="tab"
            aria-selected={filter === item.key}
            className={`filter-chip${filter === item.key ? ' active' : ''}`}
            onClick={() => setFilter(item.key)}
          >
            {item.label}
          </button>
        ))}
      </div>

      <div className="complaints-table">
        <div className="table-header" aria-hidden>
          {page.complaintsSection.tableHeaders.map((header) => (
            <span key={header}>{header}</span>
          ))}
          <span />
        </div>

        {visible.length === 0 && <p className="table-state">No reports yet. Be the first to raise an issue.</p>}

        {visible.map((item) => (
          <Link key={item.complaintId} className="table-row" to={paths.complaint(item.complaintId)}>
            <div className="issue-cell">
              <span className="issue-tile">{item.categoryCode}</span>
              <span>
                <strong>{item.title}</strong>
                <small>
                  {item.referenceNumber} · {item.categoryLabel}
                </small>
              </span>
            </div>
            <span className="location-cell">{item.location.address}</span>
            <span className="date-cell">{formatDate(item.reportedAt)}</span>
            <span className={`status-chip ${statusClass(item.status)}`}>{item.statusLabel}</span>
            <span className="view-link">{page.complaintsSection.viewActionLabel} →</span>
          </Link>
        ))}
      </div>

      <div className="privacy-note">
        <span className="info-icon" aria-hidden>
          i
        </span>
        <p>{page.informationNote}</p>
      </div>
    </section>
  );
}

function SelectedPhoto({ file, onRemove }: { file: File; onRemove: () => void }) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    const objectUrl = URL.createObjectURL(file);
    setUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [file]);

  return (
    <li className="photo-preview">
      {url ? <img src={url} alt={file.name} /> : null}
      <span>{file.name}</span>
      <button type="button" onClick={onRemove} aria-label={`Remove ${file.name}`}>
        Remove
      </button>
    </li>
  );
}

export function ComplaintForm() {
  const paths = useCitizenPaths();
  const userId = useCitizenUserId();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [photos, setPhotos] = useState<File[]>([]);
  const [searchOpen, setSearchOpen] = useState(false);
  const formQuery = useQuery({
    queryKey: ['citizen-complaint-form'],
    queryFn: () => citizenApi.complaintForm(),
  });
  const content = formQuery.data;
  const fields = content?.form.fields;
  const categoryField = fieldByName(fields, 'category');
  const descriptionField = fieldByName(fields, 'description');
  const locationField = fieldByName(fields, 'location.address');
  const photoField = fieldByName(fields, 'attachments');
  const categoryOptions = categoryField?.options ?? fallbackCategories;
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      latitude: 13.0827,
      longitude: 80.2707,
      landmark: '',
    },
  });
  const latitude = watch('latitude');
  const longitude = watch('longitude');
  const address = watch('address');
  const [placeQuery, setPlaceQuery] = useState('');
  useEffect(() => {
    const timer = window.setTimeout(() => setPlaceQuery((address ?? '').trim()), 300);
    return () => window.clearTimeout(timer);
  }, [address]);
  const placeSearch = useQuery({
    queryKey: ['location-search', placeQuery, latitude, longitude],
    queryFn: () => citizenApi.locationSearch(placeQuery, Number(latitude), Number(longitude)),
    enabled: searchOpen && placeQuery.length >= 2 && Number.isFinite(Number(latitude)) && Number.isFinite(Number(longitude)),
  });
  const places = placeSearch.data?.places ?? [];
  const [servicePin, setServicePin] = useState({ latitude: 13.0827, longitude: 80.2707 });
  useEffect(() => {
    const timer = window.setTimeout(() => {
      const nextLatitude = Number(latitude);
      const nextLongitude = Number(longitude);
      if (Number.isFinite(nextLatitude) && Number.isFinite(nextLongitude)) {
        setServicePin({ latitude: nextLatitude, longitude: nextLongitude });
      }
    }, 300);
    return () => window.clearTimeout(timer);
  }, [latitude, longitude]);
  const serviceArea = useQuery({
    queryKey: ['location-status', servicePin.latitude, servicePin.longitude],
    queryFn: () => citizenApi.locationStatus(servicePin.latitude, servicePin.longitude),
  });
  const inServiceArea = serviceArea.data?.inServiceArea !== false;
  function choosePlace(place: LocationSearchResult) {
    setSearchOpen(false);
    setValue('address', place.label, { shouldValidate: true });
    setValue('landmark', place.name, { shouldValidate: true });
    setValue('latitude', place.latitude, { shouldValidate: true });
    setValue('longitude', place.longitude, { shouldValidate: true });
  }
  const mutation = useMutation({
    mutationFn: async (values: RegisterFormValues) => {
      const attachments: { fileId: string }[] = [];
      for (const photo of photos) {
        const uploaded = await complaintsApi.uploadImage(photo, userId);
        attachments.push({ fileId: uploaded.image_id });
      }
      return citizenApi.createComplaint(userId, {
        category: values.category,
        description: values.description,
        location: {
          address: values.address,
          ...(values.landmark ? { landmark: values.landmark } : {}),
          latitude: values.latitude,
          longitude: values.longitude,
        },
        attachments,
      });
    },
    onSuccess: async (data) => {
      await queryClient.invalidateQueries({ queryKey: ['citizen-homepage', userId] });
      await queryClient.invalidateQueries({ queryKey: ['citizen-complaints', userId] });
      navigate(paths.complaint(data.complaintId));
    },
  });

  return (
    <section className="register-page">
      <p className="register-lede">
        {content?.introText ??
          'Tell us what is happening. Your report helps the local team understand what needs attention.'}
      </p>
      <p className="breadcrumb">
        <Link to={paths.complaints}>{content?.breadcrumbs[0]?.label ?? 'My complaints'}</Link>
        <span> / </span>
        <span>{content?.breadcrumbs[1]?.label ?? 'Register a complaint'}</span>
      </p>
      <h1>{content?.pageTitle ?? 'Register a complaint'}</h1>
      <p className="register-intro">
        {content?.pageDescription ?? 'Share the details below. Fields marked * are required.'}
      </p>

      <div className="register-layout">
        <form className="register-card" onSubmit={handleSubmit((values) => mutation.mutate(values))} noValidate>
          <h2>{content?.form.sectionTitle ?? 'Issue details'}</h2>

          <label className="field">
            <span>{categoryField?.label ?? 'Category'} *</span>
            <select defaultValue="" {...register('category')}>
              <option value="" disabled>
                {categoryField?.placeholder ?? 'Select an issue category'}
              </option>
              {categoryOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            {errors.category && <small className="error">{String(errors.category.message)}</small>}
          </label>

          <label className="field">
            <span>{descriptionField?.label ?? 'Describe the issue'} *</span>
            <textarea
              rows={3}
              placeholder={descriptionField?.placeholder ?? 'What happened? Include useful details…'}
              {...register('description')}
            />
            {errors.description && <small className="error">{String(errors.description.message)}</small>}
          </label>

          <label className="field">
            <span>{locationField?.label ?? 'Location / landmark'} *</span>
            <div className="location-suggest">
              <input
                placeholder={locationField?.placeholder ?? 'Street, area, or place'}
                autoComplete="off"
                {...register('address', {
                  onChange: () => {
                    setValue('landmark', '');
                    setSearchOpen(true);
                  },
                })}
              />
              {searchOpen && placeQuery.length >= 2 && (
                <ul className="location-suggest-list" role="listbox">
                  {placeSearch.isFetching && places.length === 0 && <li>Searching places…</li>}
                  {places.map((place) => (
                    <li key={`${place.label}-${place.latitude}-${place.longitude}`}>
                      <button type="button" onClick={() => choosePlace(place)}>
                        <strong>{place.name}</strong>
                        <span>{place.label}</span>
                      </button>
                    </li>
                  ))}
                  {placeSearch.isSuccess && !placeSearch.isFetching && places.length === 0 && <li>No matching places.</li>}
                </ul>
              )}
            </div>
            {errors.address && <small className="error">{String(errors.address.message)}</small>}
          </label>
          <p className="field-hint">
            {locationField?.helperText ??
              'Results match what you type near the pin on the map. Move the pin or use my location first if you are elsewhere.'}
          </p>

          <LocationPicker
            latitude={Number(latitude)}
            longitude={Number(longitude)}
            mapLabel={content?.form.mapPreview.placeholder ?? 'Map preview'}
            onPositionChange={(nextLatitude, nextLongitude) => {
              setValue('latitude', nextLatitude, { shouldValidate: true });
              setValue('longitude', nextLongitude, { shouldValidate: true });
            }}
          />
          {serviceArea.data && !serviceArea.data.inServiceArea && (
            <p className="service-area-warning" role="alert">
              This portal only accepts reports within {serviceArea.data.cityName}. Move the pin inside the city.
            </p>
          )}
          <input type="hidden" {...register('latitude')} />
          <input type="hidden" {...register('longitude')} />

          <div className="field">
            <span>{photoField?.label ?? 'Photos (optional)'}</span>
            <label className="photo-upload">
              <span className="photo-plus" aria-hidden>
                +
              </span>
              <span>
                {photos.length > 0
                  ? `${photos.length} photo${photos.length === 1 ? '' : 's'} selected`
                  : 'Add photos · JPG or PNG'}
              </span>
              <input
                type="file"
                accept={photoField?.acceptedFormats?.join(',') ?? 'image/jpeg,image/png'}
                multiple
                onChange={(event) => {
                  const picked = Array.from(event.target.files ?? []);
                  const limit = photoField?.maxFiles ?? 5;
                  setPhotos((current) => [...current, ...picked].slice(0, limit));
                  event.target.value = '';
                }}
              />
            </label>
            {photos.length > 0 && (
              <ul className="photo-preview-list">
                {photos.map((file) => (
                  <SelectedPhoto
                    key={`${file.name}-${file.lastModified}-${file.size}`}
                    file={file}
                    onRemove={() =>
                      setPhotos((current) =>
                        current.filter(
                          (item) =>
                            !(
                              item.name === file.name &&
                              item.lastModified === file.lastModified &&
                              item.size === file.size
                            ),
                        ),
                      )
                    }
                  />
                ))}
              </ul>
            )}
          </div>
          <p className="field-hint privacy">
            {content?.form.privacyNote ??
              'Avoid including sensitive personal information in photos or descriptions.'}
          </p>

          {mutation.isError && (
            <p className="error">
              {axios.isAxiosError(mutation.error) &&
              mutation.error.response?.data?.error?.code === 'OUTSIDE_SERVICE_AREA'
                ? String(mutation.error.response.data.error.message)
                : 'We could not submit your report. Please try again.'}
            </p>
          )}

          <div className="register-actions">
            <button
              className="button submit-complaint"
              type="submit"
              disabled={mutation.isPending || serviceArea.isFetching || !inServiceArea}
            >
              {mutation.isPending ? 'Submitting…' : (content?.form.submitButton.label ?? 'Submit complaint')}
            </button>
            <Link className="button-secondary" to={paths.complaints}>
              {content?.form.cancelButton.label ?? 'Cancel'}
            </Link>
          </div>
        </form>

        <aside className="next-steps-card">
          <h2>{content?.nextSteps.title ?? 'What happens next'}</h2>
          <ol>
            {(content?.nextSteps.steps ?? [
              { step: 1, text: 'We receive your report' },
              { step: 2, text: 'The team reviews the issue' },
              { step: 3, text: 'You can track progress here' },
            ]).map((step) => (
              <li key={step.step}>
                <span>{step.step}</span>
                <p>{step.text}</p>
              </li>
            ))}
          </ol>
        </aside>
      </div>
    </section>
  );
}

export function ComplaintListPage() {
  const paths = useCitizenPaths();
  const userId = useCitizenUserId();
  const [filter, setFilter] = useState('ALL');
  const [search, setSearch] = useState('');
  const [pageNumber, setPageNumber] = useState(1);
  const query = useQuery({
    queryKey: ['citizen-complaints', userId, search, filter, pageNumber],
    queryFn: () =>
      citizenApi.complaints(userId, { search, status: filter, page: pageNumber, pageSize: PAGE_SIZE }),
  });
  const page = query.data;
  const counts = page?.summary.statusCounts ?? [];
  const pagination = page?.pagination;
  const pageCount = pagination?.totalPages ?? 0;

  return (
    <section className="all-complaints-page">
      <p className="register-lede">
        {page?.pageContent.introText ?? 'Review every report you have submitted and check its latest status.'}
      </p>
      <p className="breadcrumb">
        <Link to={paths.home}>{page?.pageContent.breadcrumb.parentLabel ?? 'My complaints'}</Link>
        <span> / </span>
        <span>{page?.pageContent.breadcrumb.currentLabel ?? 'All complaints'}</span>
      </p>

      <div className="all-complaints-heading">
        <div>
          <h1>{page?.pageContent.pageTitle ?? 'All complaints'}</h1>
          <p className="complaints-count">
            {query.isLoading
              ? '…'
              : `${page?.summary.totalCount ?? 0} complaint${page?.summary.totalCount === 1 ? '' : 's'}`}
          </p>
        </div>
        <Link className="button register-cta" to={paths.newComplaint}>
          + {page?.pageContent.registerButton.label ?? 'Register a complaint'}
        </Link>
      </div>

      <label className="search-field">
        <span className="search-icon" aria-hidden>
          ⌕
        </span>
        <input
          type="search"
          placeholder={page?.pageContent.searchPlaceholder ?? 'Search by reference, issue, or location'}
          value={search}
          onChange={(event) => {
            setSearch(event.target.value);
            setPageNumber(1);
          }}
        />
      </label>

      <p className="filter-label">{page?.pageContent.filterTitle ?? 'Filter by status'}</p>
      <div className="filter-row" role="tablist" aria-label="Filter by status">
        {counts.map((item) => (
          <button
            key={item.status}
            type="button"
            role="tab"
            aria-selected={filter === item.status}
            className={`filter-chip${filter === item.status ? ' active' : ''}`}
            onClick={() => {
              setFilter(item.status);
              setPageNumber(1);
            }}
          >
            {item.label} ({item.count})
          </button>
        ))}
      </div>

      <div className="all-complaints-list">
        {query.isLoading && <p className="table-state">Loading reports…</p>}
        {query.isError && <p className="table-state error">Reports are temporarily unavailable.</p>}
        {!query.isLoading && !query.isError && (page?.complaints.length ?? 0) === 0 && (
          <p className="table-state">No complaints match your search.</p>
        )}
        {page?.complaints.map((item) => (
          <Link key={item.complaintId} className="all-complaint-row" to={paths.complaint(item.complaintId)}>
            <div className="all-complaint-main">
              <strong>{item.title}</strong>
              <small>
                {item.referenceNumber} · {item.categoryLabel}
              </small>
            </div>
            <div className="all-complaint-mid">
              <span className="location-cell">{item.location.address}</span>
              <span className={`status-chip ${statusClass(item.status)}`}>{item.statusLabel}</span>
            </div>
            <div className="all-complaint-side">
              <span className="date-cell">{formatDate(item.reportedAt)}</span>
              <span className="view-link">{page.pageContent.viewDetailsLabel} →</span>
            </div>
          </Link>
        ))}
      </div>

      <div className="pagination">
        <span>{pagination?.displayText ?? 'Showing 0–0 of 0'}</span>
        <div className="pagination-controls">
          <button type="button" disabled={!pagination?.hasPrevious} onClick={() => setPageNumber((current) => Math.max(1, current - 1))}>
            ← Previous
          </button>
          {Array.from({ length: pageCount }, (_, index) => index + 1).map((number) => (
            <button
              key={number}
              type="button"
              className={number === pageNumber ? 'active' : undefined}
              onClick={() => setPageNumber(number)}
            >
              {number}
            </button>
          ))}
          <button type="button" disabled={!pagination?.hasNext} onClick={() => setPageNumber((current) => current + 1)}>
            Next →
          </button>
        </div>
      </div>
    </section>
  );
}

export function ComplaintDetail() {
  const paths = useCitizenPaths();
  const userId = useCitizenUserId();
  const { id = '' } = useParams();
  const query = useQuery({
    queryKey: ['citizen-complaint', userId, id],
    queryFn: () => citizenApi.complaint(userId, id),
    enabled: Boolean(id),
  });

  if (query.isLoading) return <p className="state">Loading report…</p>;
  if (query.isError || !query.data)
    return (
      <section className="state">
        <h1>Report not found</h1>
        <Link to={paths.complaints}>Return to reports</Link>
      </section>
    );

  const page = query.data;
  const item = page.complaint;
  const location = item.location.landmark ? `${item.location.address} · ${item.location.landmark}` : item.location.address;

  return (
    <section className="detail-page">
      <p className="register-lede">{page.pageContent.introText}</p>
      <p className="breadcrumb">
        <Link to={paths.complaints}>{page.pageContent.breadcrumb.parentLabel}</Link>
        <span> / </span>
        <span>{page.pageContent.breadcrumb.currentLabel}</span>
      </p>

      <h1>{item.title}</h1>
      <p className="detail-ref">
        Complaint {item.referenceNumber} · Submitted {formatDate(item.reportedAt)}
      </p>
      <span className={`status-chip detail-status ${statusClass(item.status)}`}>{item.statusLabel}</span>

      <div className="detail-layout">
        <article className="detail-card">
          <h2>Complaint details</h2>
          <div className="detail-field">
            <small>Category</small>
            <p>{item.categoryLabel}</p>
          </div>
          <div className="detail-field">
            <small>Location</small>
            <p>{location}</p>
          </div>
          <div className="detail-field">
            <small>Description</small>
            <p>{item.description}</p>
          </div>
          <div className="evidence-preview">
            {item.attachments.length > 0 ? (
              item.attachments.map((attachment) => (
                <img key={attachment.attachmentId} src={attachment.url} alt="Complaint photo" />
              ))
            ) : (
              <span>No photo attached</span>
            )}
          </div>
          <div className="detail-timestamps">
            <div className="detail-field">
              <small>Reported on</small>
              <p>{formatDateTime(item.reportedAt)}</p>
            </div>
            <div className="detail-field">
              <small>Last updated</small>
              <p>{formatDateTime(item.lastUpdatedAt)}</p>
            </div>
          </div>
        </article>

        <aside className="progress-card">
          <h2>{page.progressSection.title}</h2>
          <ol className="progress-timeline">
            {page.progressSection.events.map((step) => (
              <li key={step.eventId} className={step.status === 'CURRENT' ? 'current' : 'done'}>
                <span className="timeline-dot" aria-hidden />
                <div>
                  <strong>{step.title}</strong>
                  <small>{formatTimelineStamp(step.timestamp)}</small>
                  <p>{step.description}</p>
                </div>
              </li>
            ))}
          </ol>
        </aside>
      </div>

      <section className="similar-card">
        <div className="similar-heading">
          <h2>{page.pageContent.similarComplaintsTitle}</h2>
          {page.similarComplaints.length > 0 && (
            <span className="same-issue-badge">{page.pageContent.sameIssueLabel}</span>
          )}
        </div>
        <p className="similar-copy">{page.pageContent.similarComplaintsDescription}</p>
        {page.similarComplaints.length === 0 ? (
          <p className="similar-empty">No similar complaints are linked yet.</p>
        ) : (
          page.similarComplaints.map((candidate) => (
            <div key={candidate.complaintId} className="similar-row">
              <span className="similar-ref">{candidate.referenceNumber}</span>
              <span className="similar-main">
                <strong>{candidate.title}</strong>
                <small>{candidate.location.address}</small>
              </span>
              <span className="date-cell">{formatDate(candidate.reportedAt)}</span>
              <span className={`status-chip compact ${statusClass(candidate.status)}`}>{candidate.statusLabel}</span>
              <span className="similar-privacy">{page.pageContent.privateReporterLabel}</span>
            </div>
          ))
        )}
      </section>

      <p className="detail-footnote">Status reflects the latest update available from the responsible civic team.</p>

      <div className="help-card">
        <div>
          <h2>{page.pageContent.informationSection.title}</h2>
          <p>{page.pageContent.informationSection.description}</p>
        </div>
        <a className="button-secondary" href="#help">
          {page.pageContent.informationSection.actionLabel}
        </a>
      </div>
    </section>
  );
}
