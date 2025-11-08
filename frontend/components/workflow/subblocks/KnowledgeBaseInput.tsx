"use client";

import React, { useState } from "react";
import { Database, Search, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  KnowledgeBaseSelector,
  DocumentBrowser,
  MetadataFilterUI,
  SearchPreview,
} from "../knowledge-base";

export interface KnowledgeBaseInputProps {
  id: string;
  title: string;
  value?: {
    collection?: string;
    query?: string;
    topK?: number;
    filters?: string;
  };
  defaultValue?: any;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  error?: string;
  onChange: (value: any) => void;
}

export function KnowledgeBaseInput({
  id,
  title,
  value = {},
  defaultValue,
  placeholder,
  required = false,
  disabled = false,
  error,
  onChange,
}: KnowledgeBaseInputProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [localValue, setLocalValue] = useState(value || defaultValue || {});

  const handleChange = (field: string, fieldValue: any) => {
    const newValue = { ...localValue, [field]: fieldValue };
    setLocalValue(newValue);
    onChange(newValue);
  };

  const hasConfiguration = localValue.collection || localValue.query;

  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-gray-700 flex items-center gap-1">
        {title}
        {required && <span className="text-red-500">*</span>}
      </label>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogTrigger>
          <Button
            variant="outline"
            className="w-full justify-start gap-2"
            disabled={disabled}
            type="button"
          >
            <Database className="w-4 h-4" />
            {hasConfiguration ? (
              <span className="flex-1 text-left truncate">
                {localValue.collection || "Knowledge Base"} 
                {localValue.query && ` - "${localValue.query.substring(0, 30)}..."`}
              </span>
            ) : (
              <span className="flex-1 text-left text-gray-500">
                {placeholder || "Configure Knowledge Base"}
              </span>
            )}
          </Button>
        </DialogTrigger>

        <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>Configure Knowledge Base</DialogTitle>
            <DialogDescription>
              Set up your knowledge base search configuration
            </DialogDescription>
          </DialogHeader>

          <Tabs defaultValue="collection" className="flex-1 overflow-hidden flex flex-col">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="collection">
                <Database className="w-4 h-4 mr-2" />
                Collection
              </TabsTrigger>
              <TabsTrigger value="query">
                <Search className="w-4 h-4 mr-2" />
                Query
              </TabsTrigger>
              <TabsTrigger value="filters">
                <Filter className="w-4 h-4 mr-2" />
                Filters
              </TabsTrigger>
              <TabsTrigger value="preview">
                <Search className="w-4 h-4 mr-2" />
                Preview
              </TabsTrigger>
            </TabsList>

            <div className="flex-1 overflow-y-auto mt-4">
              <TabsContent value="collection" className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium mb-2">Select Collection</h3>
                  <KnowledgeBaseSelector
                    value={localValue.collection}
                    onChange={(val) => handleChange("collection", val)}
                    disabled={disabled}
                  />
                </div>

                <div>
                  <h3 className="text-sm font-medium mb-2">Browse Documents</h3>
                  <DocumentBrowser />
                </div>
              </TabsContent>

              <TabsContent value="query" className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-700 block mb-2">
                    Search Query
                  </label>
                  <textarea
                    value={localValue.query || ""}
                    onChange={(e) => handleChange("query", e.target.value)}
                    placeholder="Enter your search query or use {{variable}} for dynamic values"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={4}
                    disabled={disabled}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Use variables like {`{{input.query}}`} to make the query dynamic
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-700 block mb-2">
                    Number of Results (Top K)
                  </label>
                  <input
                    type="number"
                    value={localValue.topK || 5}
                    onChange={(e) => handleChange("topK", parseInt(e.target.value))}
                    min={1}
                    max={100}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={disabled}
                  />
                </div>
              </TabsContent>

              <TabsContent value="filters" className="space-y-4">
                <MetadataFilterUI
                  value={localValue.filters}
                  onChange={(val) => handleChange("filters", val)}
                  disabled={disabled}
                />
              </TabsContent>

              <TabsContent value="preview" className="space-y-4">
                {localValue.query ? (
                  <SearchPreview
                    query={localValue.query}
                    topK={localValue.topK}
                    filters={localValue.filters}
                  />
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <Search className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>Enter a query in the Query tab to preview results</p>
                  </div>
                )}
              </TabsContent>
            </div>
          </Tabs>

          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={() => setIsOpen(false)}>
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {hasConfiguration && (
        <div className="text-xs text-gray-500 space-y-1">
          {localValue.collection && (
            <div>Collection: <span className="font-medium">{localValue.collection}</span></div>
          )}
          {localValue.topK && (
            <div>Top K: <span className="font-medium">{localValue.topK}</span></div>
          )}
        </div>
      )}
    </div>
  );
}
