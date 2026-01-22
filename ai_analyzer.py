# ai_analyzer.py - FIXED VERSION
import os
import json
from typing import Dict, List, Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class AIAccessibilityAnalyzer:
    """Use DeepSeek AI for accessibility insights"""
    
    async def analyze_with_custom_prompt(self, prompt: str, context: Dict = None) -> Dict[str, Any]:
        """Call DeepSeek with a custom prompt (for documents)"""
    
        if not self.available or not self.client:
            return self._mock_response(0, [], "No API client for custom prompt")
        
        try:
            print(f"🤖 DEEPSEEK: Calling API with custom prompt ({len(prompt)} chars)...")
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a document accessibility expert specializing in PDF, Word, and text documents. Provide practical, tool-specific advice."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            print(f"✅ DEEPSEEK: Custom prompt success! Response: {len(content)} chars")
            
            # Try to parse JSON
            try:
                # Find JSON in response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = content[start:end]
                    data = json.loads(json_str)
                    data["ai_source"] = "DeepSeek AI (Document Analysis)"
                    
                    # Add context if provided
                    if context:
                        data["context"] = context
                        
                    return data
            except json.JSONDecodeError as e:
                print(f"⚠️ Could not parse JSON from AI response: {e}")
            
            # If JSON fails, return structured text response
            return {
                "summary": f"Document Accessibility Analysis: {content[:250]}...",
                "full_analysis": content,
                "ai_source": "DeepSeek AI (Document Analysis - Text)",
                "context": context or {},
                "priority_issues": [
                    {
                        "title": "Review Document Structure",
                        "reason": "AI analysis generated successfully",
                        "detailed_fixes": ["See full_analysis field for complete recommendations"]
                    }
                ]
            }
            
        except Exception as e:
            print(f"❌ DEEPSEEK API error in custom prompt: {e}")
            return {
                "error": f"API Error: {str(e)}",
                "summary": "Failed to get AI analysis for document",
                "ai_source": "Error",
                "context": context or {}
            }
    
    
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if self.api_key and self.api_key.startswith("sk-"):
            print("✅ DEEPSEEK: Real API key detected!")
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )
            self.available = True
        else:
            print("⚠️ DEEPSEEK: Using mock (no valid API key)")
            print(f"   Key found: {'Yes' if self.api_key else 'No'}")
            if self.api_key:
                print(f"   Key starts with sk-: {self.api_key.startswith('sk-')}")
            self.client = None
            self.available = False
    
    async def analyze_accessibility_results(self, 
                                          url: str, 
                                          score: int, 
                                          issues: List[Dict], 
                                          raw_data: Dict = None) -> Dict[str, Any]:
        """Get AI analysis - FIXED: accepts raw_data parameter"""
        
        if not self.available:
            return self._mock_response(score, issues, "No API client")
        
        try:
            print("🤖 DEEPSEEK: Calling API...")
            
            # Simple prompt
            prompt = f"""Analyze these web accessibility results:

URL: {url}
Score: {score}/100
Issues: {len(issues)}

Top issues:
{chr(10).join([f"- {issue.get('title')}: {issue.get('description', '')[:100]}" for issue in issues[:5]])}

Provide JSON with: priority_issues[], summary, next_steps[], estimated_effort"""
            
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are an accessibility expert. Provide practical advice."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            print(f"✅ DEEPSEEK: API success! Response: {len(content)} chars")
            
            # Try to parse JSON
            try:
                # Find JSON in response
                start = content.find('{')
                end = content.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = content[start:end]
                    data = json.loads(json_str)
                    data["ai_source"] = "DeepSeek AI (Real)"
                    return data
            except:
                pass
            
            # If JSON fails, return text
            return {
                "summary": f"DeepSeek AI Analysis: {content[:200]}...",
                "ai_source": "DeepSeek AI (Real - Text)",
                "full_response": content
            }
            
        except Exception as e:
            print(f"❌ DEEPSEEK API error: {e}")
            return self._mock_response(score, issues, f"API Error: {str(e)}")
    
    def _mock_response(self, score: int, issues: List[Dict], reason: str) -> Dict[str, Any]:
        """Mock response"""
        return {
            "priority_issues": [{
                "title": "Configure API for Real AI",
                "reason": reason,
                "impact": "Get real insights with valid API key",
                "detailed_fixes": ["Use valid DeepSeek API key in .env"],
                "wcag_references": ["WCAG 2.1"]
            }],
            "summary": f"Mock AI | Score: {score}/100 | {reason}",
            "next_steps": ["Get API key from platform.deepseek.com"],
            "estimated_effort": "Unknown",
            "ai_source": "Mock (needs API key)"
        }
