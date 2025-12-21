'use client';

import React from 'react';

interface EmotionalAIBlockProps {
  onConfigChange?: (config: any) => void;
  initialConfig?: any;
}

const EmotionalAIBlock: React.FC<EmotionalAIBlockProps> = ({
  onConfigChange,
  initialConfig
}) => {
  return (
    <div className="w-full p-6 border rounded-lg">
      <h2 className="text-2xl font-bold mb-4">Emotional AI Block</h2>
      <p className="text-muted-foreground">
        Emotional AI functionality is being updated. Please check back later.
      </p>
    </div>
  );
};

export default EmotionalAIBlock;