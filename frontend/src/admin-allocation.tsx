import { NavLink } from 'react-router-dom';

export const ALLOCATION_REVIEW = '/admin/allocation-review';

const navItems = [
  { to: '/admin/home', label: 'City Overview' },
  { to: '/admin/zone-overview', label: 'Zones' },
  { to: '/admin/incident-list', label: 'Incidents' },
  { to: ALLOCATION_REVIEW, label: 'Resource Allocation', end: true },
  { to: '/admin/teams', label: 'Teams & Capacity' },
] as const;

const reasons = [
  ['Incident severity', 'High · road safety and access risk'],
  ['Demand vs capacity', 'East Zone has 7 unallocated incidents; 2 crews available in West'],
  ['Proximity & impact', '~1,250 residents within 500 m; bus stop 90 m away'],
  ['Response-time risk', 'Current queue forecast exceeds target by 3.5 hours'],
  ['Historic recurrence', 'Same road segment reported 3 times in six months'],
] as const;

const benefits = [
  'Addresses highest-risk queue first',
  'May reduce East Zone delay by ~3.5 h',
  'Uses spare capacity already available',
];

const risks = [
  'West Zone response buffer decreases',
  'Travel and handover time required',
  'West Zone SLA risk must be monitored',
];

const history = [
  ['Apr 22', 'Reported', 'teal'],
  ['Apr 25', 'Resolved', 'green'],
  ['Aug 03', 'Reopened', 'red'],
  ['Oct 14', 'Current', 'amber'],
] as const;

const options = [
  ['Recommended · Inter-zone', '~3.5 h faster', 'West −2 crew members', 'Strongest urgent-risk reduction'],
  ['Intra-zone reassignment', '~1.5 h faster', 'East internal queue delayed', 'Less travel; weaker coverage'],
  ['No transfer', 'Target missed by ~3.5 h', 'No cross-zone impact', 'Highest resident / SLA exposure'],
] as const;

export function AdminAllocationReview() {
  return (
    <div className="alloc-shell">
      <aside className="alloc-sidebar">
        <div className="alloc-brand">
          <span aria-hidden />
          <div>
            <strong>Civic SahAI</strong>
            <small>City operations</small>
          </div>
        </div>
        <div className="alloc-nav" aria-label="City operations">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} end={'end' in item}>
              {item.label}
            </NavLink>
          ))}
        </div>
      </aside>
      <div className="alloc-main">
        <header className="alloc-header">
          <div>
            <p className="alloc-crumb">Zones / East Zone / Resource allocation review</p>
            <h1>Review resource allocation recommendation</h1>
            <p>Recommendation RA-EAST-0248 · Road damage · Generated 14 Oct 2026, 10:42</p>
          </div>
          <span className="alloc-wait">Awaiting admin decision</span>
        </header>

        <section className="alloc-card alloc-summary">
          <div>
            <h2>Road damage near East Zone Bus Stop</h2>
            <p>INC-EAST-0248 · 8 linked complaints · Open 7 hours</p>
            <h3>Recommended strategy</h3>
            <strong>Inter-zone transfer: move 2 road-maintenance crew members from West Zone to East Zone</strong>
          </div>
          <aside>
            <span>Priority score</span>
            <strong>87 / 100</strong>
            <em>High urgency · SLA at risk</em>
          </aside>
        </section>

        <div className="alloc-split">
          <section className="alloc-card">
            <h2>Why this allocation?</h2>
            <p>Signals used by the recommendation engine</p>
            <dl>
              {reasons.map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
          </section>
          <section className="alloc-card">
            <h2>Inter-zone allocation: trade-offs</h2>
            <p>Expected impact compared with keeping all crews in their home zones</p>
            <div className="alloc-trade">
              <div className="benefits">
                <h3>Benefits</h3>
                <ul>
                  {benefits.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div className="risks">
                <h3>Costs & risks</h3>
                <ul>
                  {risks.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
            <p className="alloc-footnote">If transfer is rejected, East Zone is forecast to remain above target response time.</p>
          </section>
        </div>

        <div className="alloc-split">
          <section className="alloc-card">
            <h2>Resident & locality impact</h2>
            <p>Estimated exposure within a 500 m radius</p>
            <div className="alloc-metrics">
              <div>
                <strong>~1,250</strong>
                <span>Residents nearby</span>
              </div>
              <div>
                <strong>3</strong>
                <span>Landmarks in proximity</span>
              </div>
              <div>
                <strong>2</strong>
                <span>Access routes at risk</span>
              </div>
            </div>
            <ul className="alloc-places">
              <li>
                <strong>Eastview Government School · 180 m</strong>
              </li>
              <li>East Zone Bus Stop · 90 m — boarding and bus movement may be constrained</li>
            </ul>
            <p className="alloc-caution">Estimates support triage; confirm the exact obstruction and resident exposure on site.</p>
          </section>
          <section className="alloc-card">
            <h2>Historic pattern at this location</h2>
            <p>Same road segment · last six months</p>
            <strong className="alloc-history-count">3 prior occurrences · 2 resolved · 1 reopened</strong>
            <ol className="alloc-timeline">
              {history.map(([date, label, tone]) => (
                <li key={date} className={`tone-${tone}`}>
                  <time>{date}</time>
                  <span />
                  <em>{label}</em>
                </li>
              ))}
            </ol>
            <p>Repeated failure after repair suggests a durable fix may be needed, not a temporary patch.</p>
          </section>
        </div>

        <section className="alloc-card">
          <h2>Allocation options compared</h2>
          <p>Illustrative forecast; review operational constraints before approving</p>
          <div className="alloc-table">
            <span>Option</span>
            <span>Response forecast</span>
            <span>Capacity impact</span>
            <span>Key trade-off</span>
            {options.map((row) =>
              row.map((cell) => (
                <span key={cell} className={cell.startsWith('Recommended') ? 'recommended' : undefined}>
                  {cell}
                </span>
              )),
            )}
          </div>
        </section>

        <section className="alloc-card alloc-decision">
          <div>
            <h2>Admin decision</h2>
            <p>Accept to approve the crew transfer and record the rationale, or reject to return the recommendation for an alternative plan.</p>
          </div>
          <div className="alloc-actions">
            <button type="button" className="accept">
              Accept recommendation
            </button>
            <button type="button" className="reject">
              Reject
            </button>
          </div>
          <p className="alloc-footnote">Prototype interaction: records the intended decision path; final workflow needs a backend confirmation.</p>
        </section>

        <section className="alloc-audit">
          <h2>Decision audit trail</h2>
          <p>Record administrator, timestamp, accepted/rejected outcome, selected strategy, reason, and resulting crew assignment.</p>
        </section>
      </div>
    </div>
  );
}
