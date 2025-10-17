/**
 * Document Store using Zustand
 * 
 * Centralized state management for documents with persistence.
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { Document } from '@/lib/types';

interface DocumentStore {
  // State
  documents: Document[];
  isLoading: boolean;
  error: string | null;
  selectedDocument: Document | null;
  
  // Actions
  setDocuments: (documents: Document[]) => void;
  addDocument: (document: Document) => void;
  removeDocument: (documentId: string) => void;
  updateDocument: (documentId: string, updates: Partial<Document>) => void;
  setSelectedDocument: (document: Document | null) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  reset: () => void;
}

const initialState = {
  documents: [],
  isLoading: false,
  error: null,
  selectedDocument: null,
};

export const useDocumentStore = create<DocumentStore>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      setDocuments: (documents) => {
        set({ documents, error: null });
      },
      
      addDocument: (document) => {
        set((state) => ({
          documents: [...state.documents, document],
          error: null,
        }));
      },
      
      removeDocument: (documentId) => {
        set((state) => ({
          documents: state.documents.filter(
            (doc) => doc.document_id !== documentId
          ),
          selectedDocument:
            state.selectedDocument?.document_id === documentId
              ? null
              : state.selectedDocument,
        }));
      },
      
      updateDocument: (documentId, updates) => {
        set((state) => ({
          documents: state.documents.map((doc) =>
            doc.document_id === documentId ? { ...doc, ...updates } : doc
          ),
          selectedDocument:
            state.selectedDocument?.document_id === documentId
              ? { ...state.selectedDocument, ...updates }
              : state.selectedDocument,
        }));
      },
      
      setSelectedDocument: (document) => {
        set({ selectedDocument: document });
      },
      
      setLoading: (isLoading) => {
        set({ isLoading });
      },
      
      setError: (error) => {
        set({ error, isLoading: false });
      },
      
      clearError: () => {
        set({ error: null });
      },
      
      reset: () => {
        set(initialState);
      },
    }),
    {
      name: 'document-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // Only persist documents, not loading/error states
        documents: state.documents,
      }),
    }
  )
);

// Selectors for better performance
export const useDocuments = () => useDocumentStore((state) => state.documents);
export const useDocumentsLoading = () => useDocumentStore((state) => state.isLoading);
export const useDocumentsError = () => useDocumentStore((state) => state.error);
export const useSelectedDocument = () => useDocumentStore((state) => state.selectedDocument);
