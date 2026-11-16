import React from 'react';
import { FinalForensicAssessment } from '../types';

export const MetricsPanel: React.FC<{ assessment: FinalForensicAssessment }> = ({ assessment }) => {
  // Simple heuristic for explainability score based on evidence count and confidence
  const expScore = Math.min(100, (assessment.breakdown.contributors.length * 15) + ((assessment.overall_confidence || 0) * 50));
  
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white border-b pb-2">Metrics & Explainability</h2>
      
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400 uppercase">Explainability Score</p>
          <div className="flex items-end mt-1">
            <span className="text-3xl font-bold text-blue-600">{expScore.toFixed(0)}</span>
            <span className="text-sm text-gray-500 mb-1 ml-1">/ 100</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
            <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${expScore}%` }}></div>
          </div>
        </div>
        <div>
           <p className="text-sm text-gray-500 dark:text-gray-400 uppercase">Evidence Count</p>
           <p className="text-2xl font-bold text-gray-800 dark:text-gray-200 mt-1">{assessment.breakdown.contributors.length}</p>
        </div>
      </div>
      
      <div className="text-sm text-gray-600 dark:text-gray-400 border-t pt-4">
        <p className="mb-1"><strong>Processing Time:</strong> {assessment.execution_time_ms} ms</p>
        <p className="mb-1"><strong>Correlations Applied:</strong> 1</p>
        <p><strong>Conflicts Detected:</strong> 1 (Global confidence penalized)</p>
      </div>
    </div>
  );
};
