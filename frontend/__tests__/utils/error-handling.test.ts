import {
  MonitoringError,
  SSEConnectionError,
  parseSSEData,
  validateSSEEventType,
  handleSSEError,
} from '@/lib/utils/error-handling';

describe('Error Handling Utils', () => {
  describe('MonitoringError', () => {
    it('should create error with correct properties', () => {
      const error = new MonitoringError('Test message', 'TEST_CODE', { key: 'value' });
      
      expect(error.message).toBe('Test message');
      expect(error.code).toBe('TEST_CODE');
      expect(error.context).toEqual({ key: 'value' });
      expect(error.name).toBe('MonitoringError');
    });
  });

  describe('SSEConnectionError', () => {
    it('should create SSE connection error', () => {
      const error = new SSEConnectionError('Connection failed', { url: 'test-url' });
      
      expect(error.message).toBe('Connection failed');
      expect(error.code).toBe('SSE_CONNECTION_ERROR');
      expect(error.context).toEqual({ url: 'test-url' });
      expect(error.name).toBe('SSEConnectionError');
    });
  });

  describe('parseSSEData', () => {
    it('should parse valid JSON data', () => {
      const data = '{"type": "test", "payload": {"value": 123}}';
      const result = parseSSEData(data);
      
      expect(result).toEqual({ type: 'test', payload: { value: 123 } });
    });

    it('should throw MonitoringError for invalid JSON', () => {
      const invalidData = '{"invalid": json}';
      
      expect(() => parseSSEData(invalidData)).toThrow(MonitoringError);
      expect(() => parseSSEData(invalidData)).toThrow('Failed to parse SSE data');
    });

    it('should include original data in error context', () => {
      const invalidData = '{"invalid": json}';
      
      try {
        parseSSEData(invalidData);
      } catch (error) {
        expect(error).toBeInstanceOf(MonitoringError);
        expect((error as MonitoringError).context?.originalData).toBe(invalidData);
      }
    });
  });

  describe('validateSSEEventType', () => {
    const validTypes = [
      'log',
      'agent_status',
      'metrics',
      'system_metrics',
      'prediction',
      'optimization_insights',
      'execution_complete',
      'execution_failed'
    ];

    it.each(validTypes)('should return true for valid type: %s', (type) => {
      expect(validateSSEEventType(type)).toBe(true);
    });

    it.each([
      'invalid_type',
      'unknown',
      '',
      'LOG', // case sensitive
      'agent-status' // different format
    ])('should return false for invalid type: %s', (type) => {
      expect(validateSSEEventType(type)).toBe(false);
    });
  });

  describe('handleSSEError', () => {
    let consoleSpy: jest.SpyInstance;

    beforeEach(() => {
      consoleSpy = jest.spyOn(console, 'error').mockImplementation();
    });

    afterEach(() => {
      consoleSpy.mockRestore();
    });

    it('should log error to console', () => {
      const mockEvent = new Event('error');
      
      handleSSEError(mockEvent);
      
      expect(consoleSpy).toHaveBeenCalledWith('SSE connection error:', mockEvent);
    });
  });
});