# app.py - UPDATED WITH REAL CHECKER
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
import aiohttp
import asyncio
from typing import Optional
import os
import tempfile
from compliance_tracker import UniversityComplianceTracker
from datetime import datetime
from pdf_analyzer import PDFAccessibilityChecker
from ai_analyzer import AIAccessibilityAnalyzer

ai_analyzer = AIAccessibilityAnalyzer()

compliance_tracker = UniversityComplianceTracker()

# Import our real accessibility checker
try:
    from accessibility_checker import AccessibilityChecker
    CHECKER_AVAILABLE = True
    print("✅ AccessibilityChecker imported successfully")
except ImportError as e:
    CHECKER_AVAILABLE = False
    print(f"⚠️ Could not import AccessibilityChecker: {e}")
    # Create a dummy fallback
    class DummyChecker:
        async def check_url(self, url):
            return {"url": url, "score": 0, "issues": [], "summary": "Checker not available", "error": "Import failed"}

app = FastAPI(title="A11y Wizard", description="Accessibility Grader")

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize checker
if CHECKER_AVAILABLE:
    checker = AccessibilityChecker()
else:
    checker = DummyChecker()
    print("⚠️ Running with dummy checker - install dependencies for real analysis")

# Homepage
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Homepage with instruction cards"""
    return templates.TemplateResponse("index.html", {"request": request})

# Analysis page
@app.get("/analyze", response_class=HTMLResponse)
async def analyze_page(request: Request):
    """Analysis page with forms"""
    return templates.TemplateResponse("analyze.html", {"request": request})

# REAL URL analysis endpoint - NO MORE DUMMY DATA
@app.post("/analyze/url")
async def analyze_url(url: str = Form(...)):
    try:
        checker = AccessibilityChecker()
        results = await checker.check_url(url)
        
        if results.get("score") == 0 and "blocked" in results.get("summary", "").lower():
            # Return user-friendly error
            return JSONResponse({
                "error": "Website blocked the accessibility scanner. Try a different site or use document upload.",
                "score": 0,
                "issues": [],
                "summary": "Blocked by website security"
            })
        
        return JSONResponse(results)
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# Add new endpoint for AI-only analysis
@app.post("/analyze/ai")
async def analyze_with_ai(request: Request, url: str = Form(...)):
    """Get analysis for existing results"""
    try:
        # First get regular analysis
        checker = AccessibilityChecker()
        results = await checker.check_url(url)
        
        # Then get AI analysis
        if ai_analyzer.available:
            ai_results = await ai_analyzer.analyze_accessibility_results(
                url=results["url"],
                score=results["score"],
                issues=results["issues"]
            )
            return JSONResponse({
                "url": url,
                "accessibility_score": results["score"],
                "issue_count": len(results["issues"]),
                "ai_analysis": ai_results
            })
        else:
            return JSONResponse({
                "error": "Not available",
                "setup_required": True
            }, status_code=400)
            
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
@app.post("/analyze/pdf")
async def analyze_pdf(request: Request, pdf_file: UploadFile = File(...)):
    """Analyze a document for accessibility issues"""
    try:
        # Check file type
        allowed_types = ['.pdf', '.doc', '.docx', '.txt']
        file_ext = os.path.splitext(pdf_file.filename)[1].lower()
        
        if file_ext not in allowed_types:
            return JSONResponse({
                "error": f"File type {file_ext} not supported",
                "score": 0,
                "issues": [],
                "summary": f"Unsupported file type: {file_ext}"
            }, status_code=400)
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await pdf_file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Analyze the document
        checker = PDFAccessibilityChecker()
        results = checker.analyze_document(tmp_path, pdf_file.filename)
        
        # DETERMINE DOCUMENT TYPE FOR AI
        if file_ext == '.pdf':
            doc_type = "PDF"
        elif file_ext in ['.doc', '.docx']:
            doc_type = "Word"
        elif file_ext == '.txt':
            doc_type = "Text"
        else:
            doc_type = "Document"
        
        print(f"📄 Document analysis complete. Type: {doc_type}, Score: {results['score']}")
        
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        print(f"✅ PDF analysis complete. Returning results with AI: {results.get('ai_available', False)}")
        return JSONResponse(results)
        
    except Exception as e:
        return JSONResponse({
            "error": f"Failed to analyze document: {str(e)}",
            "score": 0,
            "issues": [],
            "summary": "Document analysis failed"
        }, status_code=500
            
        )


# Results page
@app.get("/results")
async def results_page(request: Request):
    """Results display page"""
    return templates.TemplateResponse("analyze.html", {"request": request})

# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "checker_available": CHECKER_AVAILABLE,
        "service": "A11y Wizard"
    }

@app.post("/analyze/url/debug")
async def analyze_url_debug(request: Request, url: str = Form(...)):
    """Debug endpoint to see raw axe-core data"""
    try:
        from accessibility_checker import AccessibilityChecker
        checker = AccessibilityChecker()
        
        if hasattr(checker, '_check_with_playwright'):
            # Get raw data
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(2000)
                
                from axe_core_python.async_playwright import Axe
                axe = Axe()
                raw_results = await axe.run(page)
                
                await browser.close()
                
                # Show everything
                return JSONResponse({
                    "url": url,
                    "raw_violations_count": len(raw_results.get("violations", [])),
                    "raw_incomplete_count": len(raw_results.get("incomplete", [])),
                    "raw_passes_count": len(raw_results.get("passes", [])),
                    "violations_detail": [
                        {
                            "id": v.get("id"),
                            "impact": v.get("impact"),
                            "description": v.get("description"),
                            "node_count": len(v.get("nodes", [])),
                            "nodes_sample": [n.get("html", "")[:100] for n in v.get("nodes", [])[:2]]
                        }
                        for v in raw_results.get("violations", [])
                    ],
                    "full_violations": raw_results.get("violations", [])
                })
        
        return JSONResponse({"error": "Playwright not available"})
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    
@app.post("/debug/axe-raw")
async def debug_axe_raw(request: Request, url: str = Form(...)):
    """Get raw axe-core data for debugging"""
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            await page.goto(url, wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(3000)
            
            from axe_core_python.async_playwright import Axe
            axe = Axe()
            raw_results = await axe.run(page)
            
            await browser.close()
            
            # Analyze what axe-core found
            violations = raw_results.get("violations", [])
            incomplete = raw_results.get("incomplete", [])
            passes = raw_results.get("passes", [])
            
            return JSONResponse({
                "url": url,
                "summary": {
                    "total_violations": len(violations),
                    "total_incomplete": len(incomplete),
                    "total_passes": len(passes),
                    "total_checks": len(violations) + len(incomplete) + len(passes)
                },
                "violations_by_id": [
                    {
                        "id": v["id"],
                        "impact": v.get("impact", "moderate"),
                        "description": v.get("description", ""),
                        "help": v.get("help", ""),
                        "node_count": len(v.get("nodes", [])),
                        "nodes_sample": [n.get("html", "")[:100] for n in v.get("nodes", [])[:2]]
                    }
                    for v in violations
                ],
                "incomplete_by_id": [
                    {
                        "id": i["id"],
                        "impact": i.get("impact", "moderate"),
                        "description": i.get("description", ""),
                        "node_count": len(i.get("nodes", []))
                    }
                    for i in incomplete
                ],
                "passes_by_id": [p["id"] for p in passes[:10]],  # First 10 only
                "scoring_debug": {
                    "score_calculation": self._debug_score_calculation(violations, incomplete, passes)
                }
            })
            
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
