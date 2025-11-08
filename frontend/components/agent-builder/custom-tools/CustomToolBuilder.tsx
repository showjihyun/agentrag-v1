"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Trash2, TestTube, Save } from "lucide-react";

interface Parameter {
  name: string;
  type: string;
  required: boolean;
  description: string;
}

interface CustomToolBuilderProps {
  onSave: (tool: any) => void;
  onCancel: () => void;
  initialData?: any;
}

export function CustomToolBuilder({
  onSave,
  onCancel,
  initialData,
}: CustomToolBuilderProps) {
  const [name, setName] = useState(initialData?.name || "");
  const [description, setDescription] = useState(initialData?.description || "");
  const [category, setCategory] = useState(initialData?.category || "custom");
  const [icon, setIcon] = useState(initialData?.icon || "🔧");
  const [method, setMethod] = useState(initialData?.method || "GET");
  const [url, setUrl] = useState(initialData?.url || "");
  const [parameters, setParameters] = useState<Parameter[]>(
    initialData?.parameters || []
  );
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  const addParameter = () => {
    setParameters([
      ...parameters,
      { name: "", type: "string", required: true, description: "" },
    ]);
  };

  const removeParameter = (index: number) => {
    setParameters(parameters.filter((_, i) => i !== index));
  };

  const updateParameter = (index: number, field: string, value: any) => {
    const updated = [...parameters];
    updated[index] = { ...updated[index], [field]: value };
    setParameters(updated);
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      // Build test data from parameters
      const testData: any = {};
      parameters.forEach((param) => {
        if (param.type === "string") testData[param.name] = "test";
        else if (param.type === "number") testData[param.name] = 123;
        else if (param.type === "boolean") testData[param.name] = true;
      });

      const response = await fetch("/api/agent-builder/custom-tools/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          method,
          url,
          parameters: testData,
        }),
      });

      const result = await response.json();
      setTestResult(result);
    } catch (error) {
      setTestResult({ success: false, error: String(error) });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = () => {
    onSave({
      name,
      description,
      category,
      icon,
      method,
      url,
      parameters,
    });
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="name">Tool Name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Custom Tool"
            />
          </div>

          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What does this tool do?"
              rows={3}
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label htmlFor="category">Category</Label>
              <Select value={category} onValueChange={setCategory}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="custom">Custom</SelectItem>
                  <SelectItem value="api">API</SelectItem>
                  <SelectItem value="data">Data</SelectItem>
                  <SelectItem value="communication">Communication</SelectItem>
                  <SelectItem value="productivity">Productivity</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="icon">Icon</Label>
              <Input
                id="icon"
                value={icon}
                onChange={(e) => setIcon(e.target.value)}
                placeholder="🔧"
                maxLength={2}
              />
            </div>

            <div>
              <Label htmlFor="method">HTTP Method</Label>
              <Select value={method} onValueChange={setMethod}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="GET">GET</SelectItem>
                  <SelectItem value="POST">POST</SelectItem>
                  <SelectItem value="PUT">PUT</SelectItem>
                  <SelectItem value="DELETE">DELETE</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label htmlFor="url">API Endpoint URL</Label>
            <Input
              id="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://api.example.com/endpoint"
            />
            <p className="text-xs text-muted-foreground mt-1">
              Use {"{{"} and {"}}"} for parameters, e.g., https://api.example.com/users/{"{"}
              {"{"}userId{"}}"}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Parameters</CardTitle>
            <Button onClick={addParameter} size="sm" variant="outline">
              <Plus className="h-4 w-4 mr-2" />
              Add Parameter
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {parameters.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              No parameters defined. Click "Add Parameter" to get started.
            </p>
          ) : (
            parameters.map((param, index) => (
              <div
                key={index}
                className="flex items-start gap-4 p-4 border rounded-lg"
              >
                <div className="flex-1 grid grid-cols-2 gap-4">
                  <div>
                    <Label>Name</Label>
                    <Input
                      value={param.name}
                      onChange={(e) =>
                        updateParameter(index, "name", e.target.value)
                      }
                      placeholder="paramName"
                    />
                  </div>

                  <div>
                    <Label>Type</Label>
                    <Select
                      value={param.type}
                      onValueChange={(value) =>
                        updateParameter(index, "type", value)
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="string">String</SelectItem>
                        <SelectItem value="number">Number</SelectItem>
                        <SelectItem value="boolean">Boolean</SelectItem>
                        <SelectItem value="array">Array</SelectItem>
                        <SelectItem value="object">Object</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="col-span-2">
                    <Label>Description</Label>
                    <Input
                      value={param.description}
                      onChange={(e) =>
                        updateParameter(index, "description", e.target.value)
                      }
                      placeholder="Parameter description"
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={param.required}
                      onChange={(e) =>
                        updateParameter(index, "required", e.target.checked)
                      }
                      className="h-4 w-4"
                    />
                    <Label>Required</Label>
                  </div>
                </div>

                <Button
                  onClick={() => removeParameter(index)}
                  size="sm"
                  variant="ghost"
                  className="text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {testResult && (
        <Card>
          <CardHeader>
            <CardTitle>Test Result</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-muted p-4 rounded-lg overflow-auto text-sm">
              {JSON.stringify(testResult, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}

      <div className="flex justify-between">
        <Button onClick={onCancel} variant="outline">
          Cancel
        </Button>

        <div className="flex gap-2">
          <Button
            onClick={handleTest}
            variant="outline"
            disabled={!url || testing}
          >
            <TestTube className="h-4 w-4 mr-2" />
            {testing ? "Testing..." : "Test Tool"}
          </Button>

          <Button onClick={handleSave} disabled={!name || !url}>
            <Save className="h-4 w-4 mr-2" />
            Save Tool
          </Button>
        </div>
      </div>
    </div>
  );
}
