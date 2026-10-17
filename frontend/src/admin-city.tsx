import { useQuery } from '@tanstack/react-query';
import { Link, NavLink } from 'react-router-dom';
import { adminDashboardApi } from './api';
import { formatDay, pressureCopy } from './admin-format';
import { ADMIN_HOME, DEFAULT_ADMIN_USER_ID } from './paths';
import type { CityOverview } from './types';

const CITY_OVERVIEW = ADMIN_HOME;

const navItems = [
  { to: CITY_OVERVIEW, label: 'City Overview', icon: 'overview', end: true },
  { to: '/admin/zone-overview', label: 'Zones', icon: 'zones' },
  { to: '/admin/incident-list', label: 'Incidents', icon: 'incidents' },
  { to: '/admin/allocation-review', label: 'Resource Allocation', icon: 'allocation' },
  { to: '/admin/teams', label: 'Teams & Capacity', icon: 'teams' },
] as const;

const mapCells = ['b', 'b', 'p', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'p', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b', 'b'] as const;

const hotspotSlots = [
  { top: '30%', left: '16%' },
  { top: '24%', left: '36%' },
  { top: '32%', left: '74%' },
  { top: '64%', left: '52%' },
  { top: '70%', left: '84%' },
  { top: '58%', left: '22%' },
  { top: '12%', left: '58%' },
  { top: '78%', left: '28%' },
];

function NavIcon({ name }: { name: (typeof navItems)[number]['icon'] }) {
  const common = { width: 16, height: 16, viewBox: '0 0 16 16', fill: 'none', 'aria-hidden': true as const };
  if (name === 'overview') {
    return (
      <svg {...common}>
        <circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeWidth="1.4" />
        <circle cx="8" cy="8" r="2" fill="currentColor" />
      </svg>
    );
  }
  if (name === 'zones') {
    return (
      <svg {...common}>
        <path d="M8 2.2 13.2 8 8 13.8 2.8 8 8 2.2Z" stroke="currentColor" strokeWidth="1.4" />
      </svg>
    );
  }
  if (name === 'incidents') {
    return (
      <svg {...common}>
        <path d="M8 2.4 13.4 13H2.6L8 2.4Z" stroke="currentColor" strokeWidth="1.4" />
      </svg>
    );
  }
  if (name === 'allocation') {
    return (
      <svg {...common}>
        <path d="M3 5h8M9 3l2.5 2L9 7M13 11H5M7 9l-2.5 2L7 13" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <path d="M8 2.2 10.2 5.6 14 6.1 11.2 8.8 11.9 12.6 8 10.8 4.1 12.6 4.8 8.8 2 6.1 5.8 5.6 8 2.2Z" stroke="currentColor" strokeWidth="1.2" />
    </svg>
  );
}

function cityModel(data: CityOverview) {
  const summary = data.summary;
  const kpis = [
    { label: 'Open incidents', value: summary.open_incidents, note: 'Need action or allocation', tone: 'red' },
    { label: 'In progress', value: summary.in_progress_incidents, note: 'Teams currently responding', tone: 'blue' },
    { label: 'Resolved', value: summary.resolved_incidents, note: 'Closed in the selected period', tone: 'green' },
    { label: 'Waiting too long', value: summary.waiting_too_long_incidents, note: 'Open for more than 48 hours', tone: 'amber' },
  ];
  const maxOpen = Math.max(1, ...data.zone_pressure.map((zone) => zone.open_incidents));
  const zones = data.zone_pressure.map((zone) => {
    const pressure = pressureCopy(zone.pressure_level);
    return {
      id: zone.zone_id,
      name: zone.zone_name,
      open: zone.open_incidents,
      teams: `${zone.available_teams} / ${zone.total_teams}`,
      state: pressure.state,
      tone: pressure.tone,
      width: Math.round((zone.open_incidents / maxOpen) * 100),
    };
  });
  const hotspots = data.zone_pressure
    .filter((zone) => zone.open_incidents > 0)
    .slice(0, hotspotSlots.length)
    .map((zone, index) => ({
      id: zone.zone_id,
      count: zone.open_incidents,
      tone: pressureCopy(zone.pressure_level).tone,
      ...hotspotSlots[index],
      label: `${zone.zone_name}, ${zone.open_incidents} open incidents`,
    }));
  const peak = Math.max(1, ...data.incident_trends.flatMap((point) => [point.reported, point.resolved]));
  const trend = data.incident_trends.map((point) => ({
    day: formatDay(point.date),
    reported: point.reported,
    resolved: point.resolved,
  }));
  return { kpis, zones, hotspots, trend, peak, period: data.period ?? 'selected period' };
}

export function AdminCityOverview() {
  const query = useQuery({
    queryKey: ['admin-city-overview'],
    queryFn: () => adminDashboardApi.overview(DEFAULT_ADMIN_USER_ID),
    retry: false,
  });
  const model = query.data ? cityModel(query.data) : null;

  return (
    <div className="ops-shell">
      <aside className="ops-sidebar">
        <div className="ops-brand">
          <span className="ops-mark">C</span>
          <div>
            <strong>Civic SahAI</strong>
            <span>City operations</span>
          </div>
        </div>
        <div className="ops-nav" aria-label="City operations">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} end={'end' in item}>
              <NavIcon name={item.icon} />
              {item.label}
            </NavLink>
          ))}
        </div>
        <div className="ops-admin">
          <span>A</span>
          <div>
            <strong>City Administrator</strong>
            <p>City administration</p>
          </div>
        </div>
      </aside>
      <div className="ops-main">
        <header className="ops-header">
          <div>
            <p className="ops-eyebrow">City operations / Live overview</p>
            <h1>What is happening across the city?</h1>
            <p className="ops-lead">
              Spot where residents are waiting, compare pressure across zones, and find where spare teams can help.
            </p>
          </div>
          <div className="ops-header-tools">
            <span className="ops-range">{model ? model.period : 'Last 15 days'}</span>
            <span className="ops-live">
              <span className="ops-live-dot" aria-hidden />
              Live
            </span>
          </div>
        </header>

        {query.isLoading ? <p className="ops-panel">Loading city overview…</p> : null}
        {query.isError ? <p className="ops-panel">The city dashboard could not be loaded. Check that the API is running.</p> : null}
        {model ? (
        <section className="ops-kpis" aria-label="City totals">
          {model.kpis.map((kpi) => (
            <article key={kpi.label} className={`ops-kpi tone-${kpi.tone}`}>
              <p>{kpi.label}</p>
              <strong>{kpi.value}</strong>
              <span>{kpi.note}</span>
            </article>
          ))}
        </section>
        ) : null}

        {model ? <>
        <div className="ops-split">
          <section className="ops-panel ops-map-panel">
            <div className="ops-panel-head">
              <div>
                <h2>Incident hotspots by zone</h2>
                <p>Select any zone on the map or in the list to explore its incidents and capacity</p>
              </div>
              <button type="button" className="ops-range">
                Satellite-style view <span aria-hidden>▾</span>
              </button>
            </div>
            <div className="ops-map" role="img" aria-label="Zone hotspot map">
              <div className="ops-map-grid">
                {mapCells.map((cell, index) => (
                  <span key={index} className={cell === 'p' ? 'ops-block park' : 'ops-block'} />
                ))}
              </div>
              <span className="ops-water vertical" />
              <span className="ops-water horizontal" />
              {model.hotspots.map((spot) => (
                <Link
                  key={spot.id}
                  to={`/admin/zone-overview?zone=${encodeURIComponent(spot.id)}`}
                  className={`ops-hotspot tone-${spot.tone}`}
                  style={{ top: spot.top, left: spot.left }}
                  aria-label={spot.label}
                >
                  {spot.count}
                </Link>
              ))}
            </div>
            <div className="ops-legend">
              <span className="tone-red">Overloaded</span>
              <span className="tone-amber">Under pressure</span>
              <span className="tone-green">Capacity available</span>
            </div>
            <p className="ops-map-note">Hotspot size reflects open incident count; colour reflects demand relative to available teams.</p>
          </section>

          <section className="ops-panel">
            <h2>Explore any zone</h2>
            <p className="ops-panel-sub">Where demand exceeds local capacity</p>
            <div className="ops-zone-head">
              <span>Zone</span>
              <span>Open</span>
              <span>Teams</span>
              <span>Pressure</span>
            </div>
            <ul className="ops-zones">
              {model.zones.map((zone) => (
                <li key={zone.id}>
                  <div className="ops-zone-row">
                    <strong>
                      <span aria-hidden>›</span> {zone.name}
                    </strong>
                    <b>{zone.open}</b>
                    <span>{zone.teams}</span>
                    <em className={`tone-${zone.tone}`}>{zone.state}</em>
                  </div>
                  <div className="ops-zone-meta">
                    <span className="ops-track">
                      <span className={`tone-${zone.tone}`} style={{ width: `${zone.width}%` }} />
                    </span>
                    <Link to={`/admin/zone-overview?zone=${encodeURIComponent(zone.id)}`}>View details →</Link>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </div>

        <section className="ops-panel ops-trend">
          <div className="ops-panel-head">
            <div>
              <h2>Are things getting better?</h2>
              <p>Daily incidents reported vs. resolved · {model.period}</p>
            </div>
            <div className="ops-trend-legend">
              <span className="reported">Reported</span>
              <span className="resolved">Resolved</span>
            </div>
          </div>
          <div className="ops-plot">
            <div className="ops-y">
              <span>{model.peak}</span>
              <span>{Math.round(model.peak / 2)}</span>
              <span>0</span>
            </div>
            <div className="ops-bars">
              {model.trend.map((point, index) => (
                <div key={`${point.day}-${index}`} className="ops-bar-group">
                  <div className="ops-bar-pair">
                    <span className="reported" style={{ height: `${(point.reported / model.peak) * 100}%` }} />
                    <span className="resolved" style={{ height: `${(point.resolved / model.peak) * 100}%` }} />
                  </div>
                  <em>{index % 2 === 0 ? point.day : ''}</em>
                </div>
              ))}
            </div>
          </div>
        </section>
        </> : null}
      </div>
    </div>
  );
}
