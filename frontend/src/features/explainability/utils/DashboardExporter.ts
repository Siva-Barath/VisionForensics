import { FinalForensicAssessment } from '../types';

export const DashboardExporter = {
  exportToJSON: (assessment: FinalForensicAssessment) => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(assessment, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", `forensic_assessment_${assessment.document_name}.json`);
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  },

  exportToCSV: (assessment: FinalForensicAssessment) => {
    let csvContent = "data:text/csv;charset=utf-8,";
    csvContent += "Category,Base Weight,Effective Weight,Risk Shift\n";
    
    assessment.breakdown.contributors.forEach(c => {
      csvContent += `${c.category},${c.base_weight},${c.effective_weight},${c.risk_shift}\n`;
    });
    
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", encodeURI(csvContent));
    downloadAnchorNode.setAttribute("download", `evidence_summary_${assessment.document_name}.csv`);
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  },
  
  exportScreenshot: () => {
    // Stub for HTML2Canvas or similar library
    alert("Dashboard screenshot export triggered. (Requires html2canvas)");
  }
};
