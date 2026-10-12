import axios from 'axios';
import type { Complaint, ComplaintCreate, ComplaintList } from './types';

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
});

const citizenUserId = import.meta.env.VITE_CITIZEN_USER_ID || 'user_citizen_01';

export const complaintsApi = {
  list: async () =>
    (await http.get<ComplaintList>('/api/v1/complaints', { params: { limit: 100 } })).data,
  get: async (id: string) => (await http.get<Complaint>(`/api/v1/complaints/${id}`)).data,
  create: async (payload: ComplaintCreate) =>
    (
      await http.post<Complaint>('/api/v1/complaints', payload, {
        headers: { 'X-User-Id': citizenUserId },
      })
    ).data,
};
