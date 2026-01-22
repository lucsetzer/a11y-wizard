# compliance_tracker.py
import json
import csv
from typing import Dict, List
import os
from datetime import datetime, timedelta  # <-- Add timedelta here

class UniversityComplianceTracker:
    """Track accessibility compliance for university audits"""
    
    def __init__(self, output_dir="compliance_reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_report(self, url: str, results: Dict, department: str = "") -> str:
        """Generate a compliance report suitable for university audits"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/compliance_{timestamp}.json"
        
        report = {
            "institution": "University Accessibility Audit",
            "timestamp": timestamp,
            "url": url,
            "department": department,
            "score": results.get("score", 0),
            "compliance_status": self._get_compliance_status(results.get("score", 0)),
            "wcag_level": self._determine_wcag_level(results.get("issues", [])),
            "critical_issues": len([i for i in results.get("issues", []) if i.get("type") == "critical"]),
            "total_issues": len(results.get("issues", [])),
            "detailed_issues": results.get("issues", []),
            "auditor": "A11y Wizard",
            "next_audit_date": self._get_next_audit_date(),
            "legal_references": [
                "ADA Title II",
                "Section 508",
                "WCAG 2.1 AA",
                "OCR Resolution Agreements"
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Also generate CSV for spreadsheets
        self._generate_csv_report(report, timestamp)
        
        return filename
    
    def _get_compliance_status(self, score: int) -> str:
        """Determine compliance status for university"""
        if score >= 95:
            return "COMPLIANT - Excellent"
        elif score >= 90:
            return "COMPLIANT - Good"
        elif score >= 80:
            return "PARTIALLY COMPLIANT - Needs Improvement"
        elif score >= 70:
            return "NON-COMPLIANT - Significant Issues"
        else:
            return "NON-COMPLIANT - Critical Remediation Required"
    
    def _determine_wcag_level(self, issues: List) -> str:
        """Determine which WCAG level the site meets"""
        # Check issue tags to determine compliance level
        for issue in issues:
            tags = issue.get("tags", [])
            if "wcag2aa" in tags and issue.get("type") == "critical":
                return "WCAG 2.0 A (Minimum)"
        
        # If no critical AA issues, assume AA
        return "WCAG 2.1 AA (Target)"
    
    def _get_next_audit_date(self) -> str:
        """University audit schedule (quarterly recommended)"""
        from datetime import datetime, timedelta
        next_date = datetime.now() + timedelta(days=90)  # Quarterly
        return next_date.strftime("%Y-%m-%d")
    
    def _generate_csv_report(self, report: Dict, timestamp: str):
        """Generate CSV for spreadsheet import"""
        csv_file = f"{self.output_dir}/compliance_{timestamp}.csv"
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow(["University Accessibility Compliance Report"])
            writer.writerow(["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow([])
            
            # Summary
            writer.writerow(["SUMMARY"])
            writer.writerow(["URL", report["url"]])
            writer.writerow(["Department", report["department"]])
            writer.writerow(["Score", f"{report['score']}/100"])
            writer.writerow(["Compliance Status", report["compliance_status"]])
            writer.writerow(["WCAG Level", report["wcag_level"]])
            writer.writerow(["Critical Issues", report["critical_issues"]])
            writer.writerow(["Total Issues", report["total_issues"]])
            writer.writerow(["Next Audit Due", report["next_audit_date"]])
            writer.writerow([])
            
            # Issues detail
            writer.writerow(["DETAILED ISSUES"])
            writer.writerow(["Type", "Title", "Description", "WCAG Criteria", "Fix Required", "Due Date"])
            
            for issue in report["detailed_issues"]:
                # Determine due date based on severity
                severity = issue.get("type", "warning")
                if severity == "critical":
                    due_date = "IMMEDIATE"
                elif severity == "warning":
                    due_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                else:
                    due_date = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
                
                writer.writerow([
                    issue.get("type", "").upper(),
                    issue.get("title", ""),
                    issue.get("description", "")[:100],
                    issue.get("category", "General"),
                    issue.get("fix", "Review required"),
                    due_date
                ])
