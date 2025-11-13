'use client';

import React, { useState } from 'react';
import { Label } from '@/components/ui/label';

interface CodeNodeConfigProps {
  data: {
    language?: 'python' | 'javascript';
    code?: string;
  };
  onChange: (data: any) => void;
}

export default function CodeNodeConfig({ data, onChange }: CodeNodeConfigProps) {
  const [language, setLanguage] = useState<'python' | 'javascript'>(
    data.language || 'javascript'
  );
  const [code, setCode] = useState(data.code || '');

  const handleLanguageChange = (newLang: 'python' | 'javascript') => {
    setLanguage(newLang);
    onChange({ ...data, language: newLang });
  };

  const handleCodeChange = (value: string) => {
    setCode(value);
    onChange({ ...data, code: value });
  };

  const pythonTemplate = `# Input data is available in 'input_data' variable
# Return your result as a dictionary

def main(input_data):
    # Your code here
    result = {
        "output": input_data.get("value", 0) * 2
    }
    return result

# The function will be called automatically
output = main(input_data)`;

  const javascriptTemplate = `// Input data is available in 'inputData' variable
// Return your result as an object

function main(inputData) {
  // Your code here
  const result = {
    output: (inputData.value || 0) * 2
  };
  return result;
}

// The function will be called automatically
const output = main(inputData);`;

  const loadTemplate = () => {
    const template = language === 'python' ? pythonTemplate : javascriptTemplate;
    setCode(template);
    onChange({ ...data, code: template });
  };

  return (
    <div className="space-y-4">
      <div>
        <Label>Language</Label>
        <div className="flex gap-2 mt-2">
          <button
            onClick={() => handleLanguageChange('javascript')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              language === 'javascript'
                ? 'bg-yellow-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            JavaScript
          </button>
          <button
            onClick={() => handleLanguageChange('python')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              language === 'python'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Python
          </button>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <Label>Code</Label>
          <button
            onClick={loadTemplate}
            className="text-xs text-blue-600 hover:text-blue-700"
          >
            Load Template
          </button>
        </div>
        <textarea
          value={code}
          onChange={(e) => handleCodeChange(e.target.value)}
          className="w-full h-64 p-3 border rounded-lg font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder={`Write your ${language} code here...`}
        />
      </div>

      <div className="bg-green-50 border border-green-200 rounded-lg p-3 space-y-2">
        <p className="text-xs text-green-800 font-medium">
          Available Variables:
        </p>
        <ul className="text-xs text-green-700 space-y-1 ml-4 list-disc">
          <li>
            <code className="bg-green-100 px-1 rounded">
              {language === 'python' ? 'input_data' : 'inputData'}
            </code>
            : Data from previous node
          </li>
          <li>
            <code className="bg-green-100 px-1 rounded">
              {language === 'python' ? 'workflow_vars' : 'workflowVars'}
            </code>
            : Workflow-level variables
          </li>
        </ul>
        <p className="text-xs text-green-800 mt-2">
          <strong>Return:</strong> Your code must return/assign an object to{' '}
          <code className="bg-green-100 px-1 rounded">output</code>
        </p>
      </div>

      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
        <p className="text-xs text-yellow-800">
          <strong>Security Note:</strong> Code execution runs in a sandboxed
          environment with limited access to system resources and network.
        </p>
      </div>
    </div>
  );
}
