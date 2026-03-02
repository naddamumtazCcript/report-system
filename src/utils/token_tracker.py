"""
Token tracking utility for monitoring OpenAI API usage
"""
import json
from datetime import datetime

class TokenTracker:
    def __init__(self):
        self.operations = []
        self.total_tokens = 0
        self.total_cost = 0
        
    def track(self, operation_name, response):
        """Track tokens from OpenAI response"""
        if hasattr(response, 'usage'):
            usage = response.usage
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
            
            # GPT-4o-mini pricing: $0.150 per 1M input, $0.600 per 1M output
            cost = (prompt_tokens * 0.150 / 1_000_000) + (completion_tokens * 0.600 / 1_000_000)
            
            self.operations.append({
                "operation": operation_name,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost": cost
            })
            
            self.total_tokens += total_tokens
            self.total_cost += cost
            
            return {
                "tokens": total_tokens,
                "cost": cost
            }
        return None
    
    def get_summary(self):
        """Get summary of all tracked operations"""
        return {
            "operations": self.operations,
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 6),
            "timestamp": datetime.now().isoformat()
        }
    
    def print_summary(self):
        """Print formatted summary"""
        print("\n" + "="*60)
        print("TOKEN USAGE SUMMARY")
        print("="*60)
        
        for op in self.operations:
            print(f"\n{op['operation']}:")
            print(f"  Prompt tokens: {op['prompt_tokens']:,}")
            print(f"  Completion tokens: {op['completion_tokens']:,}")
            print(f"  Total tokens: {op['total_tokens']:,}")
            print(f"  Cost: ${op['cost']:.6f}")
        
        print("\n" + "-"*60)
        print(f"TOTAL TOKENS: {self.total_tokens:,}")
        print(f"TOTAL COST: ${self.total_cost:.6f}")
        print("="*60 + "\n")
