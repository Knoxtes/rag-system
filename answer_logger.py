"""
Minimal Answer Logger for production RAG system
"""
import json
import os
from datetime import datetime


class AnswerLogger:
    """Simple logger for Q&A pairs in production"""
    
    def __init__(self, log_file="answer_log.json"):
        self.log_file = log_file
    
    def log_qa_pair(self, question, answer, metadata=None):
        """Log a question-answer pair with optional metadata"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "answer": answer,
                "metadata": metadata or {}
            }
            
            # Append to log file
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error logging Q&A pair: {e}")