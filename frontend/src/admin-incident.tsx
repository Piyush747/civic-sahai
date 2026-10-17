import { useQuery } from '@tanstack/react-query';
import { Link, NavLink, useParams } from 'react-router-dom';
import { categoryLabel, formatWhen, priorityLabel, statusLabel, waitingLabel } from './admin-format';
import { incidentsApi, zonesApi } from './api';
import { ZONE_OVERVIEW } from './admin-zone';

export const INCIDENT_DETAILS = '/admin/incident-details';

const navItems = [
  { to: '/admin/home', label: 'City Overview' },
  { to: ZONE_OVERVIEW, label: 'Zones' },
  { to: '/admin/incident-list', label: 'Incidents' },
  { to: '/admin/allocation-review', label: 'Resource Allocation' },
  { to: '/admin/teams', label: 'Teams & Capacity' },
] as const;

export function AdminIncidentDetails() {
  const { incidentId } = useParams();
  const incidentQuery = useQuery({
    queryKey: ['admin-incident', incidentId],
    queryFn: () => incidentsApi.get(incidentId!),
    enabled: Boolean(incidentId),
    retry: false,
  });
  const zonesQuery = useQuery({ queryKey: ['admin-zones'], queryFn: zonesApi.list, retry: false });
  const incident = incidentQuery.data;
  const zoneName = zonesQuery.data?.items.find((zone) => zone.id === incident?.zone_id)?.name ?? incident?.zone_id;
  const backTo = incident ? `${ZONE_OVERVIEW}?zone=${encodeURIComponent(incident.zone_id)}` : ZONE_OVERVIEW;

  return (
    <div className="incident-shell">
      <aside className="incident-sidebar">
        <div className="incident-brand">
          <strong>Civic SahAI</strong>
          <span>City administration</span>
        </div>
        <div className="incident-nav" aria-label="City administration">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={'end' in item}
              className={({ isActive }) => (isActive || item.label === 'Incidents' ? 'active' : undefined)}
            >
              {item.label}
            </NavLink>
          ))}
        </div>
      </aside>
      <div className="incident-main">
        <p className="incident-crumb">Incidents / {zoneName ?? 'Zone'}</p>
        <h1>Incident details</h1>
        <p className="incident-lead">Review the grouped incident, its status, and what the record includes.</p>
        {!incidentId ? <p className="incident-card">Select an incident from the list.</p> : null}
        {incidentQuery.isLoading ? <p className="incident-card">Loading incident…</p> : null}
        {incidentQuery.isError ? <p className="incident-card">This incident could not be loaded.</p> : null}
        {incident ? (
          <>
            <span className="incident-open">{statusLabel(incident.status)}</span>
            <div className="incident-top">
              <section className="incident-card">
                <h2>{categoryLabel(incident.category)}</h2>
                <p className="incident-id">{incident.id}</p>
                <p>{incident.description}</p>
                <dl>
                  <div>
                    <dt>Location</dt>
                    <dd>{zoneName}</dd>
                  </div>
                  <div>
                    <dt>Linked citizen reports</dt>
                    <dd>
                      {incident.complaint_count} report{incident.complaint_count === 1 ? '' : 's'} grouped into this incident
                    </dd>
                  </div>
                  <div>
                    <dt>Reported</dt>
                    <dd>{formatWhen(incident.created_at)}</dd>
                  </div>
                  <div>
                    <dt>Waiting time</dt>
                    <dd>{incident.status === 'OPEN' || incident.status === 'IN_PROGRESS' ? waitingLabel(incident.created_at) : 'Closed'}</dd>
                  </div>
                  <div>
                    <dt>Priority</dt>
                    <dd>{priorityLabel(incident.priority_score)}</dd>
                  </div>
                </dl>
              </section>
              <section className="incident-card incident-response">
                <h2>Response & assignment</h2>
                <p className="incident-kicker">Status</p>
                <strong>{statusLabel(incident.status)}</strong>
                <p>
                  {incident.status === 'OPEN'
                    ? 'This incident is still open. Team assignment is not included on the incident record.'
                    : 'Team assignment is not included on the incident record.'}
                </p>
              </section>
            </div>
            <section className="incident-card">
              <h2>Individual complaints</h2>
              <p>
                This incident groups {incident.complaint_count} citizen report{incident.complaint_count === 1 ? '' : 's'}. The
                incident response does not include each original submission.
              </p>
            </section>
            <section className="incident-card">
              <h2>Six-month location history</h2>
              <p>Location history is not included on the incident record.</p>
            </section>
            <section className="incident-card">
              <h2>Locality impact and accessibility</h2>
              <p>Nearby landmarks and proximity counts are not included on the incident record.</p>
            </section>
          </>
        ) : null}
        <Link className="incident-back" to={backTo}>
          ← Back to {zoneName ?? 'zone'}
        </Link>
      </div>
    </div>
  );
}
