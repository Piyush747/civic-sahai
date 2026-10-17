import { Link, NavLink, Outlet } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { adminDashboardApi, incidentsApi, zonesApi } from './api';
import { ADMIN_HOME, citizenPaths, DEFAULT_ADMIN_USER_ID, DEFAULT_CITIZEN_USER_ID } from './paths';

const navItems: { to: string; label: string; icon: string; end?: boolean }[] = [
  { to: ADMIN_HOME, label: 'Overview', icon: '▦', end: true },
  { to: '/admin/incidents', label: 'Incidents', icon: '◉' },
  { to: '/admin/clusters', label: 'Incident clusters', icon: '◎' },
  { to: '/admin/zones', label: 'Zones & burden', icon: '⌖' },
  { to: '/admin/reports', label: 'Reports & analytics', icon: '▤' },
];

const zoneBurden = [
  { name: 'Zone 04 · Central', open: 62, level: 'High', tone: 'critical', width: 88 },
  { name: 'Zone 02 · North', open: 48, level: 'Elevated', tone: 'elevated', width: 70 },
  { name: 'Zone 01 · East', open: 39, level: 'Moderate', tone: 'moderate', width: 56 },
  { name: 'Zone 03 · South', open: 34, level: 'Moderate', tone: 'moderate', width: 48 },
  { name: 'Zone 05 · West', open: 31, level: 'Balanced', tone: 'balanced', width: 42 },
] as const;

const demandDays = [
  { day: 'Fri', value: 46 },
  { day: 'Sat', value: 58 },
  { day: 'Sun', value: 53 },
  { day: 'Mon', value: 70 },
  { day: 'Tue', value: 64 },
  { day: 'Wed', value: 83 },
  { day: 'Thu', value: 76 },
] as const;

const openIncidents = [
  { issue: 'Road damage · 15 reports', zone: 'Central', age: '4 days', priority: 'Critical' },
  { issue: 'Water leakage · 8 reports', zone: 'North', age: '3 days', priority: 'High' },
  { issue: 'Waste overflow · 11 reports', zone: 'Central', age: '2 days', priority: 'High' },
  { issue: 'Streetlight outage · 5 reports', zone: 'South', age: '1 day', priority: 'Normal' },
] as const;

function formatOpsDate(date = new Date()) {
  return date.toLocaleDateString('en-GB', {
    weekday: 'long',
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  });
}

function priorityClass(priority: string) {
  const key = priority.toLowerCase();
  if (key === 'critical' || key === 'urgent') return 'critical';
  if (key === 'high' || key === 'recommended' || key === 'elevated') return 'elevated';
  if (key === 'balanced') return 'balanced';
  if (key === 'normal' || key === 'moderate') return 'moderate';
  return 'moderate';
}

export function AdminLayout() {
  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <div className="admin-brand">
          <Link to={ADMIN_HOME}>Civic SahAI</Link>
          <span>City administration</span>
        </div>
        <nav className="admin-nav" aria-label="Administrator">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => (isActive ? 'active' : undefined)}
            >
              <span aria-hidden>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="admin-sidebar-footer">
          <div className="admin-focus">
            <strong>Operational focus</strong>
            <p>Prioritize high-risk open issues and balance workload across zones.</p>
          </div>
          <span className="system-healthy">System healthy</span>
          <Link className="admin-citizen-link" to={citizenPaths(DEFAULT_CITIZEN_USER_ID).home}>
            ← Citizen portal
          </Link>
        </div>
      </aside>
      <div className="admin-main">
        <Outlet />
      </div>
    </div>
  );
}

export function AdminOverview() {
  const overviewQuery = useQuery({
    queryKey: ['admin-overview'],
    queryFn: () => adminDashboardApi.overview(DEFAULT_ADMIN_USER_ID),
    retry: false,
  });
  const incidentsQuery = useQuery({
    queryKey: ['admin-incidents'],
    queryFn: incidentsApi.list,
    retry: false,
  });
  const zonesQuery = useQuery({
    queryKey: ['admin-zones'],
    queryFn: zonesApi.list,
    retry: false,
  });

  const liveIncidents = incidentsQuery.data?.items ?? [];
  const liveZones = zonesQuery.data?.items ?? [];
  const usingLiveRows = liveIncidents.length > 0;
  const overview = overviewQuery.data;

  const liveOpenRows = liveIncidents
    .filter((item) => item.status === 'OPEN' || item.status === 'IN_PROGRESS')
    .slice(0, 4)
    .map((item) => {
      const ageDays = Math.max(
        1,
        Math.round((Date.now() - new Date(item.created_at).getTime()) / (1000 * 60 * 60 * 24)),
      );
      const priority =
        (item.priority_score ?? 0) >= 80 ? 'Critical' : (item.priority_score ?? 0) >= 55 ? 'High' : 'Normal';
      const zoneName = liveZones.find((zone) => zone.id === item.zone_id)?.name ?? item.zone_id;
      return {
        issue: `${item.title} · ${item.complaint_count} report${item.complaint_count === 1 ? '' : 's'}`,
        zone: zoneName,
        age: `${ageDays} day${ageDays === 1 ? '' : 's'}`,
        priority,
      };
    });

  const rows = usingLiveRows ? liveOpenRows : [...openIncidents];
  const maxDemand = Math.max(...demandDays.map((d) => d.value));

  return (
    <section className="admin-overview">
      <header className="admin-topbar">
        <div>
          <h1>City overview</h1>
          <p>Municipality operations · {formatOpsDate()}</p>
        </div>
        <div className="admin-top-actions">
          <span className="demo-badge">{usingLiveRows ? 'Mixed data' : 'Demo data'}</span>
          <button type="button" className="button export-btn">
            Export report
          </button>
        </div>
      </header>

      <div className="admin-kpi-grid">
        <article className="admin-kpi accent-blue">
          <p className="kpi-label">Reported incidents</p>
          <p className="kpi-value">{overview ? overview.incident_trends.reduce((sum, item) => sum + item.reported, 0) : '1,248'}</p>
          <p className="kpi-detail blue">↑ 12% vs last 30 days</p>
        </article>
        <article className="admin-kpi accent-teal">
          <p className="kpi-label">Active issue clusters</p>
          <p className="kpi-value">{overview ? overview.summary.open_incidents + overview.summary.in_progress_incidents : '386'}</p>
          <p className="kpi-detail teal">Distinct operational issues</p>
        </article>
        <article className="admin-kpi accent-critical">
          <p className="kpi-label">Open incidents</p>
          <p className="kpi-value">{overview ? overview.summary.open_incidents : usingLiveRows ? String(liveOpenRows.length || liveIncidents.length) : '214'}</p>
          <p className="kpi-detail critical">68 high / critical priority</p>
        </article>
        <article className="admin-kpi accent-amber">
          <p className="kpi-label">Waiting too long</p>
          <p className="kpi-value">{overview ? overview.summary.waiting_too_long_incidents : '42'}</p>
          <p className="kpi-detail amber">17 need action today</p>
        </article>
      </div>

      <div className="admin-panels">
        <article className="admin-panel burden-panel">
          <div className="panel-heading">
            <div>
              <h2>City burden by zone</h2>
              <p>Open clusters weighted by priority and estimated effort</p>
            </div>
            <span className="panel-chip teal">Open workload</span>
          </div>
          <div className="burden-list">
            {zoneBurden.map((zone) => (
              <div key={zone.name} className="burden-row">
                <span className="burden-name">{zone.name}</span>
                <div className="burden-track">
                  <span className={`burden-fill ${zone.tone}`} style={{ width: `${zone.width}%` }} />
                </div>
                <span className="burden-open">{zone.open} open</span>
                <span className={`status-chip compact ${priorityClass(zone.level)}`}>{zone.level}</span>
              </div>
            ))}
          </div>
          <p className="panel-footnote">
            Central zone has the highest reported open workload.
          </p>
        </article>

        <article className="admin-panel demand-panel">
          <div className="panel-heading">
            <div>
              <h2>Incident demand</h2>
              <p>Reports received · last 7 days</p>
            </div>
            <span className="panel-chip muted">7 days</span>
          </div>
          <div className="demand-chart" aria-label="Reports received over the last 7 days">
            {demandDays.map((entry) => (
              <div key={entry.day} className="demand-col">
                <span className="demand-value">{entry.value}</span>
                <div className="demand-bar-wrap">
                  <span
                    className="demand-bar"
                    style={{ height: `${Math.round((entry.value / maxDemand) * 100)}%` }}
                  />
                </div>
                <span className="demand-day">{entry.day}</span>
              </div>
            ))}
          </div>
          <div className="priority-breakdown">
            <span>Open work by priority</span>
            <span className="status-chip compact critical">Critical 18</span>
            <span className="status-chip compact elevated">High 50</span>
            <span className="status-chip compact moderate">Normal 146</span>
          </div>
        </article>

        <article className="admin-panel open-panel">
          <div className="panel-heading">
            <div>
              <h2>Open incidents</h2>
              <p>Priority and age help surface work needing intervention</p>
            </div>
            <Link className="text-link" to="/admin/incidents">
              View all →
            </Link>
          </div>
          <div className="open-table">
            <div className="open-table-header" aria-hidden>
              <span>Issue / cluster</span>
              <span>Zone</span>
              <span>Age</span>
              <span>Priority</span>
            </div>
            {rows.map((row) => (
              <div key={row.issue} className="open-table-row">
                <strong>{row.issue}</strong>
                <span>{row.zone}</span>
                <span>{row.age}</span>
                <span className={`status-chip compact ${priorityClass(row.priority)}`}>
                  {row.priority}
                </span>
              </div>
            ))}
          </div>
        </article>

      </div>

      <div className="city-insight">
        <div>
          <p className="insight-label">City insight</p>
          <p>
            Central zone carries the highest open workload. Review the 18 critical/high-priority cases first.
          </p>
        </div>
      </div>
    </section>
  );
}

export function AdminPlaceholder({ title }: { title: string }) {
  return (
    <section className="admin-placeholder">
      <h1>{title}</h1>
      <p>
        This section is mapped in the City Administration shell. The overview dashboard is ready;
        deeper admin screens can follow the same Figma patterns.
      </p>
      <Link className="button" to={ADMIN_HOME}>
        Back to overview
      </Link>
    </section>
  );
}
