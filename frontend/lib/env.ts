/**
 * Environment variable validation using Zod.
 * 
 * Ensures all required environment variables are present and valid
 * at build time, preventing runtime errors.
 */

import { z } from 'zod';

/**
 * Environment variable schema.
 */
const envSchema = z.object({
  NEXT_PUBLIC_API_URL: z
    .string()
    .url('NEXT_PUBLIC_API_URL must be a valid URL')
    .default('http://localhost:8000'),
  
  NEXT_PUBLIC_WS_URL: z
    .string()
    .url('NEXT_PUBLIC_WS_URL must be a valid URL')
    .optional(),
  
  NODE_ENV: z
    .enum(['development', 'production', 'test'])
    .default('development'),
});

/**
 * Inferred environment type.
 */
export type Env = z.infer<typeof envSchema>;

/**
 * Validate environment variables.
 */
function validateEnv(): Env {
  const parsed = envSchema.safeParse({
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL,
    NODE_ENV: process.env.NODE_ENV,
  });

  if (!parsed.success) {
    console.error('❌ Invalid environment variables:');
    console.error(JSON.stringify(parsed.error.flatten().fieldErrors, null, 2));
    
    // In development, show detailed error
    if (process.env.NODE_ENV === 'development') {
      throw new Error(
        `Environment validation failed:\n${JSON.stringify(parsed.error.flatten().fieldErrors, null, 2)}`
      );
    }
    
    // In production, use defaults but log warning
    console.warn('⚠️  Using default environment values');
    return {
      NEXT_PUBLIC_API_URL: 'http://localhost:8000',
      NODE_ENV: 'production',
    };
  }

  // Log environment in development
  if (parsed.data.NODE_ENV === 'development') {
    console.log('✅ Environment variables validated:');
    console.log(`  API_URL: ${parsed.data.NEXT_PUBLIC_API_URL}`);
    if (parsed.data.NEXT_PUBLIC_WS_URL) {
      console.log(`  WS_URL: ${parsed.data.NEXT_PUBLIC_WS_URL}`);
    }
  }

  return parsed.data;
}

/**
 * Validated environment variables.
 * 
 * Use this instead of process.env for type safety.
 * 
 * @example
 * ```ts
 * import { env } from '@/lib/env';
 * 
 * const apiClient = new RAGApiClient(env.NEXT_PUBLIC_API_URL);
 * ```
 */
export const env = validateEnv();

/**
 * Check if running in development mode.
 */
export const isDevelopment = env.NODE_ENV === 'development';

/**
 * Check if running in production mode.
 */
export const isProduction = env.NODE_ENV === 'production';

/**
 * Check if running in test mode.
 */
export const isTest = env.NODE_ENV === 'test';
