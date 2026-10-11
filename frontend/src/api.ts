import axios from 'axios';
import type { Complaint, ComplaintCreate, ComplaintList } from './types';

const http = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000' });
export const complaintsApi = {
  list: async () => (await http.get<ComplaintList>('/api/v1/complaints')).data,
  get: async (id: string) => (await http.get<Complaint>(`/api/v1/complaints/${id}`)).data,
  create: async (payload: ComplaintCreate) => (await http.post<Complaint>('/api/v1/complaints', payload)).data,
};

