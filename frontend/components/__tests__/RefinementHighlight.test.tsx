import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import RefinementHighlight from '../RefinementHighlight';

describe('RefinementHighlight', () => {
  it('renders content correctly', () => {
    render(<RefinementHighlight content="Test content" />);
    expect(screen.getByText('Test content')).toBeInTheDocument();
  });

  it('highlights new content when previousContent is provided', () => {
    const { container } = render(
      <RefinementHighlight
        content="Initial content and new addition"
        previousContent="Initial content"
      />
    );

    expect(screen.getByText('Initial content')).toBeInTheDocument();
    expect(screen.getByText(' and new addition')).toBeInTheDocument();
  });

  it('shows refining indicator when isRefining is true', () => {
    const { container } = render(
      <RefinementHighlight
        content="Test content"
        isRefining={true}
      />
    );

    // Check for the pulsing indicator (absolute positioned element)
    const indicator = container.querySelector('.animate-ping');
    expect(indicator).toBeInTheDocument();
  });

  it('applies highlight animation on content change', async () => {
    const { rerender, container } = render(
      <RefinementHighlight
        content="Initial"
        previousContent=""
      />
    );

    rerender(
      <RefinementHighlight
        content="Initial updated"
        previousContent="Initial"
      />
    );

    // Check that highlight class is applied
    await waitFor(() => {
      const highlightedElement = container.querySelector('.bg-blue-50');
      expect(highlightedElement).toBeInTheDocument();
    });
  });

  it('removes highlight after animation duration', async () => {
    jest.useFakeTimers();
    
    const { rerender, container } = render(
      <RefinementHighlight
        content="Initial"
        previousContent=""
      />
    );

    rerender(
      <RefinementHighlight
        content="Initial updated"
        previousContent="Initial"
      />
    );

    // Fast-forward time
    jest.advanceTimersByTime(2500);

    await waitFor(() => {
      const highlightedElement = container.querySelector('.bg-blue-50');
      expect(highlightedElement).not.toBeInTheDocument();
    });

    jest.useRealTimers();
  });

  it('handles content without previous content', () => {
    render(<RefinementHighlight content="New content" />);
    expect(screen.getByText('New content')).toBeInTheDocument();
  });
});
