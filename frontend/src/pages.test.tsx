import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Home } from './pages';

test('home page presents the report action', () => {
  render(<MemoryRouter><Home /></MemoryRouter>);
  expect(screen.getByRole('heading', { name: /small reports/i })).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /report a civic issue/i })).toBeInTheDocument();
});

