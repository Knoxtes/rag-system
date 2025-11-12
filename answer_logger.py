# answer_logger.py - Simple logging system for user questions and answers

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
import re

class AnswerLogger:
    """
    Simple logging system for tracking user questions and system answers
    in a clean, copy-pastable format without markdown styling.
    """
    
    def __init__(self, log_file: str = "answer_log.txt", json_log: str = "answer_log.json"):
        """
        Initialize the answer logger.
        
        Args:
            log_file: Path to the plain text log file
            json_log: Path to the JSON log file for structured data
        """
        self.log_file = log_file
        self.json_log = json_log
        
        # Create log files if they don't exist
        self._initialize_log_files()
    
    def _initialize_log_files(self):
        """Initialize log files with headers if they don't exist"""
        
        # Initialize plain text log
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write("RAG SYSTEM ANSWER LOG\n")
                f.write("=" * 50 + "\n")
                f.write(f"Log started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Initialize JSON log
        if not os.path.exists(self.json_log):
            with open(self.json_log, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)
    
    def log_qa_pair(self, question: str, answer: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Log a question-answer pair to both text and JSON formats.
        
        Args:
            question: User's question
            answer: System's answer
            metadata: Optional metadata (sources, timing, etc.)
        """
        
        timestamp = datetime.now()
        
        # Clean the answer text (remove markdown)
        clean_answer = self._clean_markdown(answer)
        
        # Log to plain text file
        self._log_to_text(question, clean_answer, timestamp, metadata)
        
        # Log to JSON file
        self._log_to_json(question, clean_answer, timestamp, metadata)
    
    def _clean_markdown(self, text: str) -> str:
        """
        Remove markdown formatting from text for clean copy-paste.
        
        Args:
            text: Text with potential markdown formatting
            
        Returns:
            Clean text without markdown
        """
        
        if not text:
            return ""
        
        # Remove bold/italic markers
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
        text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__
        text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_
        
        # Remove headers (# ## ###)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # Remove code blocks
        text = re.sub(r'```[^`]*```', '[CODE BLOCK]', text, flags=re.DOTALL)
        text = re.sub(r'`([^`]+)`', r'\1', text)  # Inline code
        
        # Remove links [text](url)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        
        # Remove bullet points and list markers
        text = re.sub(r'^\s*[-*+]\s+', '• ', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # Clean up extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 consecutive newlines
        text = text.strip()
        
        return text
    
    def _log_to_text(self, question: str, answer: str, timestamp: datetime, metadata: Optional[Dict[str, Any]]):
        """Log to plain text file in copy-pastable format"""
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write("-" * 80 + "\n")
            f.write(f"TIME: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"QUESTION: {question}\n")
            f.write("\n")
            f.write("ANSWER:\n")
            f.write(answer)
            f.write("\n")
            
            # Add metadata if available
            if metadata:
                f.write("\n")
                f.write("METADATA:\n")
                
                if metadata.get('sources'):
                    f.write(f"Sources: {', '.join(metadata['sources'])}\n")
                
                if metadata.get('response_time'):
                    f.write(f"Response time: {metadata['response_time']:.2f}s\n")
                
                if metadata.get('cached'):
                    f.write(f"Cached response: {metadata['cached']}\n")
                
                if metadata.get('quality_score'):
                    f.write(f"Quality score: {metadata['quality_score']:.2f}\n")
            
            f.write("\n" + "=" * 80 + "\n\n")
    
    def _log_to_json(self, question: str, answer: str, timestamp: datetime, metadata: Optional[Dict[str, Any]]):
        """Log to JSON file for structured access"""
        
        # Read existing data
        try:
            with open(self.json_log, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            log_data = []
        
        # Create new entry
        entry = {
            'timestamp': timestamp.isoformat(),
            'question': question,
            'answer': answer,
            'metadata': metadata or {}
        }
        
        # Add to log
        log_data.append(entry)
        
        # Write back to file
        with open(self.json_log, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
    
    def search_logs(self, query: str, limit: int = 10) -> list:
        """
        Search through logged Q&A pairs.
        
        Args:
            query: Search term
            limit: Maximum number of results
            
        Returns:
            List of matching entries
        """
        
        try:
            with open(self.json_log, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        
        results = []
        query_lower = query.lower()
        
        for entry in reversed(log_data):  # Most recent first
            if (query_lower in entry['question'].lower() or 
                query_lower in entry['answer'].lower()):
                results.append(entry)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_recent_logs(self, count: int = 10) -> list:
        """
        Get the most recent Q&A pairs.
        
        Args:
            count: Number of recent entries to return
            
        Returns:
            List of recent entries
        """
        
        try:
            with open(self.json_log, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
        
        return log_data[-count:] if log_data else []
    
    def export_logs(self, output_file: str, format: str = 'txt'):
        """
        Export logs in different formats.
        
        Args:
            output_file: Output file path
            format: Export format ('txt', 'csv', 'json')
        """
        
        try:
            with open(self.json_log, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            log_data = []
        
        if format == 'txt':
            self._export_to_txt(log_data, output_file)
        elif format == 'csv':
            self._export_to_csv(log_data, output_file)
        elif format == 'json':
            self._export_to_json(log_data, output_file)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_to_txt(self, log_data: list, output_file: str):
        """Export to plain text format"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("RAG SYSTEM EXPORTED LOGS\n")
            f.write("=" * 50 + "\n\n")
            
            for entry in log_data:
                timestamp = datetime.fromisoformat(entry['timestamp'])
                f.write(f"TIME: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"QUESTION: {entry['question']}\n")
                f.write(f"ANSWER: {entry['answer']}\n")
                
                if entry.get('metadata'):
                    f.write(f"METADATA: {json.dumps(entry['metadata'])}\n")
                
                f.write("-" * 80 + "\n\n")
    
    def _export_to_csv(self, log_data: list, output_file: str):
        """Export to CSV format"""
        
        import csv
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestamp', 'Question', 'Answer', 'Metadata'])
            
            for entry in log_data:
                writer.writerow([
                    entry['timestamp'],
                    entry['question'],
                    entry['answer'],
                    json.dumps(entry.get('metadata', {}))
                ])
    
    def _export_to_json(self, log_data: list, output_file: str):
        """Export to JSON format"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        
        try:
            with open(self.json_log, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            log_data = []
        
        if not log_data:
            return {'total_entries': 0}
        
        # Calculate stats
        total_entries = len(log_data)
        
        # Get date range
        first_entry = datetime.fromisoformat(log_data[0]['timestamp'])
        last_entry = datetime.fromisoformat(log_data[-1]['timestamp'])
        
        # Calculate average response times if available
        response_times = []
        cached_count = 0
        
        for entry in log_data:
            metadata = entry.get('metadata', {})
            if metadata.get('response_time'):
                response_times.append(metadata['response_time'])
            if metadata.get('cached'):
                cached_count += 1
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else None
        cache_hit_rate = (cached_count / total_entries) * 100 if total_entries > 0 else 0
        
        return {
            'total_entries': total_entries,
            'first_entry': first_entry.strftime('%Y-%m-%d %H:%M:%S'),
            'last_entry': last_entry.strftime('%Y-%m-%d %H:%M:%S'),
            'average_response_time': f"{avg_response_time:.2f}s" if avg_response_time else "N/A",
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'log_file_size': os.path.getsize(self.log_file) if os.path.exists(self.log_file) else 0
        }


# Example usage and testing
if __name__ == "__main__":
    # Test the logger
    logger = AnswerLogger()
    
    print("🔍 Testing Answer Logger")
    print("-" * 30)
    
    # Test logging
    test_question = "What is our company's remote work policy?"
    test_answer = """**Our Remote Work Policy:**

• Employees can work remotely up to 3 days per week
• Must maintain core hours of 9 AM - 3 PM in local timezone
• Required to attend in-person meetings when scheduled
• Home office setup budget: $500 per employee

For more details, see the [Employee Handbook](link) or contact HR."""
    
    test_metadata = {
        'sources': ['Employee Handbook', 'HR Policy Doc'],
        'response_time': 1.23,
        'cached': False,
        'quality_score': 0.92
    }
    
    logger.log_qa_pair(test_question, test_answer, test_metadata)
    print("✅ Logged test Q&A pair")
    
    # Test another entry
    logger.log_qa_pair(
        "How do I submit an expense report?", 
        "Submit expense reports through the company portal at expenses.company.com. Include receipts for all expenses over $25.",
        {'sources': ['Finance Portal'], 'response_time': 0.89, 'cached': True}
    )
    print("✅ Logged second Q&A pair")
    
    # Show stats
    stats = logger.get_stats()
    print(f"\n📊 Logging Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test search
    search_results = logger.search_logs("remote work")
    print(f"\n🔍 Search results for 'remote work': {len(search_results)} found")
    
    print(f"\n📄 Logs saved to:")
    print(f"  Plain text: {logger.log_file}")
    print(f"  JSON: {logger.json_log}")
    
    print(f"\nThe plain text log is formatted for easy copy-pasting!")