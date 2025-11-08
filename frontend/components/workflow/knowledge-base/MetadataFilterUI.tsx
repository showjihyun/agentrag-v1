"use client";

import React, { useState } from "react";
import { X, Plus } from "lucide-react";

interface MetadataFilter {
  field: string;
  operator: string;
  value: string;
}

interface MetadataFilterUIProps {
  value?: string; // JSON string
  onChange: (value: string) => void;
  disabled?: boolean;
}

const FILTER_FIELDS = [
  { label: "Author", value: "author", type: "string" },
  { label: "Language", value: "language", type: "string" },
  { label: "File Type", value: "file_type", type: "string" },
  { label: "Keywords", value: "keywords", type: "string" },
  { label: "Creation Date", value: "creation_date", type: "number" },
  { label: "Upload Date", value: "upload_date", type: "number" },
];

const STRING_OPERATORS = [
  { label: "Equals", value: "==" },
  { label: "Contains", value: "contains" },
];

const NUMBER_OPERATORS = [
  { label: "Equals", value: "==" },
  { label: "Greater than", value: ">" },
  { label: "Less than", value: "<" },
  { label: "Greater or equal", value: ">=" },
  { label: "Less or equal", value: "<=" },
];

export function MetadataFilterUI({
  value,
  onChange,
  disabled = false,
}: MetadataFilterUIProps) {
  const [filters, setFilters] = useState<MetadataFilter[]>(() => {
    if (!value) return [];
    try {
      const parsed = JSON.parse(value);
      // Convert object to array of filters
      return Object.entries(parsed).map(([field, val]) => ({
        field,
        operator: "==",
        value: String(val),
      }));
    } catch {
      return [];
    }
  });

  const updateFilters = (newFilters: MetadataFilter[]) => {
    setFilters(newFilters);

    // Convert to object format
    const filterObj: Record<string, any> = {};
    newFilters.forEach((filter) => {
      if (filter.field && filter.value) {
        // Try to parse as number if it's a numeric field
        const fieldInfo = FILTER_FIELDS.find((f) => f.value === filter.field);
        if (fieldInfo?.type === "number") {
          const numValue = Number(filter.value);
          if (!isNaN(numValue)) {
            filterObj[filter.field] = numValue;
          }
        } else {
          filterObj[filter.field] = filter.value;
        }
      }
    });

    onChange(JSON.stringify(filterObj, null, 2));
  };

  const addFilter = () => {
    updateFilters([
      ...filters,
      { field: "", operator: "==", value: "" },
    ]);
  };

  const removeFilter = (index: number) => {
    updateFilters(filters.filter((_, i) => i !== index));
  };

  const updateFilter = (
    index: number,
    field: keyof MetadataFilter,
    value: string
  ) => {
    const newFilters = [...filters];
    newFilters[index] = { ...newFilters[index], [field]: value };
    updateFilters(newFilters);
  };

  const getOperators = (field: string) => {
    const fieldInfo = FILTER_FIELDS.find((f) => f.value === field);
    return fieldInfo?.type === "number" ? NUMBER_OPERATORS : STRING_OPERATORS;
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-gray-700">
          Metadata Filters
        </label>
        <button
          onClick={addFilter}
          disabled={disabled}
          className="flex items-center gap-1 px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Plus className="w-3 h-3" />
          Add Filter
        </button>
      </div>

      {filters.length === 0 ? (
        <div className="text-sm text-gray-500 italic">
          No filters applied. Click "Add Filter" to add metadata filters.
        </div>
      ) : (
        <div className="space-y-2">
          {filters.map((filter, index) => (
            <div
              key={index}
              className="flex items-center gap-2 p-2 bg-gray-50 rounded border border-gray-200"
            >
              {/* Field selector */}
              <select
                value={filter.field}
                onChange={(e) => updateFilter(index, "field", e.target.value)}
                disabled={disabled}
                className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
              >
                <option value="">Select field...</option>
                {FILTER_FIELDS.map((field) => (
                  <option key={field.value} value={field.value}>
                    {field.label}
                  </option>
                ))}
              </select>

              {/* Operator selector */}
              <select
                value={filter.operator}
                onChange={(e) =>
                  updateFilter(index, "operator", e.target.value)
                }
                disabled={disabled || !filter.field}
                className="w-32 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
              >
                {getOperators(filter.field).map((op) => (
                  <option key={op.value} value={op.value}>
                    {op.label}
                  </option>
                ))}
              </select>

              {/* Value input */}
              <input
                type="text"
                value={filter.value}
                onChange={(e) => updateFilter(index, "value", e.target.value)}
                disabled={disabled || !filter.field}
                placeholder="Value..."
                className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
              />

              {/* Remove button */}
              <button
                onClick={() => removeFilter(index)}
                disabled={disabled}
                className="p-1 text-red-600 hover:bg-red-50 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                title="Remove filter"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* JSON preview */}
      {filters.length > 0 && (
        <div className="mt-2">
          <div className="text-xs text-gray-500 mb-1">JSON Preview:</div>
          <pre className="text-xs bg-gray-100 p-2 rounded border border-gray-200 overflow-x-auto">
            {value || "{}"}
          </pre>
        </div>
      )}
    </div>
  );
}
