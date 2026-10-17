import { useQuery } from '@tanstack/react-query';
import { Link, NavLink, useParams } from 'react-router-dom';
import { categoryLabel, formatWhen, priorityLabel, statusLabel } from './admin-format';
import { complaintImageUrl, complaintsApi, zonesApi } from './api';
import { INCIDENT_LIST } from './admin-incident-list';
import { ZONE_OVERVIEW } from './admin-zone';
import { DEFAULT_ADMIN_USER_ID } from './paths';

const navItems = [
  { to: '/admin/home', label: 'City Overview' },
  { to: ZONE_OVERVIEW, label: 'Zones' },
  { to: '/admin/incident-list', label: 'Incidents' },
  { to: '/admin/allocation-review', label: 'Resource Allocation' },
  { to: '/admin/teams', label: 'Teams & Capacity' },
] as const;

export function AdminComplaintDetails() {
  const { complaintId } = useParams();
  const complaintQuery = useQuery({
    queryKey: ['admin-complaint', complaintId],
    queryFn: () => complaintsApi.get(DEFAULT_ADMIN_USER_ID, complaintId!),
    enabled: Boolean(complaintId),
    retry: false,
  });
  const zonesQuery = useQuery({ queryKey: ['admin-zones'], queryFn: zonesApi.list, retry: false });
  const complaint = complaintQuery.data;
  const zoneName = zonesQuery.data?.items.find((zone) => zone.id === complaint?.zone_id)?.name ?? complaint?.zone_id;

  return (
    <div className="complaint-shell">
      <aside className="complaint-sidebar">
        <div className="complaint-brand">
          <strong>Civic SahAI</strong>
          <span>City administration</span>
        </div>
        <div className="complaint-nav" aria-label="City administration">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} className={item.label === 'Incidents' ? 'active' : undefined}>
              {item.label}
            </NavLink>
          ))}
        </div>
      </aside>
      <div className="complaint-main">
        <p className="complaint-crumb">Incidents / {complaint?.id ?? 'Complaint'}</p>
        <h1>Citizen complaint details</h1>
        <p className="complaint-lead">Original submission and evidence from the complaint record.</p>
        {!complaintId ? <p className="complaint-card">Open a complaint by its id.</p> : null}
        {complaintQuery.isLoading ? <p className="complaint-card">Loading complaint…</p> : null}
        {complaintQuery.isError ? <p className="complaint-card">This complaint could not be loaded.</p> : null}
        {complaint ? (
          <div className="complaint-grid">
            <section className="complaint-card">
              <h2>
                {complaint.id} · {categoryLabel(complaint.category)}
              </h2>
              <p className="complaint-submitted">Submitted {formatWhen(complaint.created_at)}</p>
              <h3>Citizen description</h3>
              <blockquote>“{complaint.description}”</blockquote>
              <h3>Location</h3>
              <p>
                {complaint.location.address}
                {zoneName ? ` · ${zoneName}` : ''} · {complaint.location.latitude}, {complaint.location.longitude}
              </p>
              <h3>Category & severity</h3>
              <p>
                {categoryLabel(complaint.category)} · {priorityLabel(complaint.priority_score)} priority
              </p>
              <h3>Attached evidence</h3>
              {complaint.image_ids.length === 0 ? <div className="complaint-evidence">No photo attached</div> : null}
              {complaint.image_ids.map((imageId) => (
                <img key={imageId} className="complaint-evidence" src={complaintImageUrl(imageId)} alt="Complaint evidence" />
              ))}
            </section>
            <section className="complaint-card complaint-workflow">
              <h2>Workflow</h2>
              <h3>Status</h3>
              <p className="complaint-status">{statusLabel(complaint.status)}</p>
              <p className="complaint-note">
                The complaint record does not include which incident it was grouped into.
              </p>
            </section>
          </div>
        ) : null}
        <Link className="complaint-back" to={INCIDENT_LIST}>
          ← Back to incidents
        </Link>
      </div>
    </div>
  );
}
