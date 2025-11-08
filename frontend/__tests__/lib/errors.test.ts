import {
  APIError,
  ValidationError,
  AuthenticationError,
  AuthorizationError,
  NotFoundError,
  NetworkError,
  ErrorHandler,
  fetchWithRetry,
} from '@/lib/errors';

describe('Error Classes', () => {
  describe('APIError', () => {
    it('should create API error with correct properties', () => {
      const error = new APIError(500, 'SERVER_ERROR', 'Server error occurred');

      expect(error.status).toBe(500);
      expect(error.code).toBe('SERVER_ERROR');
      expect(error.message).toBe('Server error occurred');
      expect(error.name).toBe('APIError');
    });

    it('should identify API errors', () => {
      const error = new APIError(500, 'ERROR', 'Error');
      expect(APIError.isAPIError(error)).toBe(true);
      expect(APIError.isAPIError(new Error())).toBe(false);
    });
  });

  describe('ValidationError', () => {
    it('should create validation error', () => {
      const error = new ValidationError('Invalid input');

      expect(error.status).toBe(400);
      expect(error.code).toBe('VALIDATION_ERROR');
      expect(error.message).toBe('Invalid input');
    });
  });

  describe('AuthenticationError', () => {
    it('should create authentication error', () => {
      const error = new AuthenticationError();

      expect(error.status).toBe(401);
      expect(error.code).toBe('AUTHENTICATION_ERROR');
      expect(error.message).toBe('Authentication required');
    });
  });

  describe('NotFoundError', () => {
    it('should create not found error', () => {
      const error = new NotFoundError('Agent');

      expect(error.status).toBe(404);
      expect(error.message).toBe('Agent not found');
    });
  });
});

describe('ErrorHandler', () => {
  describe('handle', () => {
    it('should handle ValidationError', () => {
      const error = new ValidationError('Invalid input');
      const result = ErrorHandler.handle(error);

      expect(result.title).toBe('Validation Error');
      expect(result.description).toBe('Invalid input');
      expect(result.variant).toBe('destructive');
    });

    it('should handle AuthenticationError', () => {
      const error = new AuthenticationError();
      const result = ErrorHandler.handle(error);

      expect(result.title).toBe('Authentication Required');
      expect(result.description).toBe('Please log in to continue');
    });

    it('should handle NetworkError', () => {
      const error = new NetworkError();
      const result = ErrorHandler.handle(error);

      expect(result.title).toBe('Network Error');
      expect(result.description).toContain('connection');
    });

    it('should handle generic Error', () => {
      const error = new Error('Something went wrong');
      const result = ErrorHandler.handle(error);

      expect(result.title).toBe('Error');
      expect(result.description).toBe('Something went wrong');
    });

    it('should handle unknown errors', () => {
      const result = ErrorHandler.handle('string error');

      expect(result.title).toBe('Error');
      expect(result.description).toBe('An unexpected error occurred');
    });
  });

  describe('log', () => {
    it('should log errors to console', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      const error = new Error('Test error');

      ErrorHandler.log(error, 'TestContext');

      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining('[TestContext]'),
        error
      );

      consoleSpy.mockRestore();
    });
  });
});

describe('fetchWithRetry', () => {
  it('should succeed on first attempt', async () => {
    const fn = jest.fn().mockResolvedValue('success');

    const result = await fetchWithRetry(fn);

    expect(result).toBe('success');
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('should retry on failure', async () => {
    const fn = jest
      .fn()
      .mockRejectedValueOnce(new Error('Fail 1'))
      .mockRejectedValueOnce(new Error('Fail 2'))
      .mockResolvedValue('success');

    const result = await fetchWithRetry(fn, { delay: 10 });

    expect(result).toBe('success');
    expect(fn).toHaveBeenCalledTimes(3);
  });

  it('should not retry client errors', async () => {
    const error = new ValidationError('Invalid');
    const fn = jest.fn().mockRejectedValue(error);

    await expect(fetchWithRetry(fn, { delay: 10 })).rejects.toThrow(error);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it('should throw after max retries', async () => {
    const error = new NetworkError();
    const fn = jest.fn().mockRejectedValue(error);

    await expect(
      fetchWithRetry(fn, { maxRetries: 3, delay: 10 })
    ).rejects.toThrow(error);
    expect(fn).toHaveBeenCalledTimes(3);
  });

  it('should use exponential backoff', async () => {
    jest.useFakeTimers();
    const fn = jest
      .fn()
      .mockRejectedValueOnce(new Error('Fail'))
      .mockResolvedValue('success');

    const promise = fetchWithRetry(fn, { delay: 100, backoff: 2 });

    // First call fails immediately
    await Promise.resolve();
    expect(fn).toHaveBeenCalledTimes(1);

    // Wait for retry delay (100ms)
    jest.advanceTimersByTime(100);
    await Promise.resolve();

    expect(fn).toHaveBeenCalledTimes(2);
    await expect(promise).resolves.toBe('success');

    jest.useRealTimers();
  });
});
