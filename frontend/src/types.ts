export const categories = ['ROAD_DAMAGE', 'WASTE', 'WATER_SUPPLY', 'STREETLIGHT', 'DRAINAGE', 'OTHER'] as const;
export type Category = typeof categories[number];
export type Status = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED';
export type ComplaintCreate = { title: string; description: string; category: Category; zone_id: string; location: { latitude: number; longitude: number; address: string } };
export type Complaint = ComplaintCreate & { id: string; status: Status; priority_score: number | null; created_at: string; updated_at: string };
export type ComplaintList = { items: Complaint[]; skip: number; limit: number; total: number };

