/**
 * Plugin Error Handling
 * 플러그인 관련 에러 처리 및 사용자 친화적 메시지 변환
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
   * 기술적 에러를 사용자 친화적 메시지로 변환
   */
  static toUserFriendlyError(error: any): UserFriendlyError {
    const errorMessage = error?.message || error?.toString() || 'Unknown error';
    const errorCode = error?.code || error?.status;

    // 네트워크 에러
    if (errorMessage.includes('fetch') || errorMessage.includes('network')) {
      return {
        title: '연결 오류',
        message: '서버에 연결할 수 없습니다.',
        suggestion: '인터넷 연결을 확인하고 다시 시도해주세요.',
        action: {
          label: '다시 시도',
          onClick: () => window.location.reload()
        },
        severity: 'error'
      };
    }

    // 인증 에러
    if (errorCode === 401 || errorMessage.includes('unauthorized')) {
      return {
        title: '인증 필요',
        message: '로그인이 필요합니다.',
        suggestion: '다시 로그인해주세요.',
        action: {
          label: '로그인',
          onClick: () => window.location.href = '/login'
        },
        severity: 'warning'
      };
    }

    // 권한 에러
    if (errorCode === 403 || errorMessage.includes('forbidden')) {
      return {
        title: '권한 부족',
        message: '이 작업을 수행할 권한이 없습니다.',
        suggestion: '관리자에게 문의하여 권한을 요청해주세요.',
        severity: 'warning'
      };
    }

    // 플러그인 설치 에러
    if (errorMessage.includes('installation') || errorMessage.includes('install')) {
      return {
        title: '설치 실패',
        message: '플러그인 설치 중 오류가 발생했습니다.',
        suggestion: '플러그인 소스를 확인하고 다시 시도해주세요.',
        action: {
          label: '다시 설치',
          onClick: () => {} // 호출하는 곳에서 구현
        },
        severity: 'error'
      };
    }

    // 플러그인 설정 에러
    if (errorMessage.includes('configuration') || errorMessage.includes('config')) {
      return {
        title: '설정 오류',
        message: '플러그인 설정에 문제가 있습니다.',
        suggestion: '설정 값을 확인하고 올바른 형식으로 입력해주세요.',
        severity: 'warning'
      };
    }

    // 플러그인 실행 에러
    if (errorMessage.includes('execution') || errorMessage.includes('runtime')) {
      return {
        title: '실행 오류',
        message: '플러그인 실행 중 오류가 발생했습니다.',
        suggestion: '플러그인 로그를 확인하고 설정을 점검해주세요.',
        action: {
          label: '로그 보기',
          onClick: () => {} // 호출하는 곳에서 구현
        },
        severity: 'error'
      };
    }

    // 의존성 에러
    if (errorMessage.includes('dependency') || errorMessage.includes('dependencies')) {
      return {
        title: '의존성 오류',
        message: '필요한 의존성이 설치되지 않았습니다.',
        suggestion: '의존성을 설치하거나 플러그인을 다시 설치해주세요.',
        action: {
          label: '의존성 설치',
          onClick: () => {} // 호출하는 곳에서 구현
        },
        severity: 'warning'
      };
    }

    // 검증 에러
    if (errorMessage.includes('validation') || errorMessage.includes('invalid')) {
      return {
        title: '입력 오류',
        message: '입력한 정보가 올바르지 않습니다.',
        suggestion: '입력 형식을 확인하고 다시 입력해주세요.',
        severity: 'warning'
      };
    }

    // 타임아웃 에러
    if (errorMessage.includes('timeout') || errorMessage.includes('시간 초과')) {
      return {
        title: '시간 초과',
        message: '작업이 시간 초과되었습니다.',
        suggestion: '잠시 후 다시 시도하거나 타임아웃 설정을 늘려보세요.',
        action: {
          label: '다시 시도',
          onClick: () => {} // 호출하는 곳에서 구현
        },
        severity: 'warning'
      };
    }

    // 서버 에러
    if (errorCode >= 500) {
      return {
        title: '서버 오류',
        message: '서버에서 오류가 발생했습니다.',
        suggestion: '잠시 후 다시 시도해주세요. 문제가 지속되면 관리자에게 문의하세요.',
        action: {
          label: '다시 시도',
          onClick: () => window.location.reload()
        },
        severity: 'error'
      };
    }

    // 기본 에러
    return {
      title: '오류 발생',
      message: errorMessage,
      suggestion: '문제가 지속되면 관리자에게 문의해주세요.',
      severity: 'error'
    };
  }

  /**
   * 플러그인별 특화 에러 메시지
   */
  static getPluginSpecificError(pluginType: string, error: any): UserFriendlyError {
    const baseError = this.toUserFriendlyError(error);

    switch (pluginType) {
      case 'vector_search':
        if (error.message?.includes('collection')) {
          return {
            ...baseError,
            title: '벡터 검색 오류',
            message: 'Milvus 컬렉션에 접근할 수 없습니다.',
            suggestion: '컬렉션 이름을 확인하고 Milvus 서버 상태를 점검해주세요.'
          };
        }
        break;

      case 'web_search':
        if (error.message?.includes('rate limit')) {
          return {
            ...baseError,
            title: '검색 제한',
            message: '검색 요청 한도를 초과했습니다.',
            suggestion: '잠시 후 다시 시도하거나 검색 빈도를 줄여주세요.'
          };
        }
        break;

      case 'local_data':
        if (error.message?.includes('path') || error.message?.includes('file')) {
          return {
            ...baseError,
            title: '파일 접근 오류',
            message: '지정된 파일이나 경로에 접근할 수 없습니다.',
            suggestion: '파일 경로와 권한을 확인해주세요.'
          };
        }
        break;
    }

    return baseError;
  }

  /**
   * 에러 심각도에 따른 색상 반환
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
   * 에러 심각도에 따른 아이콘 반환
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
 * 에러 토스트 표시 헬퍼
 */
export const showPluginError = (error: any, pluginType?: string) => {
  const userError = pluginType 
    ? PluginErrorHandler.getPluginSpecificError(pluginType, error)
    : PluginErrorHandler.toUserFriendlyError(error);

  // toast 라이브러리 사용 (sonner)
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
 * 에러 복구 제안 생성
 */
export const generateRecoverySuggestions = (error: any, context: {
  pluginId?: string;
  pluginType?: string;
  operation?: string;
}): string[] => {
  const suggestions: string[] = [];
  const errorMessage = error?.message || '';

  // 일반적인 복구 제안
  suggestions.push('페이지를 새로고침해보세요');
  suggestions.push('잠시 후 다시 시도해보세요');

  // 컨텍스트별 제안
  if (context.operation === 'install') {
    suggestions.push('플러그인 소스 URL을 확인해보세요');
    suggestions.push('네트워크 연결 상태를 점검해보세요');
    suggestions.push('다른 플러그인 소스를 시도해보세요');
  }

  if (context.operation === 'config') {
    suggestions.push('설정 값의 형식을 확인해보세요');
    suggestions.push('필수 필드가 모두 입력되었는지 확인해보세요');
    suggestions.push('이전 설정으로 복원해보세요');
  }

  if (context.operation === 'execute') {
    suggestions.push('플러그인 설정을 점검해보세요');
    suggestions.push('플러그인 로그를 확인해보세요');
    suggestions.push('플러그인을 재시작해보세요');
  }

  // 플러그인 타입별 제안
  if (context.pluginType === 'vector_search') {
    suggestions.push('Milvus 서버 연결 상태를 확인해보세요');
    suggestions.push('컬렉션 이름이 올바른지 확인해보세요');
  }

  if (context.pluginType === 'web_search') {
    suggestions.push('인터넷 연결 상태를 확인해보세요');
    suggestions.push('검색 엔진 설정을 점검해보세요');
  }

  if (context.pluginType === 'local_data') {
    suggestions.push('파일 경로가 존재하는지 확인해보세요');
    suggestions.push('파일 접근 권한을 확인해보세요');
  }

  return suggestions.slice(0, 5); // 최대 5개 제안
};