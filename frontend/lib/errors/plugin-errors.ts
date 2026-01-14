/**
 * Plugin Error Handling
 * Plugin-related error handling and user-friendly message conversion
 */

export interface UserFriendlyError {
  title: string;
  message: string;
  suggestion?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  severity: 'info' | 'warning' | 'error' | 'critical';
}

export class PluginErrorHandler {
  /**
   * Convert technical errors to user-friendly messages
   */
  static toUserFriendlyError(error: any): UserFriendlyError {
    const errorMessage = error?.message || error?.toString() || 'Unknown error';
    const errorCode = error?.code || error?.status;

    // Network error
    if (errorMessage.includes('fetch') || errorMessage.includes('network')) {
      return {
        title: 'Connection Error',
        message: 'Unable to connect to the server.',
        suggestion: 'Please check your internet connection and try again.',
        action: {
          label: 'Retry',
          onClick: () => window.location.reload()
        },
        severity: 'error'
      };
    }

    // Authentication error
    if (errorCode === 401 || errorMessage.includes('unauthorized')) {
      return {
        title: 'Authentication Required',
        message: 'Login is required.',
        suggestion: 'Please log in again.',
        action: {
          label: 'Login',
          onClick: () => window.location.href = '/login'
        },
        severity: 'warning'
      };
    }

    // Permission error
    if (errorCode === 403 || errorMessage.includes('forbidden')) {
      return {
        title: 'Insufficient Permissions',
        message: 'You do not have permission to perform this action.',
        suggestion: 'Please contact an administrator to request permissions.',
        severity: 'warning'
      };
    }

    // Plugin installation error
    if (errorMessage.includes('installation') || errorMessage.includes('install')) {
      return {
        title: 'Installation Failed',
        message: 'An error occurred during plugin installation.',
        suggestion: 'Please verify the plugin source and try again.',
        action: {
          label: 'Reinstall',
          onClick: () => {} // Implemented by caller
        },
        severity: 'error'
      };
    }

    // Plugin configuration error
    if (errorMessage.includes('configuration') || errorMessage.includes('config')) {
      return {
        title: 'Configuration Error',
        message: 'There is a problem with the plugin configuration.',
        suggestion: 'Please check the configuration values and enter them in the correct format.',
        severity: 'warning'
      };
    }

    // Plugin execution error
    if (errorMessage.includes('execution') || errorMessage.includes('runtime')) {
      return {
        title: 'Execution Error',
        message: 'An error occurred during plugin execution.',
        suggestion: 'Please check the plugin logs and review the configuration.',
        action: {
          label: 'View Logs',
          onClick: () => {} // Implemented by caller
        },
        severity: 'error'
      };
    }

    // Dependency error
    if (errorMessage.includes('dependency') || errorMessage.includes('dependencies')) {
      return {
        title: 'Dependency Error',
        message: 'Required dependencies are not installed.',
        suggestion: 'Please install the dependencies or reinstall the plugin.',
        action: {
          label: 'Install Dependencies',
          onClick: () => {} // Implemented by caller
        },
        severity: 'warning'
      };
    }

    // Validation error
    if (errorMessage.includes('validation') || errorMessage.includes('invalid')) {
      return {
        title: 'Input Error',
        message: 'The entered information is not valid.',
        suggestion: 'Please check the input format and try again.',
        severity: 'warning'
      };
    }

    // Timeout error
    if (errorMessage.includes('timeout')) {
      return {
        title: 'Timeout',
        message: 'The operation has timed out.',
        suggestion: 'Please try again later or increase the timeout setting.',
        action: {
          label: 'Retry',
          onClick: () => {} // Implemented by caller
        },
        severity: 'warning'
      };
    }

    // Server error
    if (errorCode >= 500) {
      return {
        title: 'Server Error',
        message: 'An error occurred on the server.',
        suggestion: 'Please try again later. If the problem persists, contact an administrator.',
        action: {
          label: 'Retry',
          onClick: () => window.location.reload()
        },
        severity: 'error'
      };
    }

    // Default error
    return {
      title: 'Error Occurred',
      message: errorMessage,
      suggestion: 'If the problem persists, please contact an administrator.',
      severity: 'error'
    };
  }

  /**
   * Plugin-specific error messages
   */
  static getPluginSpecificError(pluginType: string, error: any): UserFriendlyError {
    const baseError = this.toUserFriendlyError(error);

    switch (pluginType) {
      case 'vector_search':
        if (error.message?.includes('collection')) {
          return {
            ...baseError,
            title: 'Vector Search Error',
            message: 'Unable to access Milvus collection.',
            suggestion: 'Please verify the collection name and check the Milvus server status.'
          };
        }
        break;

      case 'web_search':
        if (error.message?.includes('rate limit')) {
          return {
            ...baseError,
            title: 'Search Limit',
            message: 'Search request limit exceeded.',
            suggestion: 'Please try again later or reduce search frequency.'
          };
        }
        break;

      case 'local_data':
        if (error.message?.includes('path') || error.message?.includes('file')) {
          return {
            ...baseError,
            title: 'File Access Error',
            message: 'Unable to access the specified file or path.',
            suggestion: 'Please verify the file path and permissions.'
          };
        }
        break;
    }

    return baseError;
  }

  /**
   * Return color based on error severity
   */
  static getSeverityColor(severity: UserFriendlyError['severity']): string {
    switch (severity) {
      case 'info':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'warning':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'critical':
        return 'text-red-800 bg-red-100 border-red-300';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  }

  /**
   * Return icon based on error severity
   */
  static getSeverityIcon(severity: UserFriendlyError['severity']): string {
    switch (severity) {
      case 'info':
        return 'info';
      case 'warning':
        return 'alert-triangle';
      case 'error':
        return 'x-circle';
      case 'critical':
        return 'alert-circle';
      default:
        return 'help-circle';
    }
  }
}

/**
 * Error toast display helper
 */
export const showPluginError = (error: any, pluginType?: string) => {
  const userError = pluginType 
    ? PluginErrorHandler.getPluginSpecificError(pluginType, error)
    : PluginErrorHandler.toUserFriendlyError(error);

  // Using toast library (sonner)
  const { toast } = require('sonner');
  
  if (userError.severity === 'critical' || userError.severity === 'error') {
    toast.error(userError.title, {
      description: userError.message,
      action: userError.action ? {
        label: userError.action.label,
        onClick: userError.action.onClick
      } : undefined
    });
  } else if (userError.severity === 'warning') {
    toast.warning(userError.title, {
      description: userError.message,
      action: userError.action ? {
        label: userError.action.label,
        onClick: userError.action.onClick
      } : undefined
    });
  } else {
    toast.info(userError.title, {
      description: userError.message,
      action: userError.action ? {
        label: userError.action.label,
        onClick: userError.action.onClick
      } : undefined
    });
  }
};

/**
 * Generate error recovery suggestions
 */
export const generateRecoverySuggestions = (error: any, context: {
  pluginId?: string;
  pluginType?: string;
  operation?: string;
}): string[] => {
  const suggestions: string[] = [];
  const errorMessage = error?.message || '';

  // General recovery suggestions
  suggestions.push('Try refreshing the page');
  suggestions.push('Try again later');

  // Context-specific suggestions
  if (context.operation === 'install') {
    suggestions.push('Verify the plugin source URL');
    suggestions.push('Check your network connection');
    suggestions.push('Try a different plugin source');
  }

  if (context.operation === 'config') {
    suggestions.push('Check the format of configuration values');
    suggestions.push('Verify all required fields are filled');
    suggestions.push('Try restoring to previous settings');
  }

  if (context.operation === 'execute') {
    suggestions.push('Review the plugin configuration');
    suggestions.push('Check the plugin logs');
    suggestions.push('Try restarting the plugin');
  }

  // Plugin type-specific suggestions
  if (context.pluginType === 'vector_search') {
    suggestions.push('Check the Milvus server connection');
    suggestions.push('Verify the collection name is correct');
  }

  if (context.pluginType === 'web_search') {
    suggestions.push('Check your internet connection');
    suggestions.push('Review the search engine settings');
  }

  if (context.pluginType === 'local_data') {
    suggestions.push('Verify the file path exists');
    suggestions.push('Check file access permissions');
  }

  return suggestions.slice(0, 5); // Maximum 5 suggestions
};