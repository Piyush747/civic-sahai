import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { expect, test, vi } from 'vitest';
import { Home } from './pages';

vi.mock('./api', () => ({
  complaintsApi: {
    list: vi.fn().mockResolvedValue({ items: [], skip: 0, limit: 20, total: 0 }),
  },
}));

function renderHome() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <Home />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

test('home dashboard presents the report action from the Figma design', async () => {
  renderHome();
  expect(screen.getByRole('heading', { name: /good (morning|afternoon|evening), piyush/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /report an issue/i })).toHaveAttribute(
    'href',
    '/citizen/complaints/new/usr-id=101',
  );
  expect(await screen.findByText(/your recent complaints/i)).toBeInTheDocument();
});
