import { Metadata } from 'next';
import { AgenticRAGQuery } from '@/components/agentic-rag/agentic-rag-query';

export const metadata: Metadata = {
  title: 'Agentic RAG | AgenticBuilder',
  description: 'Intelligent retrieval with query decomposition, multi-source search, and reflection',
};

export default function AgenticRAGPage() {
  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Agentic RAG</h1>
        <p className="text-lg text-muted-foreground">
          Advanced retrieval-augmented generation with intelligent query processing
        </p>
      </div>

      <AgenticRAGQuery />
    </div>
  );
}
