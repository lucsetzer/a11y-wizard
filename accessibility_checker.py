# accessibility_checker.py - COMPLETE WORKING VERSION
import asyncio
from typing import Dict, List, Any

try:
    from playwright.async_api import async_playwright
    from axe_core_python.async_playwright import Axe
    PLAYWRIGHT_AVAILABLE = True
    print("✅ Playwright + axe-core available")
except ImportError as e:
    PLAYWRIGHT_AVAILABLE = False
    print(f"⚠️ Playwright/axe-core not available: {e}")

class AccessibilityChecker:
    """Main accessibility checker"""
    
    def __init__(self):
        self.timeout = 30000
    
    async def check_url(self, url: str) -> Dict[str, Any]:
        """Check a URL for accessibility issues"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Try Playwright first if available
        if PLAYWRIGHT_AVAILABLE:
            try:
                print(f"🔍 Using Playwright to analyze: {url}")
                return await self._check_with_playwright(url)
            except Exception as e:
                print(f"⚠️ Playwright failed: {e}")
                print("🔄 Falling back to simple checker...")
        
        # Fallback to simple checker
        return await self._check_with_simple(url)
    
    async def _check_with_playwright(self, url: str) -> Dict[str, Any]:
        """Use Playwright + axe-core"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=self.timeout)
                await page.wait_for_timeout(2000)
                
                axe = Axe()
                results = await axe.run(page)
                
                return self._process_axe_results(url, results)
                
            finally:
                await browser.close()
    
    def _process_axe_results(self, url: str, axe_data: Dict) -> Dict[str, Any]:
        """Process axe-core results"""
        violations = axe_data.get("violations", [])
        incomplete = axe_data.get("incomplete", [])
        passes = axe_data.get("passes", [])
        
        issues = []
        
        # Process violations
        for violation in violations:
            node_count = len(violation.get("nodes", []))
            issues.append({
                "type": "critical",
                "title": violation.get("id", "Violation").replace("-", " ").title(),
                "count": node_count,
                "description": violation.get("description", ""),
                "help": violation.get("help", ""),
                "helpUrl": violation.get("helpUrl", ""),
                "impact": violation.get("impact", "moderate"),
                "fix": self._get_fix_suggestion(violation.get("id", "")),
                "category": self._get_category(violation.get("tags", [])),
                "nodes": violation.get("nodes", [])[:2]
            })
        
        # Process incomplete
        for item in incomplete:
            node_count = len(item.get("nodes", []))
            issues.append({
                "type": "warning",
                "title": item.get("id", "Review").replace("-", " ").title(),
                "count": node_count,
                "description": f"Needs review: {item.get('description', '')}",
                "impact": item.get("impact", "moderate"),
                "fix": "Manual review required.",
                "category": self._get_category(item.get("tags", []))
            })
        
        # Calculate score
        score = self._calculate_score(violations, incomplete, passes)
        
        return {
            "url": url,
            "score": score,
            "issues": issues[:20],  # Limit issues
            "summary": self._generate_summary(violations, incomplete, score),
            "method": "axe-core",
            "violation_count": len(violations),
            "warning_count": len(incomplete),
            "pass_count": len(passes)
        }
    
    def _calculate_score(self, violations, incomplete, passes) -> int:
        """STRICT scoring for university compliance"""
        total = len(violations) + len(incomplete) + len(passes)
        
        if total == 0:
            return 100
        
        # University scoring is VERY strict
        # Start from 100, deduct heavily for any issues
        
        score = 100
        
        # CRITICAL: Any violation is a major deduction
        for v in violations:
            impact = v.get("impact", "moderate").lower()
            
            # University penalty scale (much stricter!)
            if impact == "critical":
                score -= 15  # Major legal risk
            elif impact == "serious":
                score -= 10  # Serious compliance issue
            elif impact == "moderate":
                score -= 7   # Moderate - still needs fixing
            else:  # minor
                score -= 4   # Minor - still unacceptable for universities
        
        # Warnings also matter for universities
        score -= len(incomplete) * 3
        
        # Bonus for high pass rate (encourage comprehensive testing)
        pass_rate = len(passes) / total
        if pass_rate > 0.95:
            score += 5  # Bonus for excellent coverage
        
        # University minimum: 80, but aim for 95+
        score = max(60, min(100, score))  # Never below 60 even with issues
        
        # If score < 90, add a compliance warning
        if score < 90:
            print("⚠️ UNIVERSITY COMPLIANCE WARNING: Score below 90%")
        
        return int(score)
    
    async def _check_with_simple(self, url: str) -> Dict[str, Any]:
        """Simple HTML checker fallback"""
        try:
            import aiohttp
            from bs4 import BeautifulSoup
        
            async with aiohttp.ClientSession() as session:
                # ADD PROPER BROWSER HEADERS
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=10, ssl=False) as resp:
                    if resp.status == 403:
                        return self._error_result(url, f"Website blocked access (403 Forbidden)")
                    if resp.status != 200:
                        return self._error_result(url, f"HTTP {resp.status}")
                    html = await resp.text()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            issues = []
            
            # Check images
            images = soup.find_all('img')
            images_no_alt = [img for img in images if not img.get('alt')]
            if images_no_alt:
                issues.append({
                    "type": "critical",
                    "title": "Missing Image Alt Text",
                    "count": len(images_no_alt),
                    "description": "Images without alt text",
                    "fix": "Add alt='description' to images",
                    "category": "Images"
                })
            
            # Check lang attribute
            html_tag = soup.find('html')
            if not html_tag or not html_tag.get('lang'):
                issues.append({
                    "type": "critical",
                    "title": "Missing Language Attribute",
                    "count": 1,
                    "description": "HTML missing lang attribute",
                    "fix": "Add lang='en' to <html> tag",
                    "category": "Page Structure"
                })
            
            score = max(0, 100 - (len(issues) * 15))
            
            return {
                "url": url,
                "score": score,
                "issues": issues,
                "summary": f"Simple check found {len(issues)} issues",
                "method": "simple"
            }
            
        except Exception as e:
            return self._error_result(url, f"Simple checker failed: {str(e)}")
    
    def _get_fix_suggestion(self, issue_id: str) -> str:
        """Get fix suggestion for issue"""
        fixes = {
            "document-title": "Add a descriptive <title> element in the <head> section.",
            "image-alt": "Add alt text to images. Use alt='' for decorative images.",
            "html-has-lang": "Add lang attribute to <html> tag, e.g., <html lang='en'>.",
            "color-contrast": "Increase color contrast ratio to at least 4.5:1.",
            "link-name": "Links should have descriptive text content.",
            "button-name": "Buttons should have accessible names.",
            "label": "Form inputs should have associated <label> elements.",
            "aria-hidden-focus": "Don't hide focusable elements from screen readers."
        }
        return fixes.get(issue_id, "Review WCAG guidelines and fix accordingly.")
    
    def _get_category(self, tags: List[str]) -> str:
        """Get category from tags"""
        if "cat.color" in tags:
            return "Color"
        elif "cat.forms" in tags:
            return "Forms"
        elif "cat.images" in tags:
            return "Images"
        elif "cat.language" in tags:
            return "Language"
        elif "cat.structure" in tags:
            return "Structure"
        return "General"
    
    def _generate_summary(self, violations, incomplete, score) -> str:
        """Generate summary text"""
        if score >= 90:
            emoji = "✅"
            text = "Excellent"
        elif score >= 70:
            emoji = "⚠️"
            text = "Good"
        elif score >= 50:
            emoji = "🔧"
            text = "Needs Work"
        else:
            emoji = "❌"
            text = "Poor"
        
        return f"{emoji} {text} - Score: {score}/100. {len(violations)} violations, {len(incomplete)} warnings."
    
    def _error_result(self, url: str, error: str) -> Dict[str, Any]:
        """Create error result"""
        return {
            "url": url,
            "score": 0,
            "issues": [{
                "type": "critical",
                "title": "Analysis Failed",
                "count": 1,
                "description": error[:100],
                "fix": "Try again with a different URL",
                "category": "Error"
            }],
            "summary": f"Failed: {error[:50]}",
            "method": "error"
        }
