import { useQuery } from '@tanstack/react-query';
import { Link, NavLink, useSearchParams } from 'react-router-dom';
import { formatWhen, pressureCopy, waitingLabel } from './admin-format';
import { adminDashboardApi, zonesApi } from './api';
import { DEFAULT_ADMIN_USER_ID } from './paths';

export const ZONE_OVERVIEW = '/admin/zone-overview';

const navItems = [
  { to: '/admin/home', label: 'City Overview' },
  { to: ZONE_OVERVIEW, label: 'Zones', end: true },
  { to: '/admin/incident-list', label: 'Incidents' },
  { to: '/admin/allocation-review', label: 'Resource Allocation' },
  { to: '/admin/teams', label: 'Teams & Capacity' },
] as const;

const typeTones = ['amber', 'green', 'blue', 'rose', 'teal'] as const;

export function AdminZoneOverview() {
  const [params, setParams] = useSearchParams();
  const zonesQuery = useQuery({ queryKey: ['admin-zones'], queryFn: zonesApi.list, retry: false });
  const zones = zonesQuery.data?.items ?? [];
  const requested = params.get('zone');
  const zone = zones.find((item) => item.id === requested) ?? zones[0];
  const overviewQuery = useQuery({
    queryKey: ['admin-zone-overview', zone?.id],
    queryFn: () => adminDashboardApi.zoneOverview(DEFAULT_ADMIN_USER_ID, zone.id),
    enabled: Boolean(zone),
    retry: false,
  });
  const data = overviewQuery.data?.data;
  const pressure = pressureCopy(data?.zone.pressure_level ?? data?.response_health.pressure_level ?? 'balanced');
  const summary = data?.summary;
  const kpis = summary
    ? [
        { label: 'Open incidents', value: summary.open_incidents, note: 'Need action or follow-up', tone: 'red' },
        { label: 'In progress', value: summary.in_progress_incidents, note: 'Assigned and being worked on', tone: 'blue' },
        { label: 'Resolved', value: summary.resolved_incidents, note: 'Closed in the selected period', tone: 'green' },
        { label: 'Waiting too long', value: summary.waiting_too_long_incidents, note: 'Still open after 48 hours', tone: 'amber' },
      ]
    : [];
  const reported = (data?.incident_types ?? []).map((item, index) => ({
    letter: item.name.slice(0, 1).toUpperCase(),
    tone: typeTones[index % typeTones.length],
    title: item.name,
    detail: `${item.incident_count} incident${item.incident_count === 1 ? '' : 's'} in this period`,
  }));
  const volume = (data?.incident_trends ?? []).map((point) => [point.reported, point.resolved] as const);
  const peak = Math.max(1, ...volume.flat());
  const queue = data?.assignment_queue.items ?? [];
  const [featured, ...rest] = queue;
  const health = data?.response_health;
  const zoneName = data?.zone.name ?? zone?.name ?? 'Zone';

  return (
    <div className="zone-shell">
      <aside className="zone-sidebar">
        <div className="zone-brand">
          <span className="zone-mark" aria-hidden />
          <div>
            <strong>Civic SahAI</strong>
            <span>City operations</span>
          </div>
        </div>
        <div className="zone-nav" aria-label="City operations">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} end={'end' in item}>
              {item.label}
            </NavLink>
          ))}
        </div>
        <p className="zone-workspace">City workspace</p>
      </aside>
      <div className="zone-main">
        <header className="zone-header">
          <div>
            <h1>{zoneName} overview</h1>
            <p>Understand incoming demand, response progress, and where support is needed.</p>
          </div>
          <div className="zone-header-tools">
            <select
              className="zone-select"
              aria-label="Zone"
              value={zone?.id ?? ''}
              onChange={(event) => setParams({ zone: event.target.value })}
            >
              {zones.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
            {data ? <span className="zone-status">{pressure.state}</span> : null}
          </div>
        </header>
        {zonesQuery.isLoading || overviewQuery.isLoading ? <p className="zone-card">Loading zone overview…</p> : null}
        {zonesQuery.isError || overviewQuery.isError ? (
          <p className="zone-card">The zone overview could not be loaded. Check that the API is running.</p>
        ) : null}
        {!zonesQuery.isLoading && zones.length === 0 ? <p className="zone-card">No zones are available yet.</p> : null}
        {data && summary && health ? (
          <>
            <div className="zone-meta">
              <span>{overviewQuery.data?.meta.period ?? 'Selected period'}</span>
              <span>Updated {formatWhen(overviewQuery.data?.meta.data_as_of ?? '')}</span>
            </div>
            <section className="zone-kpis" aria-label={`${zoneName} totals`}>
              {kpis.map((kpi) => (
                <article key={kpi.label} className={`zone-kpi tone-${kpi.tone}`}>
                  <p>{kpi.label}</p>
                  <strong>{kpi.value}</strong>
                  <span>{kpi.note}</span>
                </article>
              ))}
            </section>
            <div className="zone-split">
              <section className="zone-card">
                <h2>Most reported incidents in {zoneName}</h2>
                <p>Related citizen complaints are grouped into a single incident</p>
                <ul>
                  {reported.length === 0 ? <li>No incidents were reported in this period.</li> : null}
                  {reported.map((item) => (
                    <li key={item.title}>
                      <span className={`zone-letter tone-${item.tone}`}>{item.letter}</span>
                      <div>
                        <strong>{item.title}</strong>
                        <span>{item.detail}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
              <section className="zone-card">
                <div className="zone-card-head">
                  <div>
                    <h2>Complaint volume over time</h2>
                    <p>Daily incidents reported vs resolved</p>
                  </div>
                  <div className="zone-legend">
                    <span className="reported">Reported</span>
                    <span className="resolved">Resolved</span>
                  </div>
                </div>
                <div className="zone-bars" aria-hidden>
                  {volume.map(([reportedCount, resolvedCount], index) => (
                    <div key={index} className="zone-bar-group">
                      <div className="zone-bar-pair">
                        <span className="reported" style={{ height: `${(reportedCount / peak) * 100}%` }} />
                        <span className="resolved" style={{ height: `${(resolvedCount / peak) * 100}%` }} />
                      </div>
                      <em>{index % 2 === 0 ? index + 1 : ''}</em>
                    </div>
                  ))}
                </div>
              </section>
            </div>
            <div className="zone-split zone-bottom">
              <section className="zone-assign">
                <header>
                  <h2>Incidents needing team assignment</h2>
                  <p>
                    {data.assignment_queue.total_count} open incident{data.assignment_queue.total_count === 1 ? '' : 's'} still
                    need a committed team.
                  </p>
                </header>
                <div className="zone-assign-body">
                  {featured ? (
                    <article className="zone-critical">
                      <div>
                        <span>{featured.priority === 'critical' ? 'P1 · Critical' : 'Needs assignment'}</span>
                        <strong>{featured.incident_type}</strong>
                        <p>
                          {zoneName} · waiting {waitingLabel(featured.created_at)}
                          {featured.waiting_too_long ? ' · waiting too long' : ''}
                        </p>
                      </div>
                      <Link to={`/admin/incident-details/${encodeURIComponent(featured.incident_id)}`}>Review →</Link>
                    </article>
                  ) : (
                    <p>No incidents are waiting for a team.</p>
                  )}
                  {rest.map((item) => (
                    <article key={item.incident_id} className="zone-queue">
                      <span className="zone-rank">{item.priority === 'critical' ? 'P1' : 'P2'}</span>
                      <div>
                        <strong>{item.incident_type}</strong>
                        <p>
                          {item.incident_id} · waiting {waitingLabel(item.created_at)}
                        </p>
                      </div>
                      <em>{item.priority ?? 'Normal'}</em>
                      <Link to={`/admin/incident-details/${encodeURIComponent(item.incident_id)}`}>Review →</Link>
                    </article>
                  ))}
                </div>
              </section>
              <section className="zone-card zone-health">
                <h2>Zone response health</h2>
                <p>Signals that affect the allocation decision</p>
                <div className="zone-risk">
                  <strong>{pressure.state}</strong>
                  <span>
                    {health.deployed_teams} of {health.total_teams} teams are deployed
                  </span>
                </div>
                <dl>
                  <div>
                    <dt>Open incidents</dt>
                    <dd>{summary.open_incidents}</dd>
                  </div>
                  <div>
                    <dt>Resolved in period</dt>
                    <dd>{summary.resolved_incidents}</dd>
                  </div>
                  <div>
                    <dt>Teams available</dt>
                    <dd>
                      {health.available_teams} teams
                      <small>
                        {health.deployed_teams} of {health.total_teams} teams deployed
                      </small>
                    </dd>
                  </div>
                </dl>
              </section>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
