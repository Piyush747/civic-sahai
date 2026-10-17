import { useQuery } from '@tanstack/react-query';
import { Link, NavLink, useSearchParams } from 'react-router-dom';
import {
  categoryLabel,
  categoryMatches,
  formatWhen,
  incidentTypeOptions,
  isIncidentType,
  priorityLabel,
  statusLabel,
  type IncidentTypeFilter,
} from './admin-format';
import { INCIDENT_DETAILS } from './admin-incident';
import { incidentsApi, zonesApi } from './api';
import type { Incident } from './types';

export const INCIDENT_LIST = '/admin/incident-list';

const navItems = [
  { to: '/admin/home', label: 'City Overview' },
  { to: '/admin/zone-overview', label: 'Zones' },
  { to: INCIDENT_LIST, label: 'Incidents', end: true },
  { to: '/admin/allocation-review', label: 'Resource Allocation' },
  { to: '/admin/teams', label: 'Teams & Capacity' },
] as const;

const statusOptions = [
  { value: 'all', label: 'All statuses' },
  { value: 'OPEN', label: 'Open' },
  { value: 'IN_PROGRESS', label: 'In progress' },
  { value: 'RESOLVED', label: 'Resolved' },
  { value: 'CLOSED', label: 'Closed' },
] as const;

function tone(value: string) {
  const key = value.toLowerCase();
  if (key === 'open' || key === 'high' || key === 'critical') return 'red';
  if (key === 'in progress' || key === 'medium') return 'amber';
  if (key === 'low' || key === 'resolved' || key === 'closed') return 'green';
  return 'blue';
}

function matches(item: Incident, type: IncidentTypeFilter, status: string, search: string) {
  if (!categoryMatches(type, item.category)) return false;
  if (status !== 'all' && item.status !== status) return false;
  const haystack = `${item.id} ${item.title} ${item.description}`.toLowerCase();
  return haystack.includes(search.trim().toLowerCase());
}

export function AdminIncidentList() {
  const [params, setParams] = useSearchParams();
  const requested = params.get('type');
  const type: IncidentTypeFilter = isIncidentType(requested) ? requested : 'all';
  const status = statusOptions.some((option) => option.value === params.get('status')) ? params.get('status')! : 'all';
  const search = params.get('q') ?? '';
  const zoneId = params.get('zone');
  const incidentsQuery = useQuery({ queryKey: ['admin-incidents'], queryFn: incidentsApi.list, retry: false });
  const zonesQuery = useQuery({ queryKey: ['admin-zones'], queryFn: zonesApi.list, retry: false });
  const zones = zonesQuery.data?.items ?? [];
  const zone = zones.find((item) => item.id === zoneId);
  const zoneName = zone?.name ?? 'All zones';
  const inZone = (incidentsQuery.data?.items ?? []).filter((item) => (zone ? item.zone_id === zone.id : true));
  const rows = inZone.filter((item) => matches(item, type, status, search));
  const typeLabel = incidentTypeOptions.find((option) => option.value === type)?.label ?? 'All incident types';
  const totals = [
    { label: 'Total incidents', value: rows.length, tone: 'teal' },
    { label: 'Open', value: rows.filter((item) => item.status === 'OPEN').length, tone: 'red' },
    { label: 'In progress', value: rows.filter((item) => item.status === 'IN_PROGRESS').length, tone: 'amber' },
    { label: 'Resolved', value: rows.filter((item) => item.status === 'RESOLVED' || item.status === 'CLOSED').length, tone: 'green' },
  ];

  function update(next: Record<string, string | null>) {
    const draft = new URLSearchParams(params);
    for (const [key, value] of Object.entries(next)) {
      if (!value || value === 'all') draft.delete(key);
      else draft.set(key, value);
    }
    setParams(draft);
  }

  return (
    <div className="list-shell">
      <aside className="list-sidebar">
        <div className="list-brand">
          <span>CS</span>
          <div>
            <strong>Civic SahAI</strong>
            <small>City operations</small>
          </div>
        </div>
        <div className="list-nav" aria-label="City operations">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} end={'end' in item}>
              {item.label}
            </NavLink>
          ))}
        </div>
        <p>City workspace</p>
      </aside>
      <div className="list-main">
        <header className="list-header">
          <div>
            <p className="list-crumb">Zones / {zoneName} / Reported incident types</p>
            <h1>{zoneName} incidents</h1>
            <p>Review individual incidents, current status, and response progress.</p>
          </div>
          <select
            className="list-zone"
            aria-label="Zone"
            value={zone?.id ?? 'all'}
            onChange={(event) => update({ zone: event.target.value })}
          >
            <option value="all">All zones</option>
            {zones.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </header>
        <div className="list-filters">
          <label>
            Incident type
            <select value={type} onChange={(event) => update({ type: event.target.value })}>
              {incidentTypeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span className="list-hidden">Status</span>
            <select aria-label="Status" value={status} onChange={(event) => update({ status: event.target.value })}>
              {statusOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="list-search">
            <span className="list-hidden">Search</span>
            <input
              type="search"
              placeholder="Search by incident ID, street or keyword"
              value={search}
              onChange={(event) => update({ q: event.target.value })}
            />
          </label>
        </div>
        {incidentsQuery.isLoading ? <p className="list-table">Loading incidents…</p> : null}
        {incidentsQuery.isError ? <p className="list-table">Incidents could not be loaded. Check that the API is running.</p> : null}
        {incidentsQuery.data ? (
          <>
            <section className="list-totals" aria-label={`${zoneName} incident totals`}>
              {totals.map((item) => (
                <article key={item.label} className={`tone-${item.tone}`}>
                  <p>{item.label}</p>
                  <strong>{item.value}</strong>
                </article>
              ))}
            </section>
            <section className="list-table">
              <h2>Reported incidents</h2>
              <p>
                {type === 'all'
                  ? `Incidents in ${zoneName} · select an incident to view full details`
                  : `Showing ${typeLabel.toLowerCase()} reports in ${zoneName} · select an incident to view full details`}
              </p>
              <div className="list-head">
                <span>Incident</span>
                <span>Location</span>
                <span>Reported</span>
                <span>Status</span>
                <span>Priority</span>
                <span />
              </div>
              <ul>
                {rows.length === 0 ? <li>No incidents match these filters.</li> : null}
                {rows.map((item) => {
                  const location = zones.find((entry) => entry.id === item.zone_id)?.name ?? item.zone_id;
                  const priority = priorityLabel(item.priority_score);
                  const currentStatus = statusLabel(item.status);
                  return (
                    <li key={item.id}>
                      <div>
                        <strong>{item.id}</strong>
                        <span>{item.title}</span>
                      </div>
                      <span>{location}</span>
                      <time>{formatWhen(item.created_at)}</time>
                      <em className={`tone-${tone(currentStatus)}`}>{currentStatus}</em>
                      <em className={`priority tone-${tone(priority)}`}>{priority}</em>
                      <Link to={`${INCIDENT_DETAILS}/${encodeURIComponent(item.id)}`}>View →</Link>
                    </li>
                  );
                })}
              </ul>
              <p className="list-foot">
                {type === 'all' && status === 'all' && !search
                  ? `Showing ${rows.length} of ${inZone.length} incidents`
                  : `Showing ${rows.length} matching incident${rows.length === 1 ? '' : 's'}`}
              </p>
            </section>
          </>
        ) : null}
      </div>
    </div>
  );
}
