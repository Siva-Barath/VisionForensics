import React from 'react';

export const DependencyGraphVis: React.FC = () => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white border-b pb-2">Detector Dependency Graph</h2>
      
      <div className="font-mono text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-900 p-4 rounded overflow-auto border border-gray-200 dark:border-gray-700 whitespace-pre">
        {`Image Quality
 ├── OCR (Reliability Penalty: -40%)
 ├── Signature
 └── Logo

Copy Move
 └── Signature (Synergistic Boost: +20%)

Layout
 ├── Classification
 └── OCR`}
      </div>
      <p className="text-xs text-gray-500 mt-2 italic">
        Visualizing how penalties and bonuses propagated through the Bayesian engine.
      </p>
    </div>
  );
};
