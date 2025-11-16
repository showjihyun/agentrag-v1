/**
 * Logger utility for development and production environments
 * - Development: All logs are shown
 * - Production: Only errors and warnings are shown
 */

type LogLevel = 'log' | 'info' | 'warn' | 'error' | 'debug';

class Logger {
  private get isDevelopment() {
    return process.env.NODE_ENV === 'development';
  }

  log(...args: any[]) {
    if (this.isDevelopment) {
      console.log(...args);
    }
  }

  info(...args: any[]) {
    if (this.isDevelopment) {
      console.info(...args);
    }
  }

  warn(...args: any[]) {
    console.warn(...args);
  }

  error(...args: any[]) {
    console.error(...args);
  }

  debug(...args: any[]) {
    if (this.isDevelopment) {
      console.debug(...args);
    }
  }

  group(label: string) {
    if (this.isDevelopment) {
      console.group(label);
    }
  }

  groupEnd() {
    if (this.isDevelopment) {
      console.groupEnd();
    }
  }

  table(data: any) {
    if (this.isDevelopment) {
      console.table(data);
    }
  }
}

export const logger = new Logger();
