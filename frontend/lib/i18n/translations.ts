/**
 * Translation strings for all supported languages
 */

import { Locale } from './config';

export type TranslationKey = keyof typeof translations.en;

export const translations = {
  en: {
    // Common
    'common.loading': 'Loading...',
    'common.error': 'Error',
    'common.success': 'Success',
    'common.cancel': 'Cancel',
    'common.save': 'Save',
    'common.delete': 'Delete',
    'common.edit': 'Edit',
    'common.close': 'Close',
    'common.back': 'Back',
    'common.next': 'Next',
    'common.submit': 'Submit',
    'common.search': 'Search',
    'common.filter': 'Filter',
    'common.sort': 'Sort',
    'common.refresh': 'Refresh',

    // Auth
    'auth.login': 'Login',
    'auth.logout': 'Logout',
    'auth.register': 'Register',
    'auth.email': 'Email',
    'auth.password': 'Password',
    'auth.username': 'Username',
    'auth.confirmPassword': 'Confirm Password',
    'auth.forgotPassword': 'Forgot Password?',
    'auth.rememberMe': 'Remember Me',
    'auth.loginSuccess': 'Login successful',
    'auth.loginError': 'Login failed',
    'auth.registerSuccess': 'Registration successful',
    'auth.registerError': 'Registration failed',

    // Chat
    'chat.placeholder': 'Type your message...',
    'chat.send': 'Send',
    'chat.newChat': 'New Chat',
    'chat.history': 'Chat History',
    'chat.noMessages': 'No messages yet',
    'chat.thinking': 'Thinking...',
    'chat.typing': 'Typing...',

    // Documents
    'documents.upload': 'Upload Documents',
    'documents.uploadSuccess': 'Documents uploaded successfully',
    'documents.uploadError': 'Upload failed',
    'documents.delete': 'Delete Document',
    'documents.deleteConfirm': 'Are you sure you want to delete this document?',
    'documents.noDocuments': 'No documents found',
    'documents.processing': 'Processing...',

    // Dashboard
    'dashboard.title': 'Dashboard',
    'dashboard.overview': 'Overview',
    'dashboard.usage': 'Usage',
    'dashboard.documents': 'Documents',
    'dashboard.sessions': 'Sessions',
    'dashboard.settings': 'Settings',

    // Settings
    'settings.language': 'Language',
    'settings.theme': 'Theme',
    'settings.notifications': 'Notifications',
    'settings.privacy': 'Privacy',
    'settings.account': 'Account',

    // Errors
    'error.network': 'Network error. Please check your connection.',
    'error.server': 'Server error. Please try again later.',
    'error.notFound': 'Not found',
    'error.unauthorized': 'Unauthorized. Please login.',
    'error.forbidden': 'Access forbidden',
  },

  ko: {
    // Common
    'common.loading': '로딩 중...',
    'common.error': '오류',
    'common.success': '성공',
    'common.cancel': '취소',
    'common.save': '저장',
    'common.delete': '삭제',
    'common.edit': '편집',
    'common.close': '닫기',
    'common.back': '뒤로',
    'common.next': '다음',
    'common.submit': '제출',
    'common.search': '검색',
    'common.filter': '필터',
    'common.sort': '정렬',
    'common.refresh': '새로고침',

    // Auth
    'auth.login': '로그인',
    'auth.logout': '로그아웃',
    'auth.register': '회원가입',
    'auth.email': '이메일',
    'auth.password': '비밀번호',
    'auth.username': '사용자명',
    'auth.confirmPassword': '비밀번호 확인',
    'auth.forgotPassword': '비밀번호를 잊으셨나요?',
    'auth.rememberMe': '로그인 상태 유지',
    'auth.loginSuccess': '로그인 성공',
    'auth.loginError': '로그인 실패',
    'auth.registerSuccess': '회원가입 성공',
    'auth.registerError': '회원가입 실패',

    // Chat
    'chat.placeholder': '메시지를 입력하세요...',
    'chat.send': '전송',
    'chat.newChat': '새 채팅',
    'chat.history': '채팅 기록',
    'chat.noMessages': '메시지가 없습니다',
    'chat.thinking': '생각 중...',
    'chat.typing': '입력 중...',

    // Documents
    'documents.upload': '문서 업로드',
    'documents.uploadSuccess': '문서 업로드 성공',
    'documents.uploadError': '업로드 실패',
    'documents.delete': '문서 삭제',
    'documents.deleteConfirm': '이 문서를 삭제하시겠습니까?',
    'documents.noDocuments': '문서가 없습니다',
    'documents.processing': '처리 중...',

    // Dashboard
    'dashboard.title': '대시보드',
    'dashboard.overview': '개요',
    'dashboard.usage': '사용량',
    'dashboard.documents': '문서',
    'dashboard.sessions': '세션',
    'dashboard.settings': '설정',

    // Settings
    'settings.language': '언어',
    'settings.theme': '테마',
    'settings.notifications': '알림',
    'settings.privacy': '개인정보',
    'settings.account': '계정',

    // Errors
    'error.network': '네트워크 오류. 연결을 확인하세요.',
    'error.server': '서버 오류. 나중에 다시 시도하세요.',
    'error.notFound': '찾을 수 없음',
    'error.unauthorized': '인증되지 않음. 로그인하세요.',
    'error.forbidden': '접근 금지',
  },

  ja: {
    // Common
    'common.loading': '読み込み中...',
    'common.error': 'エラー',
    'common.success': '成功',
    'common.cancel': 'キャンセル',
    'common.save': '保存',
    'common.delete': '削除',
    'common.edit': '編集',
    'common.close': '閉じる',
    'common.back': '戻る',
    'common.next': '次へ',
    'common.submit': '送信',
    'common.search': '検索',
    'common.filter': 'フィルター',
    'common.sort': '並び替え',
    'common.refresh': '更新',

    // Auth
    'auth.login': 'ログイン',
    'auth.logout': 'ログアウト',
    'auth.register': '登録',
    'auth.email': 'メール',
    'auth.password': 'パスワード',
    'auth.username': 'ユーザー名',
    'auth.confirmPassword': 'パスワード確認',
    'auth.forgotPassword': 'パスワードをお忘れですか？',
    'auth.rememberMe': 'ログイン状態を保持',
    'auth.loginSuccess': 'ログイン成功',
    'auth.loginError': 'ログイン失敗',
    'auth.registerSuccess': '登録成功',
    'auth.registerError': '登録失敗',

    // Chat
    'chat.placeholder': 'メッセージを入力...',
    'chat.send': '送信',
    'chat.newChat': '新しいチャット',
    'chat.history': 'チャット履歴',
    'chat.noMessages': 'メッセージがありません',
    'chat.thinking': '考え中...',
    'chat.typing': '入力中...',

    // Documents
    'documents.upload': 'ドキュメントアップロード',
    'documents.uploadSuccess': 'アップロード成功',
    'documents.uploadError': 'アップロード失敗',
    'documents.delete': 'ドキュメント削除',
    'documents.deleteConfirm': 'このドキュメントを削除しますか？',
    'documents.noDocuments': 'ドキュメントがありません',
    'documents.processing': '処理中...',

    // Dashboard
    'dashboard.title': 'ダッシュボード',
    'dashboard.overview': '概要',
    'dashboard.usage': '使用状況',
    'dashboard.documents': 'ドキュメント',
    'dashboard.sessions': 'セッション',
    'dashboard.settings': '設定',

    // Settings
    'settings.language': '言語',
    'settings.theme': 'テーマ',
    'settings.notifications': '通知',
    'settings.privacy': 'プライバシー',
    'settings.account': 'アカウント',

    // Errors
    'error.network': 'ネットワークエラー。接続を確認してください。',
    'error.server': 'サーバーエラー。後でもう一度お試しください。',
    'error.notFound': '見つかりません',
    'error.unauthorized': '未認証。ログインしてください。',
    'error.forbidden': 'アクセス禁止',
  },

  zh: {
    // Common
    'common.loading': '加载中...',
    'common.error': '错误',
    'common.success': '成功',
    'common.cancel': '取消',
    'common.save': '保存',
    'common.delete': '删除',
    'common.edit': '编辑',
    'common.close': '关闭',
    'common.back': '返回',
    'common.next': '下一步',
    'common.submit': '提交',
    'common.search': '搜索',
    'common.filter': '筛选',
    'common.sort': '排序',
    'common.refresh': '刷新',

    // Auth
    'auth.login': '登录',
    'auth.logout': '登出',
    'auth.register': '注册',
    'auth.email': '邮箱',
    'auth.password': '密码',
    'auth.username': '用户名',
    'auth.confirmPassword': '确认密码',
    'auth.forgotPassword': '忘记密码？',
    'auth.rememberMe': '记住我',
    'auth.loginSuccess': '登录成功',
    'auth.loginError': '登录失败',
    'auth.registerSuccess': '注册成功',
    'auth.registerError': '注册失败',

    // Chat
    'chat.placeholder': '输入消息...',
    'chat.send': '发送',
    'chat.newChat': '新对话',
    'chat.history': '对话历史',
    'chat.noMessages': '暂无消息',
    'chat.thinking': '思考中...',
    'chat.typing': '输入中...',

    // Documents
    'documents.upload': '上传文档',
    'documents.uploadSuccess': '上传成功',
    'documents.uploadError': '上传失败',
    'documents.delete': '删除文档',
    'documents.deleteConfirm': '确定要删除此文档吗？',
    'documents.noDocuments': '暂无文档',
    'documents.processing': '处理中...',

    // Dashboard
    'dashboard.title': '仪表板',
    'dashboard.overview': '概览',
    'dashboard.usage': '使用情况',
    'dashboard.documents': '文档',
    'dashboard.sessions': '会话',
    'dashboard.settings': '设置',

    // Settings
    'settings.language': '语言',
    'settings.theme': '主题',
    'settings.notifications': '通知',
    'settings.privacy': '隐私',
    'settings.account': '账户',

    // Errors
    'error.network': '网络错误。请检查连接。',
    'error.server': '服务器错误。请稍后重试。',
    'error.notFound': '未找到',
    'error.unauthorized': '未授权。请登录。',
    'error.forbidden': '禁止访问',
  },
};

export function getTranslation(locale: Locale, key: TranslationKey): string {
  return translations[locale][key] || translations.en[key] || key;
}
