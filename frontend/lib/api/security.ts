/**
 * Security API Client
 * API 키 관리를 위한 클라이언트
 */

export interface CreateAPIKeyRequest {
  name: string;
  expires_in_days: number;
  scopes?: string[];
}

export interface APIKeyResponse {
  id: string;
  name: string;
  prefix: string;
  expires_at?: string;
  last_used_at?: string;
  usage_count: number;
  is_active: boolean;
  scopes: string[];
  created_at: string;
}

export interface CreateAPIKeyResponse extends APIKeyResponse {
  key: string; // ⚠️ Only returned once!
  warning: string;
}

/**
 * Create new API key
 */
export async function createAPIKey(
  data: CreateAPIKeyRequest,
  token: string
): Promise<CreateAPIKeyResponse> {
  const response = await fetch('/api/security/api-keys', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create API key');
  }

  return response.json();
}

/**
 * List all API keys
 */
export async function listAPIKeys(
  token: string,
  includeInactive = false
): Promise<APIKeyResponse[]> {
  const url = new URL('/api/security/api-keys', window.location.origin);
  if (includeInactive) {
    url.searchParams.set('include_inactive', 'true');
  }

  const response = await fetch(url.toString(), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to list API keys');
  }

  return response.json();
}

/**
 * Rotate API key
 */
export async function rotateAPIKey(
  keyId: string,
  token: string
): Promise<CreateAPIKeyResponse> {
  const response = await fetch(`/api/security/api-keys/${keyId}/rotate`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to rotate API key');
  }

  return response.json();
}

/**
 * Revoke API key
 */
export async function revokeAPIKey(keyId: string, token: string): Promise<void> {
  const response = await fetch(`/api/security/api-keys/${keyId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to revoke API key');
  }
}

/**
 * Get expiring keys
 */
export async function getExpiringKeys(
  token: string,
  daysThreshold = 7
): Promise<any[]> {
  const url = new URL('/api/security/api-keys/expiring', window.location.origin);
  url.searchParams.set('days_threshold', daysThreshold.toString());

  const response = await fetch(url.toString(), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get expiring keys');
  }

  return response.json();
}
