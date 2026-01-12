from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time

class BaseProvider(ABC):
    """
    Abstract base class for all LLM providers.
    Defines the interface that all providers must implement.
    """
    
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        self.provider_name = self.__class__.__name__
    
    @abstractmethod
    async def query(self, prompt: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Query the provider with a prompt.
        
        Returns:
            {
                "status": "success" | "error",
                "response_text": str,
                "response_time_ms": float,
                "token_count": int,
                "error_message": str (if error),
                "sources": list (if available),
                "model_used": str,
                "provider": str
            }
        """
        pass
    
    @abstractmethod
    async def validate_key(self) -> bool:
        """
        Validate that the API key is valid.
        """
        pass
    
    def format_response(self, response_text: str, response_time_ms: float, 
                       token_count: int = None, sources: list = None) -> Dict[str, Any]:
        """
        Format a successful response in the standard format.
        """
        if token_count is None:
            token_count = len(response_text.split())
        
        return {
            "status": "success",
            "response_text": response_text[:5000],  # Truncate for DB
            "response_time_ms": response_time_ms,
            "token_count": token_count,
            "sources": sources or [],
            "model_used": self.model_name,
            "provider": self.provider_name,
        }
    
    def format_error(
        self,
        error_message: str,
        response_time_ms: float,
        error_type: str = "unknown",
        retry_after_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Format an error response in the standard format.
        """
        return {
            "status": "error",
            "error_type": error_type,
            "error_message": error_message[:500],
            "retry_after_ms": retry_after_ms,
            "response_time_ms": response_time_ms,
            "model_used": self.model_name,
            "provider": self.provider_name,
        }
