import axios from 'axios';
import type {
  CitizenComplaintCreate,
  CitizenComplaintCreated,
  CitizenComplaintDetail,
  CitizenComplaintList,
  Complaint,
  ComplaintCreate,
  ComplaintFormContent,
  ComplaintList,
  Homepage,
  IncidentList,
  LocationSearchResult,
  LocationStatus,
  ZoneList,
} from './types';

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
});

function withUser(userId: string) {
  return { headers: { 'X-User-Id': userId } };
}

export function complaintImageUrl(imageId: string) {
  const base = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
  const path = imageId
    .split('/')
    .map((part) => encodeURIComponent(part))
    .join('/');
  return `${base}/api/v1/complaint-images/${path}`;
}

export const citizenApi = {
  homepage: async (userId: string) =>
    (await http.get<{ data: Homepage }>('/api/v1/citizen/homepage', withUser(userId))).data.data,
  complaintForm: async () =>
    (await http.get<{ data: ComplaintFormContent }>('/api/v1/citizen/complaint-form')).data.data,
  locationStatus: async (latitude: number, longitude: number) =>
    (
      await http.get<{ data: LocationStatus }>('/api/v1/citizen/location-status', {
        params: { latitude, longitude },
      })
    ).data.data,
  locationSearch: async (query: string, latitude: number, longitude: number) =>
    (
      await http.get<{ data: { places: LocationSearchResult[] } }>('/api/v1/citizen/location-search', {
        params: { q: query, latitude, longitude },
      })
    ).data.data,
  createComplaint: async (userId: string, payload: CitizenComplaintCreate) =>
    (
      await http.post<{ data: CitizenComplaintCreated }>('/api/v1/citizen/complaint', payload, withUser(userId))
    ).data.data,
  complaint: async (userId: string, complaintId: string) =>
    (
      await http.get<{ data: CitizenComplaintDetail }>(
        `/api/v1/citizen/${encodeURIComponent(complaintId)}`,
        withUser(userId),
      )
    ).data.data,
  complaints: async (
    userId: string,
    query: { search?: string; status?: string; page: number; pageSize: number },
  ) => {
    const params: Record<string, string | number> = { page: query.page, pageSize: query.pageSize };
    if (query.search) params.search = query.search;
    if (query.status && query.status !== 'ALL') params.status = query.status;
    return (
      await http.get<{ data: CitizenComplaintList }>('/api/v1/citizen/complaints', {
        ...withUser(userId),
        params,
      })
    ).data.data;
  },
};

export const complaintsApi = {
  list: async (userId: string) =>
    (await http.get<ComplaintList>('/api/v1/complaints', { params: { limit: 100 }, ...withUser(userId) })).data,
  get: async (userId: string, id: string) =>
    (await http.get<Complaint>(`/api/v1/complaints/${id}`, withUser(userId))).data,
  uploadImage: async (file: File, userId: string) => {
    const data = await file.arrayBuffer();
    return (
      await http.post<{ image_id: string }>('/api/v1/complaint-images', data, {
        headers: { 'Content-Type': file.type || 'application/octet-stream', 'X-User-Id': userId },
      })
    ).data;
  },
  create: async (userId: string, payload: ComplaintCreate) =>
    (await http.post<Complaint>('/api/v1/complaints', payload, withUser(userId))).data,
};

export const incidentsApi = {
  list: async () => (await http.get<IncidentList>('/api/v1/incidents')).data,
};

export const zonesApi = {
  list: async () => (await http.get<ZoneList>('/api/v1/zones')).data,
};
