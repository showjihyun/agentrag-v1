/**
 * Document Store using Zustand
 * 
 * Manages document state, uploads, and selections
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import { SearchResult } from '@/lib/types';

// Types
interface Document {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadedAt: Date;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  progress?: number;
  error?: string;
}

interface DocumentState {
  documents: Document[];
  selectedDocumentId: string | null;
  selectedChunkId: string | null;
  sources: SearchResult[];
  uploadQueue: File[];
  isUploading: boolean;
  isLoading: boolean;
  error: string | null;
}

interface DocumentActions {
  // Document actions
  addDocument: (document: Document) => void;
  updateDocument: (id: string, updates: Partial<Document>) => void;
  removeDocument: (id: string) => void;
  setDocuments: (documents: Document[]) => void;
  
  // Selection actions
  selectDocument: (id: string | null) => void;
  selectChunk: (id: string | null) => void;
  
  // Sources actions
  setSources: (sources: SearchResult[]) => void;
  addSource: (source: SearchResult) => void;
  clearSources: () => void;
  
  // Upload actions
  addToUploadQueue: (files: File[]) => void;
  removeFromUploadQueue: (index: number) => void;
  clearUploadQueue: () => void;
  setUploading: (isUploading: boolean) => void;
  
  // Loading and error
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Computed
  getDocumentById: (id: string) => Document | undefined;
  getUploadingDocuments: () => Document[];
  getCompletedDocuments: () => Document[];
  getFailedDocuments: () => Document[];
  
  // Utility
  reset: () => void;
}

type DocumentStore = DocumentState & DocumentActions;

// Initial state
const initialState: DocumentState = {
  documents: [],
  selectedDocumentId: null,
  selectedChunkId: null,
  sources: [],
  uploadQueue: [],
  isUploading: false,
  isLoading: false,
  error: null,
};

// Create store
export const useDocumentStore = create<DocumentStore>()(
  devtools(
    immer((set, get) => ({
      ...initialState,
      
      // Document actions
      addDocument: (document) => {
        set((state) => {
          state.documents.push(document);
        });
      },
      
      updateDocument: (id, updates) => {
        set((state) => {
          const index = state.documents.findIndex((doc) => doc.id === id);
          if (index !== -1) {
            // Create a properly typed updated document for exactOptionalPropertyTypes compatibility
            const currentDocument = state.documents[index];
            const updatedDocument = {
              ...currentDocument,
              ...(updates.id !== undefined && { id: updates.id }),
              ...(updates.name !== undefined && { name: updates.name }),
              ...(updates.size !== undefined && { size: updates.size }),
              ...(updates.type !== undefined && { type: updates.type }),
              ...(updates.uploadedAt !== undefined && { uploadedAt: updates.uploadedAt }),
              ...(updates.status !== undefined && { status: updates.status }),
              ...(updates.progress !== undefined && { progress: updates.progress }),
              ...(updates.error !== undefined && { error: updates.error }),
            };
            state.documents[index] = updatedDocument;
          }
        });
      },
      
      removeDocument: (id) => {
        set((state) => {
          state.documents = state.documents.filter((doc) => doc.id !== id);
          if (state.selectedDocumentId === id) {
            state.selectedDocumentId = null;
          }
        });
      },
      
      setDocuments: (documents) => {
        set((state) => {
          state.documents = documents;
        });
      },
      
      // Selection actions
      selectDocument: (id) => {
        set((state) => {
          state.selectedDocumentId = id;
        });
      },
      
      selectChunk: (id) => {
        set((state) => {
          state.selectedChunkId = id;
        });
      },
      
      // Sources actions
      setSources: (sources) => {
        set((state) => {
          state.sources = sources;
        });
      },
      
      addSource: (source) => {
        set((state) => {
          // Avoid duplicates
          if (!state.sources.find((s) => s.chunk_id === source.chunk_id)) {
            state.sources.push(source);
          }
        });
      },
      
      clearSources: () => {
        set((state) => {
          state.sources = [];
        });
      },
      
      // Upload actions
      addToUploadQueue: (files) => {
        set((state) => {
          state.uploadQueue.push(...files);
        });
      },
      
      removeFromUploadQueue: (index) => {
        set((state) => {
          state.uploadQueue.splice(index, 1);
        });
      },
      
      clearUploadQueue: () => {
        set((state) => {
          state.uploadQueue = [];
        });
      },
      
      setUploading: (isUploading) => {
        set((state) => {
          state.isUploading = isUploading;
        });
      },
      
      // Loading and error
      setLoading: (isLoading) => {
        set((state) => {
          state.isLoading = isLoading;
        });
      },
      
      setError: (error) => {
        set((state) => {
          state.error = error;
        });
      },
      
      // Computed
      getDocumentById: (id) => {
        return get().documents.find((doc) => doc.id === id);
      },
      
      getUploadingDocuments: () => {
        return get().documents.filter((doc) => doc.status === 'uploading' || doc.status === 'processing');
      },
      
      getCompletedDocuments: () => {
        return get().documents.filter((doc) => doc.status === 'completed');
      },
      
      getFailedDocuments: () => {
        return get().documents.filter((doc) => doc.status === 'failed');
      },
      
      // Utility
      reset: () => {
        set(initialState);
      },
    })),
    { name: 'DocumentStore' }
  )
);

// Selectors
export const useDocuments = () => useDocumentStore((state) => state.documents);
export const useSelectedDocumentId = () => useDocumentStore((state) => state.selectedDocumentId);
export const useSelectedChunkId = () => useDocumentStore((state) => state.selectedChunkId);
export const useSources = () => useDocumentStore((state) => state.sources);
export const useUploadQueue = () => useDocumentStore((state) => state.uploadQueue);
export const useIsUploading = () => useDocumentStore((state) => state.isUploading);

// Computed selectors
export const useDocumentCount = () => useDocumentStore((state) => state.documents.length);
export const useSourceCount = () => useDocumentStore((state) => state.sources.length);
export const useHasSources = () => useDocumentStore((state) => state.sources.length > 0);
export const useUploadingCount = () => useDocumentStore((state) => 
  state.documents.filter((doc) => doc.status === 'uploading' || doc.status === 'processing').length
);

// Action selectors
export const useDocumentActions = () => useDocumentStore((state) => ({
  addDocument: state.addDocument,
  updateDocument: state.updateDocument,
  removeDocument: state.removeDocument,
  selectDocument: state.selectDocument,
  selectChunk: state.selectChunk,
  setSources: state.setSources,
  addSource: state.addSource,
  clearSources: state.clearSources,
  addToUploadQueue: state.addToUploadQueue,
  setUploading: state.setUploading,
}));
