 import { render, screen } from '@testing-library/react';
import App from './App';

test('renders Location Tracker title', () => {
  render(<App />);
  const titleElement = screen.getByText(/Location Tracker/i);
  expect(titleElement).toBeInTheDocument();
});
