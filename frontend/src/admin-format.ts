export function formatWhen(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
}

export function formatDay(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
}

export function categoryLabel(category: string) {
  const labels: Record<string, string> = {
    ROAD_DAMAGE: 'Road damage',
    WASTE_MANAGEMENT: 'Garbage not collected',
    WASTE: 'Garbage not collected',
    STREETLIGHT: 'Streetlight outage',
    WATER_SUPPLY: 'Water supply disruption',
    DRAINAGE: 'Drainage',
    PUBLIC_SAFETY: 'Public safety',
    OTHER: 'Other',
  };
  return labels[category] ?? category.replace(/_/g, ' ');
}

export function statusLabel(status: string) {
  const labels: Record<string, string> = {
    OPEN: 'Open',
    IN_PROGRESS: 'In progress',
    RESOLVED: 'Resolved',
    CLOSED: 'Closed',
  };
  return labels[status] ?? status;
}

export function priorityLabel(score: number | null) {
  if (score == null) return 'Unscored';
  if (score >= 80) return 'Critical';
  if (score >= 55) return 'High';
  if (score >= 30) return 'Medium';
  return 'Low';
}

export function pressureCopy(level: string) {
  if (level === 'overloaded') return { state: 'Overloaded', tone: 'red' };
  if (level === 'under_pressure') return { state: 'High', tone: 'amber' };
  if (level === 'spare_capacity') return { state: 'Spare capacity', tone: 'green' };
  return { state: 'Balanced', tone: 'blue' };
}

export function waitingLabel(createdAt: string) {
  const hours = Math.max(0, Math.round((Date.now() - new Date(createdAt).getTime()) / 36e5));
  if (hours < 48) return `${hours} hour${hours === 1 ? '' : 's'}`;
  const days = Math.round(hours / 24);
  return `${days} day${days === 1 ? '' : 's'}`;
}

export const incidentTypeOptions = [
  { value: 'all', label: 'All incident types' },
  { value: 'road-damage', label: 'Road damage' },
  { value: 'garbage', label: 'Garbage not collected' },
  { value: 'streetlight', label: 'Streetlight outage' },
  { value: 'water', label: 'Water supply disruption' },
] as const;

export type IncidentTypeFilter = (typeof incidentTypeOptions)[number]['value'];

const categoriesByType: Record<Exclude<IncidentTypeFilter, 'all'>, string[]> = {
  'road-damage': ['ROAD_DAMAGE'],
  garbage: ['WASTE_MANAGEMENT', 'WASTE'],
  streetlight: ['STREETLIGHT'],
  water: ['WATER_SUPPLY'],
};

export function isIncidentType(value: string | null): value is IncidentTypeFilter {
  return incidentTypeOptions.some((option) => option.value === value);
}

export function categoryMatches(type: IncidentTypeFilter, category: string) {
  if (type === 'all') return true;
  return categoriesByType[type].includes(category);
}
