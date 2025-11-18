# cost_monitor.py - Track API costs in real-time

import json
import os
from datetime import datetime
from pathlib import Path

COST_LOG_FILE = "api_costs.json"

# Vertex AI Pricing (as of Nov 2024)
PRICING = {
    'gemini-1.5-flash': {
        'input': 0.075 / 1_000_000,   # $0.075 per 1M tokens
        'output': 0.30 / 1_000_000     # $0.30 per 1M tokens
    },
    'gemini-1.5-pro': {
        'input': 1.25 / 1_000_000,     # $1.25 per 1M tokens
        'output': 5.00 / 1_000_000     # $5.00 per 1M tokens
    },
    'gemini-2.0-flash': {
        'input': 0.075 / 1_000_000,    # Same as 1.5-flash
        'output': 0.30 / 1_000_000
    }
}

class CostMonitor:
    """Track and monitor API usage costs"""
    
    def __init__(self, budget_limit=300.0, alert_thresholds=[50, 200, 290]):
        self.budget_limit = budget_limit
        self.alert_thresholds = sorted(alert_thresholds)
        self.cost_log_file = COST_LOG_FILE
        self.costs = self._load_costs()
        self.alerts_sent = set()
        
    def _load_costs(self):
        """Load cost history from file"""
        if os.path.exists(self.cost_log_file):
            with open(self.cost_log_file, 'r') as f:
                return json.load(f)
        return {
            'total_cost': 0.0,
            'monthly_costs': {},
            'daily_costs': {},
            'queries': []
        }
    
    def _save_costs(self):
        """Save cost history to file"""
        with open(self.cost_log_file, 'w') as f:
            json.dump(self.costs, f, indent=2)
    
    def log_query(self, model_name, input_tokens, output_tokens, operation='query'):
        """
        Log a single API query and calculate cost.
        
        Args:
            model_name: Model used (e.g., 'gemini-1.5-flash')
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            operation: Type of operation (e.g., 'query', 'routing', 'chat')
        """
        # Get pricing for model (default to flash if unknown)
        pricing = PRICING.get(model_name, PRICING['gemini-1.5-flash'])
        
        # Calculate cost
        input_cost = input_tokens * pricing['input']
        output_cost = output_tokens * pricing['output']
        total_cost = input_cost + output_cost
        
        # Update totals
        self.costs['total_cost'] += total_cost
        
        # Track by date
        today = datetime.now().strftime('%Y-%m-%d')
        month = datetime.now().strftime('%Y-%m')
        
        if month not in self.costs['monthly_costs']:
            self.costs['monthly_costs'][month] = 0.0
        self.costs['monthly_costs'][month] += total_cost
        
        if today not in self.costs['daily_costs']:
            self.costs['daily_costs'][today] = 0.0
        self.costs['daily_costs'][today] += total_cost
        
        # Log query details
        self.costs['queries'].append({
            'timestamp': datetime.now().isoformat(),
            'model': model_name,
            'operation': operation,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost': total_cost
        })
        
        # Keep only last 1000 queries to prevent file bloat
        if len(self.costs['queries']) > 1000:
            self.costs['queries'] = self.costs['queries'][-1000:]
        
        # Save
        self._save_costs()
        
        # Check for alerts
        self._check_alerts()
        
        return total_cost
    
    def _check_alerts(self):
        """Check if we've crossed any budget thresholds"""
        total = self.costs['total_cost']
        
        for threshold in self.alert_thresholds:
            if total >= threshold and threshold not in self.alerts_sent:
                self._send_alert(threshold, total)
                self.alerts_sent.add(threshold)
    
    def _send_alert(self, threshold, current_cost):
        """Send budget alert (print to console and log)"""
        remaining = self.budget_limit - current_cost
        percent = (current_cost / self.budget_limit) * 100
        
        message = f"""
╔═══════════════════════════════════════════════════════════╗
║                  🚨 BUDGET ALERT 🚨                       ║
╠═══════════════════════════════════════════════════════════╣
║  Threshold Reached: ${threshold:.2f}                      ║
║  Current Spending:  ${current_cost:.2f} ({percent:.1f}%)  ║
║  Budget Remaining:  ${remaining:.2f}                      ║
║  Budget Limit:      ${self.budget_limit:.2f}              ║
╚═══════════════════════════════════════════════════════════╝
"""
        print(message)
        
        # Log alert
        alert_log = "budget_alerts.log"
        with open(alert_log, 'a') as f:
            f.write(f"\n{datetime.now().isoformat()}\n")
            f.write(message)
            f.write("\n")
        
        # If critical (near limit), show emergency instructions
        if remaining < 20:
            emergency_msg = """
⚠️  CRITICAL: Less than $20 remaining!

To stop all charges immediately:
1. Run: gcloud billing projects unlink rag-chatbot-475316
2. Or disable Vertex AI: gcloud services disable aiplatform.googleapis.com
3. Or visit: https://console.cloud.google.com/billing

Your system will stop working but you won't be charged.
"""
            print(emergency_msg)
    
    def get_summary(self):
        """Get cost summary"""
        total = self.costs['total_cost']
        remaining = self.budget_limit - total
        percent = (total / self.budget_limit) * 100
        
        today = datetime.now().strftime('%Y-%m-%d')
        today_cost = self.costs['daily_costs'].get(today, 0.0)
        
        month = datetime.now().strftime('%Y-%m')
        month_cost = self.costs['monthly_costs'].get(month, 0.0)
        
        total_queries = len(self.costs['queries'])
        avg_cost_per_query = total / total_queries if total_queries > 0 else 0
        
        return {
            'total_cost': total,
            'remaining_budget': remaining,
            'percent_used': percent,
            'today_cost': today_cost,
            'month_cost': month_cost,
            'total_queries': total_queries,
            'avg_cost_per_query': avg_cost_per_query,
            'estimated_queries_remaining': int(remaining / avg_cost_per_query) if avg_cost_per_query > 0 else 0
        }
    
    def print_summary(self):
        """Print cost summary to console"""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print(" "*20 + "💰 COST SUMMARY 💰")
        print("="*60)
        print(f"  Total Spent:        ${summary['total_cost']:.4f} ({summary['percent_used']:.1f}%)")
        print(f"  Remaining Budget:   ${summary['remaining_budget']:.2f}")
        print(f"  Today's Cost:       ${summary['today_cost']:.4f}")
        print(f"  This Month:         ${summary['month_cost']:.2f}")
        print(f"  Total Queries:      {summary['total_queries']}")
        print(f"  Avg Cost/Query:     ${summary['avg_cost_per_query']:.6f}")
        print(f"  Est. Queries Left:  {summary['estimated_queries_remaining']:,}")
        print("="*60 + "\n")
    
    def reset_monthly(self):
        """Reset monthly tracking (call at start of new month)"""
        month = datetime.now().strftime('%Y-%m')
        if month not in self.costs['monthly_costs']:
            self.costs['monthly_costs'][month] = 0.0
        self._save_costs()

# Global instance
_monitor = None

def get_monitor():
    """Get global cost monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = CostMonitor(budget_limit=300.0, alert_thresholds=[50, 200, 290])
    return _monitor

def log_api_call(model_name, input_tokens, output_tokens, operation='query'):
    """
    Convenience function to log an API call.
    
    Usage:
        from cost_monitor import log_api_call
        log_api_call('gemini-1.5-flash', 500, 200, 'chat')
    """
    monitor = get_monitor()
    return monitor.log_query(model_name, input_tokens, output_tokens, operation)

def print_cost_summary():
    """Print current cost summary"""
    monitor = get_monitor()
    monitor.print_summary()

if __name__ == "__main__":
    # Test the monitor
    monitor = CostMonitor(budget_limit=300.0, alert_thresholds=[50, 200, 290])
    
    # Simulate some queries
    print("Simulating API calls...")
    for i in range(10):
        cost = monitor.log_query('gemini-1.5-flash', 500, 200, 'test')
        print(f"Query {i+1}: ${cost:.6f}")
    
    # Print summary
    monitor.print_summary()
