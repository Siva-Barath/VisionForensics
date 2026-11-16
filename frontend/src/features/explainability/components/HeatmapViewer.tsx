import React from 'react';

export const HeatmapViewer: React.FC = () => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white border-b pb-2">Heatmap Viewer</h2>
      <div className="flex items-center space-x-4 mb-4">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Select Overlay:</label>
        <select className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:text-white">
          <option>None</option>
          <option>ELA Heatmap</option>
          <option>Blur Map</option>
          <option>Noise Map</option>
          <option>Copy-Move Map</option>
        </select>
      </div>
      <div className="h-64 bg-gray-100 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded flex items-center justify-center text-gray-500 italic relative overflow-hidden">
        {/* Mock visual for the heatmap */}
        <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-red-500/20 to-transparent pointer-events-none"></div>
        Select a heatmap to visualize structural inconsistencies over the document.
      </div>
    </div>
  );
};
