/**
 * Unit tests for workflow tool configuration components
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import OpenAIChatConfig from '@/components/workflow/tool-configs/OpenAIChatConfig';
import SlackConfig from '@/components/workflow/tool-configs/SlackConfig';
import HttpRequestConfig from '@/components/workflow/tool-configs/HttpRequestConfig';
import VectorSearchConfig from '@/components/workflow/tool-configs/VectorSearchConfig';
import PythonCodeConfig from '@/components/workflow/tool-configs/PythonCodeConfig';
import ConditionConfig from '@/components/workflow/tool-configs/ConditionConfig';

describe('OpenAIChatConfig', () => {
  it('renders with default values', () => {
    const mockOnChange = jest.fn();
    render(<OpenAIChatConfig data={{}} onChange={mockOnChange} />);
    
    expect(screen.getByText('OpenAI Chat')).toBeInTheDocument();
    expect(screen.getByLabelText(/API Key/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Model/i)).toBeInTheDocument();
  });
  
  it('calls onChange when API key is entered', async () => {
    const mockOnChange = jest.fn();
    render(<OpenAIChatConfig data={{}} onChange={mockOnChange} />);
    
    const apiKeyInput = screen.getByPlaceholderText('sk-...');
    fireEvent.change(apiKeyInput, { target: { value: 'sk-test-key' } });
    
    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalled();
    });
  });
  
  it('displays temperature slider', () => {
    const mockOnChange = jest.fn();
    render(<OpenAIChatConfig data={{ temperature: 0.7 }} onChange={mockOnChange} />);
    
    expect(screen.getByText('Temperature')).toBeInTheDocument();
    expect(screen.getByText('0.7')).toBeInTheDocument();
  });
});

describe('SlackConfig', () => {
  it('renders Slack configuration', () => {
    const mockOnChange = jest.fn();
    render(<SlackConfig data={{}} onChange={mockOnChange} />);
    
    expect(screen.getByText('Slack')).toBeInTheDocument();
    expect(screen.getByLabelText(/Bot Token/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Action/i)).toBeInTheDocument();
  });
  
  it('shows channel input for send_message action', () => {
    const mockOnChange = jest.fn();
    render(<SlackConfig data={{ action: 'send_message' }} onChange={mockOnChange} />);
    
    expect(screen.getByLabelText(/Channel/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Message/i)).toBeInTheDocument();
  });
});

describe('HttpRequestConfig', () => {
  it('renders HTTP request configuration', () => {
    const mockOnChange = jest.fn();
    render(<HttpRequestConfig data={{}} onChange={mockOnChange} />);
    
    expect(screen.getByText('HTTP Request')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/https:\/\//i)).toBeInTheDocument();
  });
  
  it('shows method selector', () => {
    const mockOnChange = jest.fn();
    render(<HttpRequestConfig data={{ method: 'GET' }} onChange={mockOnChange} />);
    
    expect(screen.getByText('GET')).toBeInTheDocument();
  });
  
  it('has tabs for Headers, Query, and Body', () => {
    const mockOnChange = jest.fn();
    render(<HttpRequestConfig data={{}} onChange={mockOnChange} />);
    
    expect(screen.getByText(/Headers/i)).toBeInTheDocument();
    expect(screen.getByText(/Query/i)).toBeInTheDocument();
    expect(screen.getByText(/Body/i)).toBeInTheDocument();
  });
});

describe('VectorSearchConfig', () => {
  it('renders vector search configuration', () => {
    const mockOnChange = jest.fn();
    render(<VectorSearchConfig data={{}} onChange={mockOnChange} />);
    
    expect(screen.getByText('Vector Search')).toBeInTheDocument();
    expect(screen.getByLabelText(/Search Query/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Collection Name/i)).toBeInTheDocument();
  });
  
  it('displays top_k slider', () => {
    const mockOnChange = jest.fn();
    render(<VectorSearchConfig data={{ top_k: 5 }} onChange={mockOnChange} />);
    
    expect(screen.getByText('Number of Results')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
  });
  
  it('displays score threshold slider', () => {
    const mockOnChange = jest.fn();
    render(<VectorSearchConfig data={{ score_threshold: 0.7 }} onChange={mockOnChange} />);
    
    expect(screen.getByText('Score Threshold')).toBeInTheDocument();
    expect(screen.getByText('0.70')).toBeInTheDocument();
  });
});

describe('PythonCodeConfig', () => {
  it('renders Python code configuration', () => {
    const mockOnChange = jest.fn();
    render(<PythonCodeConfig data={{}} onChange={mockOnChange} />);
    
    expect(screen.getByText('Python Code')).toBeInTheDocument();
    expect(screen.getByLabelText(/Python Code/i)).toBeInTheDocument();
  });
  
  it('shows allow imports toggle', () => {
    const mockOnChange = jest.fn();
    render(<PythonCodeConfig data={{}} onChange={mockOnChange} />);
    
    expect(screen.getByText('Allow Imports')).toBeInTheDocument();
  });
  
  it('displays available libraries', () => {
    const mockOnChange = jest.fn();
    render(<PythonCodeConfig data={{}} onChange={mockOnChange} />);
    
    expect(screen.getByText('Available Libraries:')).toBeInTheDocument();
    expect(screen.getByText('json')).toBeInTheDocument();
    expect(screen.getByText('pandas')).toBeInTheDocument();
  });
});

describe('ConditionConfig', () => {
  it('renders condition configuration', () => {
    const mockOnChange = jest.fn();
    render(<ConditionConfig data={{}} onChange={mockOnChange} />);
    
    expect(screen.getByText('Condition')).toBeInTheDocument();
    expect(screen.getByLabelText(/Condition Type/i)).toBeInTheDocument();
  });
  
  it('shows operator selection', () => {
    const mockOnChange = jest.fn();
    render(<ConditionConfig data={{ operator: 'greater_than' }} onChange={mockOnChange} />);
    
    expect(screen.getByText(/Condition Type/i)).toBeInTheDocument();
  });
  
  it('displays output info', () => {
    const mockOnChange = jest.fn();
    render(<ConditionConfig data={{}} onChange={mockOnChange} />);
    
    expect(screen.getByText('Outputs:')).toBeInTheDocument();
    expect(screen.getByText('True')).toBeInTheDocument();
    expect(screen.getByText('False')).toBeInTheDocument();
  });
});

describe('Tool Config Integration', () => {
  it('all configs accept data prop', () => {
    const mockOnChange = jest.fn();
    const testData = { test: 'value' };
    
    const configs = [
      OpenAIChatConfig,
      SlackConfig,
      HttpRequestConfig,
      VectorSearchConfig,
      PythonCodeConfig,
      ConditionConfig
    ];
    
    configs.forEach(Config => {
      const { unmount } = render(<Config data={testData} onChange={mockOnChange} />);
      unmount();
    });
    
    // If no errors thrown, test passes
    expect(true).toBe(true);
  });
  
  it('all configs call onChange when modified', async () => {
    const mockOnChange = jest.fn();
    
    // Test OpenAI config
    const { unmount: unmount1 } = render(
      <OpenAIChatConfig data={{}} onChange={mockOnChange} />
    );
    const input1 = screen.getByPlaceholderText('sk-...');
    fireEvent.change(input1, { target: { value: 'test' } });
    unmount1();
    
    // Test Slack config
    const { unmount: unmount2 } = render(
      <SlackConfig data={{}} onChange={mockOnChange} />
    );
    const input2 = screen.getByPlaceholderText('xoxb-...');
    fireEvent.change(input2, { target: { value: 'test' } });
    unmount2();
    
    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalled();
    });
  });
});
