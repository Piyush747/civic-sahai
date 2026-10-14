export const categories = ['ROAD_DAMAGE', 'WASTE', 'WATER_SUPPLY', 'STREETLIGHT', 'DRAINAGE', 'OTHER'] as const;
export type Category = typeof categories[number];
export type Status = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED';
export type ComplaintCreate = { title: string; description: string; category: Category; zone_id: string; location: { latitude: number; longitude: number; address: string } };
export type Complaint = ComplaintCreate & {
  id: string;
  status: Status;
  priority_score: number | null;
  created_at: string;
  updated_at: string;
  image_ids?: string[];
};
export type ComplaintList = { items: Complaint[]; skip: number; limit: number; total: number };

export type IncidentStatus = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED';
export type Incident = {
  id: string;
  city_id: string;
  zone_id: string;
  category: Category;
  title: string;
  description: string;
  status: IncidentStatus;
  priority_score: number | null;
  complaint_count: number;
  created_at: string;
  updated_at: string;
};
export type IncidentList = { items: Incident[]; total: number };

export type Zone = {
  id: string;
  city_id: string;
  name: string;
  population: number;
  boundary: Record<string, unknown> | null;
  created_at: string;
};
export type ZoneList = { items: Zone[]; total: number };

