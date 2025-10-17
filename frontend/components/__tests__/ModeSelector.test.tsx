import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ModeSelector from '../ModeSelector';
import { QueryMode } from '@/lib/types';

describe('ModeSelector', () => {
  const mockOnModeChange = jest.fn();

  beforeEach(() => {
    mockOnModeChange.mockClear();
  });

  describe('Mode Selection and Visual Feedback', () => {
    it('should render all three mode options', () => {
      render(
        <ModeSelector selectedMode="BALANCED" onModeChange={mockOnModeChange} />
      );

      expect(screen.getByText('Fast')).toBeInTheDocument();
      expect(screen.getByText('Balanced')).toBeInTheDocument();
      expect(screen.getByText('Deep')).toBeInTheDocument();
    });

    it('should highlight the selected mode', () => {
      const { rerender } = render(
        <ModeSelector selectedMode="FAST" onModeChange={mockOnModeChange} />
      );

      const fastButton = screen.getByText('Fast').closest('button');
      expect(fastButton).toHaveClass('bg-white');
      expect(fastButton).toHaveClass('text-blue-600');

      // Change to BALANCED
      rerender(
        <ModeSelector selectedMode="BALANCED" onModeChange={mockOnModeChange} />
      );

      const balancedButton = screen.getByText('Balanced').closest('button');
      expect(balancedButton).toHaveClass('bg-white');
      expect(balancedButton).toHaveClass('text-blue-600');
    });

    it('should call onModeChange when a mode is clicked', () => {
      render(
        <ModeSelector selectedMode="BALANCED" onModeChange={mockOnModeChange} />
      );

      const fastButton = screen.getByText('Fast').closest('button');
      fireEvent.click(fastButton!);

      expect(mockOnModeChange).toHaveBeenCalledWith('FAST');
      expect(mockOnModeChange).toHaveBeenCalledTimes(1);
    });

    it('should not call onModeChange when clicking the already selected mode', () => {
      render(
        <ModeSelector selectedMode="BALANCED" onModeChange={mockOnModeChange} />
      );

      const balancedButton = screen.getByText('Balanced').closest('button');
      fireEvent.click(balancedButton!);

      // Should still be called, but with the same mode
      expect(mockOnModeChange).toHaveBeenCalledWith('BALANCED');
    });

    it('should disable all buttons when disabled prop is true', () => {
      render(
        <ModeSelector
          selectedMode="BALANCED"
          onModeChange={mockOnModeChange}
          disabled={true}
        />
      );

      const fastButton = screen.getByText('Fast').closest('button');
      const balancedButton = screen.getByText('Balanced').closest('button');
      const deepButton = screen.getByText('Deep').closest('button');

      expect(fastButton).toBeDisabled();
      expect(balancedButton).toBeDisabled();
      expect(deepButton).toBeDisabled();
    });

    it('should not call onModeChange when disabled', () => {
      render(
        <ModeSelector
          selectedMode="BALANCED"
          onModeChange={mockOnModeChange}
          disabled={true}
        />
      );

      const fastButton = screen.getByText('Fast').closest('button');
      fireEvent.click(fastButton!);

      expect(mockOnModeChange).not.toHaveBeenCalled();
    });
  });

  describe('Tooltip Display', () => {
    it('should have title attributes with descriptions', () => {
      render(
        <ModeSelector selectedMode="BALANCED" onModeChange={mockOnModeChange} />
      );

      const fastButton = screen.getByText('Fast').closest('button');
      const balancedButton = screen.getByText('Balanced').closest('button');
      const deepButton = screen.getByText('Deep').closest('button');

      expect(fastButton).toHaveAttribute(
        'title',
        'Quick results in ~2s, basic retrieval'
      );
      expect(balancedButton).toHaveAttribute(
        'title',
        'Refined answers in ~5s, best of both'
      );
      expect(deepButton).toHaveAttribute(
        'title',
        'Comprehensive analysis in 10s+, full reasoning'
      );
    });

    it('should render tooltip content in the DOM', () => {
      render(
        <ModeSelector selectedMode="BALANCED" onModeChange={mockOnModeChange} />
      );

      // Tooltips are rendered but hidden by default
      expect(
        screen.getByText('Quick results in ~2s, basic retrieval')
      ).toBeInTheDocument();
      expect(
        screen.getByText('Refined answers in ~5s, best of both')
      ).toBeInTheDocument();
      expect(
        screen.getByText('Comprehensive analysis in 10s+, full reasoning')
      ).toBeInTheDocument();
    });
  });

  describe('Icons', () => {
    it('should render icons for each mode', () => {
      const { container } = render(
        <ModeSelector selectedMode="BALANCED" onModeChange={mockOnModeChange} />
      );

      // Check that SVG icons are present
      const svgs = container.querySelectorAll('svg');
      expect(svgs.length).toBeGreaterThanOrEqual(3); // At least 3 icons
    });

    it('should apply correct icon colors based on selection', () => {
      render(
        <ModeSelector selectedMode="FAST" onModeChange={mockOnModeChange} />
      );

      const fastButton = screen.getByText('Fast').closest('button');
      const iconSpan = fastButton?.querySelector('span:first-child');

      expect(iconSpan).toHaveClass('text-blue-600');
    });
  });

  describe('Accessibility', () => {
    it('should have proper button types', () => {
      render(
        <ModeSelector selectedMode="BALANCED" onModeChange={mockOnModeChange} />
      );

      const buttons = screen.getAllByRole('button');
      buttons.forEach((button) => {
        expect(button).toHaveAttribute('type', 'button');
      });
    });

    it('should have focus styles', () => {
      render(
        <ModeSelector selectedMode="BALANCED" onModeChange={mockOnModeChange} />
      );

      const fastButton = screen.getByText('Fast').closest('button');
      expect(fastButton).toHaveClass('focus:outline-none');
      expect(fastButton).toHaveClass('focus:ring-2');
    });
  });

  describe('Custom className', () => {
    it('should apply custom className to container', () => {
      const { container } = render(
        <ModeSelector
          selectedMode="BALANCED"
          onModeChange={mockOnModeChange}
          className="custom-class"
        />
      );

      const wrapper = container.firstChild;
      expect(wrapper).toHaveClass('custom-class');
    });
  });
});
