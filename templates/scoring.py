# scoring.py - Better scoring logic
class AccessibilityScorer:
    """Better, more nuanced scoring system"""
    
    @staticmethod
    def calculate_score(axe_results):
        """Calculate a fair accessibility score from axe results"""
        violations = axe_results.get("violations", [])
        incomplete = axe_results.get("incomplete", [])
        passes = axe_results.get("passes", [])
        
        total_checks = len(violations) + len(incomplete) + len(passes)
        
        if total_checks == 0:
            return 100
        
        # Weight by impact and prevalence
        base_score = 100
        
        for violation in violations:
            impact = violation.get("impact", "moderate").lower()
            nodes_count = len(violation.get("nodes", []))
            
            # Impact weights
            if impact == "critical":
                weight = 0.8  # Very important
            elif impact == "serious":
                weight = 0.6
            elif impact == "moderate":
                weight = 0.4
            else:  # minor
                weight = 0.2
            
            # Node count factor (logarithmic - first few matter most)
            node_factor = min(1.0, 0.2 + (0.8 * (1 - 0.9 ** nodes_count)))
            
            # Deduct score
            deduction = 10 * weight * node_factor
            base_score -= deduction
        
        # Incomplete/warnings have less impact
        for item in incomplete:
            base_score -= 2 * min(1.0, 0.5 * (1 - 0.95 ** len(item.get("nodes", []))))
        
        # Bonus for passes
        pass_bonus = len(passes) * 0.5
        base_score += min(20, pass_bonus)  # Max 20 bonus
        
        return max(0, min(100, int(base_score)))
    
    @staticmethod
    def get_grade(score):
        """Convert score to letter grade"""
        if score >= 95:
            return "A+", "🏆 Excellent"
        elif score >= 90:
            return "A", "✅ Very Good"
        elif score >= 85:
            return "A-", "👍 Good"
        elif score >= 80:
            return "B+", "⚠️ Above Average"
        elif score >= 75:
            return "B", "⚠️ Average"
        elif score >= 70:
            return "B-", "⚠️ Below Average"
        elif score >= 60:
            return "C", "🔧 Needs Work"
        elif score >= 50:
            return "D", "🚨 Poor"
        else:
            return "F", "🚨 Very Poor"
