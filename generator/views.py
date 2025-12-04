"""
Views for the AI Brief Generator.
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from .services.llm import LLMService
from .services.rate_limiter import rate_limiter


def get_client_ip(request):
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def index(request):
    """Render the main page."""
    return render(request, 'generator/index.html')


@csrf_exempt
@require_http_methods(["POST"])
def generate_brief(request):
    """
    API endpoint to generate campaign brief.
    
    Expected JSON payload:
    {
        "brand_name": "string",
        "platform": "Instagram" | "TikTok" | "UGC",
        "goal": "Awareness" | "Conversions" | "Content Assets",
        "tone": "Professional" | "Friendly" | "Playful"
    }
    
    Returns JSON response with brief, angles, criteria, and telemetry.
    """
    # Rate limiting
    client_ip = get_client_ip(request)
    if not rate_limiter.is_allowed(client_ip):
        return JsonResponse({
            "error": "Rate limit exceeded. Please try again later.",
            "remaining": 0
        }, status=429)
    
    # Parse request body
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON in request body"
        }, status=400)
    
    # Extract inputs
    brand_name = data.get('brand_name', '').strip()
    platform = data.get('platform', '').strip()
    goal = data.get('goal', '').strip()
    tone = data.get('tone', '').strip()

    print(brand_name, platform, goal, tone)
    
    # Validate inputs using LLM service
    llm_service = LLMService()
    is_valid, error_message = llm_service.validate_inputs(
        brand_name, platform, goal, tone
    )
    
    if not is_valid:
        return JsonResponse({
            "error": error_message
        }, status=400)
    
    # Generate brief
    try:
        result = llm_service.generate_brief(brand_name, platform, goal, tone)
        
        # Add rate limit info
        result["rate_limit"] = {
            "remaining": rate_limiter.get_remaining(client_ip)
        }
        
        return JsonResponse(result, status=200)
        
    except ValueError as e:
        return JsonResponse({
            "error": f"Validation error: {str(e)}"
        }, status=400)
    except RuntimeError as e:
        return JsonResponse({
            "error": f"Service error: {str(e)}"
        }, status=500)
    except Exception as e:
        return JsonResponse({
            "error": f"Unexpected error: {str(e)}"
        }, status=500)

