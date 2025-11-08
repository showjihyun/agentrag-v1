/**
 * Zustand Stores Index
 * 
 * Centralized export for all Zustand stores
 */

// Chat Store
export {
  useChatStore,
  useMessages,
  useIsProcessing,
  useCurrentSessionId,
  useChatError,
  useLastMessageTimestamp,
  useMessageCount,
  useHasMessages,
  useLastMessage,
  useChatActions,
} from './useChatStore';

// UI Store
export {
  useUIStore,
  useTheme,
  useIsSidebarOpen,
  useSidebarWidth,
  useActiveModal,
  useModalData,
  useIsMobileMenuOpen,
  useIsDocViewerOpen,
  useGlobalLoading,
  useLoadingMessage,
  useToasts,
  useUIActions,
} from './useUIStore';

// Document Store
export {
  useDocumentStore,
  useDocuments,
  useSelectedDocumentId,
  useSelectedChunkId,
  useSources,
  useUploadQueue,
  useIsUploading,
  useDocumentCount,
  useSourceCount,
  useHasSources,
  useUploadingCount,
  useDocumentActions,
} from './useDocumentStore';
