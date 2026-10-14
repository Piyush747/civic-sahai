import { useLocation, useParams } from 'react-router-dom';

export const DEFAULT_CITIZEN_USER_ID = '1001';
export const ADMIN_HOME = '/admin/home';

export function citizenUserIdFromPath(pathname: string, param?: string) {
  const source = param || pathname;
  const match = source.match(/(?:^|\/)usr-id=([^/]+)/);
  return match?.[1] || DEFAULT_CITIZEN_USER_ID;
}

export function citizenPaths(userId: string) {
  const suffix = `usr-id=${userId}`;
  return {
    home: `/citizen/home/${suffix}`,
    complaints: `/citizen/complaints/${suffix}`,
    newComplaint: `/citizen/complaints/new/${suffix}`,
    complaint: (id: string) => `/citizen/complaints/${id}/${suffix}`,
  };
}

export function useCitizenUserId() {
  const { userRef } = useParams();
  const { pathname } = useLocation();
  return citizenUserIdFromPath(pathname, userRef);
}

export function useCitizenPaths() {
  return citizenPaths(useCitizenUserId());
}
