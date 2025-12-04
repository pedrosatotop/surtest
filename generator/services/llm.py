"""
LLM service for generating campaign briefs using OpenAI.
"""
import time
import json
from typing import Dict, Any, Optional, Tuple
from openai import OpenAI
from django.conf import settings


class LLMService:
    """Service for interacting with OpenAI API with guardrails."""
    
    # Allowed values for validation
    ALLOWED_PLATFORMS = ["Instagram", "TikTok", "UGC"]
    ALLOWED_GOALS = ["Awareness", "Conversions", "Content Assets"]
    ALLOWED_TONES = ["Professional", "Friendly", "Playful"]
    
    # Profanity filter - basic list (in production, use a proper library)
    PROFANITY_WORDS = {
        # Add common profanity words here - keeping minimal for demo
    }
    
    def __init__(self):
        """Initialize OpenAI client."""
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in environment variables")
        self.client = OpenAI(api_key=api_key)
    
    def validate_inputs(self, brand_name: str, platform: str, goal: str, tone: str) -> Tuple[bool, Optional[str]]:
        """
        Validate all inputs with allowlist and profanity checks.
        
        Returns:
            (is_valid, error_message)
        """
        # Check brand name
        if not brand_name or not brand_name.strip():
            return False, "Brand name is required"
        
        brand_name_clean = brand_name.strip()
        if len(brand_name_clean) < 2:
            return False, "Brand name must be at least 2 characters"
        if len(brand_name_clean) > 100:
            return False, "Brand name must be less than 100 characters"
        
        # Profanity check on brand name
        brand_lower = brand_name_clean.lower()
        for word in self.PROFANITY_WORDS:
            if word in brand_lower:
                return False, "Brand name contains inappropriate content"
        
        # Allowlist validation for platform
        if platform not in self.ALLOWED_PLATFORMS:
            return False, f"Platform must be one of: {', '.join(self.ALLOWED_PLATFORMS)}"
        
        # Allowlist validation for goal
        if goal not in self.ALLOWED_GOALS:
            return False, f"Goal must be one of: {', '.join(self.ALLOWED_GOALS)}"
        
        # Allowlist validation for tone
        if tone not in self.ALLOWED_TONES:
            return False, f"Tone must be one of: {', '.join(self.ALLOWED_TONES)}"
        
        return True, None
    
    def generate_brief(self, brand_name: str, platform: str, goal: str, tone: str) -> Dict[str, Any]:
        """
        Generate campaign brief using OpenAI with structured output.
        
        Returns:
            Dictionary with brief, angles, criteria, and telemetry
        """
        start_time = time.time()
        
        # System prompt - concise and deterministic
        system_prompt = """You are an expert marketing strategist specializing in creator campaigns. 
Generate concise, actionable campaign briefs. Always return exactly 3 content angles and 3 creator selection criteria.
Keep briefs to 4-6 sentences. Be specific and platform-appropriate."""
        
        # User prompt - compact and structured
        user_prompt = f"""Generate a campaign brief for {brand_name}.

Platform: {platform}
Goal: {goal}
Tone: {tone}

Return a JSON object with:
- "brief": A 4-6 sentence campaign brief
- "angles": Array of exactly 3 content angle suggestions
- "criteria": Array of exactly 3 creator selection criteria bullets"""
        
        try:
            # Call OpenAI with JSON schema for deterministic output
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using mini for cost efficiency
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},  # Force JSON output
                temperature=0.4,  # Low temperature for consistency (<= 0.5 as required)
                max_tokens=600,  # Limit tokens for cost control
                timeout=30  # Prevent hanging
            )
            
            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Validate structure
            if "brief" not in result or "angles" not in result or "criteria" not in result:
                raise ValueError("Invalid response structure from LLM")
            
            # Ensure arrays have exactly 3 items
            if not isinstance(result["angles"], list) or len(result["angles"]) != 3:
                raise ValueError("Angles must be an array of exactly 3 items")
            
            if not isinstance(result["criteria"], list) or len(result["criteria"]) != 3:
                raise ValueError("Criteria must be an array of exactly 3 items")
            
            # Calculate telemetry
            latency_ms = (time.time() - start_time) * 1000
            tokens_used = response.usage.total_tokens
            tokens_prompt = response.usage.prompt_tokens
            tokens_completion = response.usage.completion_tokens
            
            return {
                "brief": result["brief"],
                "angles": result["angles"],
                "criteria": result["criteria"],
                "telemetry": {
                    "latency_ms": round(latency_ms, 2),
                    "tokens_total": tokens_used,
                    "tokens_prompt": tokens_prompt,
                    "tokens_completion": tokens_completion,
                    "estimated_cost_usd": round((tokens_prompt * 0.15 + tokens_completion * 0.60) / 1_000_000, 6)  # Approximate cost for gpt-4o-mini
                }
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"LLM service error: {str(e)}")

