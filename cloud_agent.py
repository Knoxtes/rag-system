"""
Cloud Agent Module - Delegates AI operations to cloud-based services

This module provides an abstraction layer for delegating AI operations
to cloud-based agents (Vertex AI/Google Cloud) or fallback consumer APIs.
"""

import os
from typing import Optional
from config import USE_VERTEX_AI, PROJECT_ID, LOCATION, GOOGLE_API_KEY, GEMINI_MODEL

# Import required modules
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel as VertexGenerativeModel
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    print("⚠️  Vertex AI not installed. Install with: pip install google-cloud-aiplatform")

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("⚠️  Google Generative AI not installed.")


class CloudAgentDelegate:
    """
    Delegates AI operations to cloud-based agents.
    
    This class provides a centralized way to delegate AI model operations
    to cloud services (Vertex AI) or fallback to consumer APIs.
    """
    
    def __init__(self, use_vertex: bool = USE_VERTEX_AI, 
                 project_id: str = PROJECT_ID,
                 location: str = LOCATION,
                 api_key: Optional[str] = GOOGLE_API_KEY):
        """
        Initialize the cloud agent delegate.
        
        Args:
            use_vertex: Whether to use Vertex AI (cloud) or consumer API
            project_id: Google Cloud project ID for Vertex AI
            location: Google Cloud location (e.g., 'us-central1')
            api_key: API key for consumer API fallback
        """
        self.use_vertex = use_vertex
        self.project_id = project_id
        self.location = location
        self.api_key = api_key
        self._initialized = False
    
    def get_model(self, model_name: str = GEMINI_MODEL):
        """
        Delegate to cloud agent to get an AI model instance.
        
        This method delegates the model initialization to either:
        - Vertex AI (Google Cloud) - preferred for production
        - Consumer API - fallback for development
        
        Args:
            model_name: Name of the model to use
            
        Returns:
            An initialized AI model instance (VertexGenerativeModel or GenerativeModel)
        """
        if self.use_vertex:
            return self._delegate_to_vertex_ai(model_name)
        else:
            return self._delegate_to_consumer_api(model_name)
    
    def _delegate_to_vertex_ai(self, model_name: str):
        """
        Delegate to Vertex AI cloud agent.
        
        Args:
            model_name: Name of the model to use
            
        Returns:
            VertexGenerativeModel instance
        """
        if not VERTEX_AI_AVAILABLE:
            print("⚠️  Vertex AI not available, falling back to consumer API")
            return self._delegate_to_consumer_api(model_name)
        
        if not self._initialized:
            # Initialize Vertex AI with cloud project
            vertexai.init(project=self.project_id, location=self.location)
            self._initialized = True
            print(f"  ☁️  Cloud Agent: Delegating to Vertex AI (Project: {self.project_id})")
        
        # Map consumer model names to Vertex AI model names
        vertex_model_map = {
            'gemini-2.5-flash': 'gemini-2.5-flash',
            'gemini-2.0-flash-exp': 'gemini-2.0-flash-exp',
            'gemini-1.5-flash': 'gemini-1.5-flash',
            'gemini-1.5-pro': 'gemini-1.5-pro'
        }
        
        vertex_model_name = vertex_model_map.get(model_name, 'gemini-2.5-flash')
        print(f"  📦 Cloud Agent Model: {vertex_model_name}")
        
        return VertexGenerativeModel(vertex_model_name)
    
    def _delegate_to_consumer_api(self, model_name: str):
        """
        Delegate to consumer API (fallback).
        
        Args:
            model_name: Name of the model to use
            
        Returns:
            GenerativeModel instance
        """
        if not GENAI_AVAILABLE:
            raise ImportError("Google Generative AI package not installed")
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set for consumer API")
        
        genai.configure(api_key=self.api_key)
        print(f"  🔑 Using Consumer API (fallback) with model: {model_name}")
        
        return genai.GenerativeModel(model_name)
    
    def get_delegation_info(self) -> dict:
        """
        Get information about the current cloud agent delegation.
        
        Returns:
            Dictionary with delegation information
        """
        return {
            'using_cloud_agent': self.use_vertex,
            'cloud_provider': 'Google Cloud Vertex AI' if self.use_vertex else 'Consumer API',
            'project_id': self.project_id if self.use_vertex else None,
            'location': self.location if self.use_vertex else None,
            'initialized': self._initialized
        }


# Global cloud agent delegate instance
_cloud_agent = None


def get_cloud_agent() -> CloudAgentDelegate:
    """
    Get the global cloud agent delegate instance.
    
    Returns:
        CloudAgentDelegate instance
    """
    global _cloud_agent
    if _cloud_agent is None:
        _cloud_agent = CloudAgentDelegate()
    return _cloud_agent


def delegate_to_cloud_agent(model_name: str = GEMINI_MODEL):
    """
    Convenience function to delegate model creation to cloud agent.
    
    Args:
        model_name: Name of the model to use
        
    Returns:
        An initialized AI model instance
    """
    agent = get_cloud_agent()
    return agent.get_model(model_name)
