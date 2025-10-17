import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import ResponseStatusBadge from '../ResponseStatusBadge';

describe('ResponseStatusBadge', () => {
  it('renders preliminary badge correctly', () => {
    render(
      <ResponseStatusBadge
        responseType="preliminary"
        pathSource="speculative"
        confidenceScore={0.75}
      />
    );

    expect(screen.getByText('Preliminary')).toBeInTheDocument();
    expect(screen.getByText('Confidence: 75%')).toBeInTheDocument();
    expect(screen.getByText('via speculative')).toBeInTheDocument();
  });

  it('renders refinement badge with refining indicator', () => {
    render(
      <ResponseStatusBadge
        responseType="refinement"
        pathSource="agentic"
        confidenceScore={0.85}
        isRefining={true}
      />
    );

    expect(screen.getByText('Refining...')).toBeInTheDocument();
    expect(screen.getByText('Processing deeper analysis...')).toBeInTheDocument();
  });

  it('renders final badge correctly', () => {
    render(
      <ResponseStatusBadge
        responseType="final"
        pathSource="hybrid"
        confidenceScore={0.92}
      />
    );

    expect(screen.getByText('Complete')).toBeInTheDocument();
    expect(screen.getByText('Confidence: 92%')).toBeInTheDocument();
  });

  it('shows appropriate confidence color based on score', () => {
    const { rerender } = render(
      <ResponseStatusBadge
        responseType="preliminary"
        confidenceScore={0.9}
      />
    );

    let confidenceElement = screen.getByText('Confidence: 90%');
    expect(confidenceElement).toHaveClass('text-green-600');

    rerender(
      <ResponseStatusBadge
        responseType="preliminary"
        confidenceScore={0.65}
      />
    );

    confidenceElement = screen.getByText('Confidence: 65%');
    expect(confidenceElement).toHaveClass('text-yellow-600');

    rerender(
      <ResponseStatusBadge
        responseType="preliminary"
        confidenceScore={0.45}
      />
    );

    confidenceElement = screen.getByText('Confidence: 45%');
    expect(confidenceElement).toHaveClass('text-orange-600');
  });

  it('does not render when responseType is undefined', () => {
    const { container } = render(<ResponseStatusBadge />);
    expect(container.firstChild).toBeNull();
  });

  it('renders without confidence score', () => {
    render(
      <ResponseStatusBadge
        responseType="preliminary"
        pathSource="speculative"
      />
    );

    expect(screen.getByText('Preliminary')).toBeInTheDocument();
    expect(screen.queryByText(/Confidence:/)).not.toBeInTheDocument();
  });
});
