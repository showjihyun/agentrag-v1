import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ResponseComparison from '../ResponseComparison';

describe('ResponseComparison', () => {
  it('renders current content without comparison toggle when no previous content', () => {
    render(
      <ResponseComparison
        currentContent="Current response"
        responseType="final"
      />
    );

    expect(screen.getByText('Current response')).toBeInTheDocument();
    expect(screen.queryByText('Compare versions')).not.toBeInTheDocument();
  });

  it('renders current content without comparison toggle for preliminary responses', () => {
    render(
      <ResponseComparison
        currentContent="Current response"
        previousContent="Previous response"
        responseType="preliminary"
      />
    );

    expect(screen.getByText('Current response')).toBeInTheDocument();
    expect(screen.queryByText('Compare versions')).not.toBeInTheDocument();
  });

  it('shows comparison toggle when previous content exists and differs', () => {
    render(
      <ResponseComparison
        currentContent="Updated response"
        previousContent="Initial response"
        responseType="refinement"
      />
    );

    expect(screen.getByText('Compare versions')).toBeInTheDocument();
  });

  it('toggles comparison view on button click', () => {
    render(
      <ResponseComparison
        currentContent="Updated response"
        previousContent="Initial response"
        responseType="refinement"
      />
    );

    const toggleButton = screen.getByText('Compare versions');
    fireEvent.click(toggleButton);

    expect(screen.getByText('Hide comparison')).toBeInTheDocument();
    expect(screen.getByText('Initial Response')).toBeInTheDocument();
    expect(screen.getByText('Refined Response')).toBeInTheDocument();
  });

  it('displays both versions in comparison mode', () => {
    render(
      <ResponseComparison
        currentContent="Updated response with more details"
        previousContent="Updated response"
        responseType="final"
      />
    );

    const toggleButton = screen.getByText('Compare versions');
    fireEvent.click(toggleButton);

    expect(screen.getByText('Updated response')).toBeInTheDocument();
    expect(screen.getByText('Updated response with more details')).toBeInTheDocument();
  });

  it('highlights differences in refined response', () => {
    const { container } = render(
      <ResponseComparison
        currentContent="Initial text with addition"
        previousContent="Initial text"
        responseType="final"
      />
    );

    const toggleButton = screen.getByText('Compare versions');
    fireEvent.click(toggleButton);

    // Check for highlighted new content
    const highlighted = container.querySelector('.bg-green-200');
    expect(highlighted).toBeInTheDocument();
    expect(highlighted?.textContent).toContain(' with addition');
  });

  it('hides comparison when toggle is clicked again', () => {
    render(
      <ResponseComparison
        currentContent="Updated response"
        previousContent="Initial response"
        responseType="refinement"
      />
    );

    const toggleButton = screen.getByText('Compare versions');
    fireEvent.click(toggleButton);
    
    expect(screen.getByText('Hide comparison')).toBeInTheDocument();
    
    const hideButton = screen.getByText('Hide comparison');
    fireEvent.click(hideButton);

    expect(screen.getByText('Compare versions')).toBeInTheDocument();
    expect(screen.queryByText('Initial Response')).not.toBeInTheDocument();
  });

  it('does not show toggle when content is identical', () => {
    render(
      <ResponseComparison
        currentContent="Same response"
        previousContent="Same response"
        responseType="final"
      />
    );

    expect(screen.queryByText('Compare versions')).not.toBeInTheDocument();
  });
});
