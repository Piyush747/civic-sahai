import { beforeEach, expect, test, vi } from 'vitest';

const { get, post } = vi.hoisted(() => ({
  get: vi.fn().mockResolvedValue({ data: { data: {} } }),
  post: vi.fn().mockResolvedValue({ data: { data: { complaintId: 'cmp-1' } } }),
}));

vi.mock('axios', () => ({
  default: {
    create: () => ({ get, post }),
  },
}));

import { citizenApi } from './api';

beforeEach(() => {
  get.mockClear();
  post.mockClear();
});

test('citizen requests send X-User-Id from the caller', async () => {
  await citizenApi.homepage('101');
  expect(get).toHaveBeenCalledWith('/api/v1/citizen/homepage', { headers: { 'X-User-Id': '101' } });

  await citizenApi.complaint('1001', 'cmp-1042');
  expect(get).toHaveBeenCalledWith('/api/v1/citizen/cmp-1042', { headers: { 'X-User-Id': '1001' } });

  await citizenApi.complaints('101', { search: 'pothole', status: 'IN_PROGRESS', page: 1, pageSize: 5 });
  expect(get).toHaveBeenCalledWith('/api/v1/citizen/complaints', {
    headers: { 'X-User-Id': '101' },
    params: { search: 'pothole', status: 'IN_PROGRESS', page: 1, pageSize: 5 },
  });

  await citizenApi.createComplaint('101', {
    category: 'ROAD_DAMAGE',
    description: 'There is a large pothole near the bus stop.',
    location: { address: 'Sector 15, Main Road', latitude: 12.97, longitude: 77.64 },
    attachments: [],
  });
  expect(post).toHaveBeenCalledWith(
    '/api/v1/citizen/complaint',
    expect.any(Object),
    { headers: { 'X-User-Id': '101' } },
  );
});

test('the complaint form request does not send a user id', async () => {
  await citizenApi.complaintForm();
  expect(get).toHaveBeenCalledWith('/api/v1/citizen/complaint-form');
});
