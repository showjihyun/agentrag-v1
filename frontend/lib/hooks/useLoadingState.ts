import { useState, useCallback } from 'react';

type LoadingStage = 'analyzing' | 'searching' | 'generating' | 'finalizing';

export function useLoadingState() {
  const [loadingStage, setLoadingStage] = useState<LoadingStage>('analyzing');
  const [showSuccess, setShowSuccess] = useState(false);
  const [lastProcessingTime, setLastProcessingTime] = useState<number>();

  const handleSuccess = useCallback((processingTime: number) => {
    setLastProcessingTime(processingTime);
    setShowSuccess(true);
    
    setTimeout(() => setShowSuccess(false), 3000);
  }, []);

  const hideSuccess = useCallback(() => {
    setShowSuccess(false);
  }, []);

  return {
    loadingStage,
    setLoadingStage,
    showSuccess,
    lastProcessingTime,
    handleSuccess,
    hideSuccess,
  };
}
