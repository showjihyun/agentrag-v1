'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command';
import { Badge } from '@/components/ui/badge';
import {
  Search,
  Layers,
  Box,
  GitBranch,
  Database,
  Clock,
  Star,
} from 'lucide-react';

interface SearchResult {
  id: string;
  type: 'agent' | 'block' | 'workflow' | 'knowledgebase' | 'execution';
  title: string;
  description?: string;
  metadata?: Record<string, any>;
  url: string;
}

export function GlobalSearch() {
  const router = useRouter();
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState('');
  const [results, setResults] = React.useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = React.useState(false);
  const [recentSearches, setRecentSearches] = React.useState<string[]>([]);

  // Keyboard shortcut
  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };

    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  // Load recent searches
  React.useEffect(() => {
    const saved = localStorage.getItem('recent-searches');
    if (saved) {
      setRecentSearches(JSON.parse(saved));
    }
  }, []);

  // Search function
  const performSearch = React.useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setIsSearching(true);
    try {
      // TODO: Replace with actual API call
      const response = await fetch(
        `/api/agent-builder/search?q=${encodeURIComponent(searchQuery)}`
      );
      const data = await response.json();
      setResults(data.results || []);
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  // Debounced search
  React.useEffect(() => {
    const timer = setTimeout(() => {
      performSearch(query);
    }, 300);

    return () => clearTimeout(timer);
  }, [query, performSearch]);

  const handleSelect = (result: SearchResult) => {
    // Save to recent searches
    const updated = [query, ...recentSearches.filter((s) => s !== query)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('recent-searches', JSON.stringify(updated));

    // Navigate
    router.push(result.url);
    setOpen(false);
    setQuery('');
  };

  const getIcon = (type: SearchResult['type']) => {
    switch (type) {
      case 'agent':
        return <Layers className="h-4 w-4" />;
      case 'block':
        return <Box className="h-4 w-4" />;
      case 'workflow':
        return <GitBranch className="h-4 w-4" />;
      case 'knowledgebase':
        return <Database className="h-4 w-4" />;
      case 'execution':
        return <Clock className="h-4 w-4" />;
    }
  };

  const groupedResults = React.useMemo(() => {
    const groups: Record<string, SearchResult[]> = {
      agent: [],
      block: [],
      workflow: [],
      knowledgebase: [],
      execution: [],
    };

    results.forEach((result) => {
      groups[result.type].push(result);
    });

    return groups;
  }, [results]);

  return (
    <>
      {/* Trigger button */}
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground border rounded-md hover:bg-accent transition-colors"
      >
        <Search className="h-4 w-4" />
        <span>Search...</span>
        <kbd className="pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground opacity-100">
          <span className="text-xs">⌘</span>K
        </kbd>
      </button>

      {/* Command dialog */}
      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput
          placeholder="Search agents, blocks, workflows..."
          value={query}
          onValueChange={setQuery}
        />
        <CommandList>
          {!query && recentSearches.length > 0 && (
            <>
              <CommandGroup heading="Recent Searches">
                {recentSearches.map((search, index) => (
                  <CommandItem
                    key={index}
                    onSelect={() => setQuery(search)}
                  >
                    <Clock className="mr-2 h-4 w-4" />
                    {search}
                  </CommandItem>
                ))}
              </CommandGroup>
              <CommandSeparator />
            </>
          )}

          {isSearching && (
            <CommandEmpty>Searching...</CommandEmpty>
          )}

          {!isSearching && query && results.length === 0 && (
            <CommandEmpty>No results found.</CommandEmpty>
          )}

          {Object.entries(groupedResults).map(([type, items]) => {
            if (items.length === 0) return null;

            return (
              <CommandGroup
                key={type}
                heading={type.charAt(0).toUpperCase() + type.slice(1) + 's'}
              >
                {items.map((result) => (
                  <CommandItem
                    key={result.id}
                    onSelect={() => handleSelect(result)}
                  >
                    {getIcon(result.type)}
                    <div className="ml-2 flex-1">
                      <div className="flex items-center gap-2">
                        <span>{result.title}</span>
                        {result.metadata?.isFavorite && (
                          <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                        )}
                      </div>
                      {result.description && (
                        <div className="text-xs text-muted-foreground truncate">
                          {result.description}
                        </div>
                      )}
                    </div>
                    {result.metadata?.status && (
                      <Badge variant="outline" className="ml-2">
                        {result.metadata.status}
                      </Badge>
                    )}
                  </CommandItem>
                ))}
              </CommandGroup>
            );
          })}
        </CommandList>
      </CommandDialog>
    </>
  );
}
