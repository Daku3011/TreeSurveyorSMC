"""
AI Tree Analysis Service
Supports:
1. OpenRouter API (OpenAI-compatible multi-provider: Gemini, GPT-4o-mini, Claude, Llama Vision)
2. Google Gemini Direct API
"""
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

import os
import json
import re
import base64
import mimetypes
import requests


PROMPT = """You are an expert botanist and arborist specializing in Indian tree species, 
especially those found in Gujarat and the Surat region.

Analyze this tree image and provide a detailed assessment. Return your analysis as a JSON object 
with EXACTLY these keys (no markdown, no code fences, just raw JSON):

{
    "common_name_english": "English common name of the tree species",
    "common_name_gujarati": "Gujarati name (in Gujarati script like આંબો, વડ, પીપળ, નીમ etc.)",
    "botanical_name": "Scientific/botanical name in italicized Latin format",
    "family": "Botanical family name",
    "health_condition": "One of: Excellent, Good, Fair, Poor, Dead",
    "estimated_age": 25,
    "growth_stage": "One of: Sapling, Young, Mature, Old",
    "description": "A detailed 2-3 sentence description of the tree including its visual characteristics, canopy shape, bark texture, and any notable features visible in the image.",
    "confidence": "One of: High, Medium, Low - your confidence in the species identification",
    "ecological_notes": "Brief ecological significance - native/exotic status, wildlife value, carbon sequestration potential"
}

IMPORTANT:
- If you cannot identify the exact species, provide your best guess and set confidence to "Low"
- estimated_age should be an integer (years) or null if impossible to estimate
- For Gujarati name, use Gujarati script (e.g., આંબો for Mango, વડ for Banyan, લીમડો for Neem)
- Focus on tree species commonly found in Gujarat/Western India
- Return ONLY the JSON object, no other text"""


def encode_image(image_path):
    """Encode an image file to base64 with MIME type."""
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type or not mime_type.startswith('image/'):
        mime_type = 'image/jpeg'
    with open(image_path, 'rb') as f:
        b64_data = base64.b64encode(f.read()).decode('utf-8')
    return mime_type, b64_data


def parse_and_validate_ai_json(result_text):
    """Clean markdown code fences and validate JSON schema."""
    result_text = result_text.strip()
    if result_text.startswith('```'):
        result_text = re.sub(r'^```(?:json)?\s*', '', result_text)
        result_text = re.sub(r'\s*```$', '', result_text)
    
    result = json.loads(result_text)
    
    valid_health = ['Excellent', 'Good', 'Fair', 'Poor', 'Dead']
    if result.get('health_condition') not in valid_health:
        result['health_condition'] = 'Good'
    
    valid_stages = ['Sapling', 'Young', 'Mature', 'Old']
    if result.get('growth_stage') not in valid_stages:
        result['growth_stage'] = 'Mature'
    
    valid_confidence = ['High', 'Medium', 'Low']
    if result.get('confidence') not in valid_confidence:
        result['confidence'] = 'Medium'
    
    age = result.get('estimated_age')
    if age is not None:
        try:
            result['estimated_age'] = int(age)
        except (ValueError, TypeError):
            result['estimated_age'] = None
            
    return result


def analyze_with_openrouter(image_path, api_key, model=None):
    """Analyze image using OpenRouter vision models."""
    model = model or os.environ.get('OPENROUTER_MODEL', 'google/gemini-2.5-flash')
    mime_type, b64_data = encode_image(image_path)
    
    headers = {
        'Authorization': f'Bearer {api_key.strip()}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'http://localhost:5000',
        'X-Title': 'SMC Tree Census'
    }
    
    payload = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': PROMPT},
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:{mime_type};base64,{b64_data}'
                        }
                    }
                ]
            }
        ]
    }
    
    response = requests.post(
        'https://openrouter.ai/api/v1/chat/completions',
        headers=headers,
        json=payload,
        timeout=60
    )
    
    if response.status_code != 200:
        error_detail = response.text
        try:
            err_json = response.json()
            if 'error' in err_json:
                error_detail = err_json['error'].get('message', error_detail)
        except:
            pass
        return {
            'success': False,
            'error': f'OpenRouter API error ({response.status_code}): {error_detail}'
        }
        
    res_data = response.json()
    choices = res_data.get('choices', [])
    if not choices:
        return {'success': False, 'error': 'OpenRouter returned empty choices'}
        
    content = choices[0].get('message', {}).get('content', '')
    parsed = parse_and_validate_ai_json(content)
    return {'success': True, 'data': parsed}


def analyze_with_gemini(image_path, api_key):
    """Analyze image using direct Google Gemini SDK."""
    import google.generativeai as genai
    from PIL import Image
    
    genai.configure(api_key=api_key.strip())
    candidate_models = ['gemini-3.6-flash', 'gemini-2.5-flash', 'gemini-1.5-flash']
    img = Image.open(image_path)
    
    last_error = None
    response = None
    
    for model_name in candidate_models:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content([PROMPT, img])
            if response and response.text:
                break
        except Exception as e:
            last_error = e
            err_str = str(e)
            if "PERMISSION_DENIED" in err_str or "API_KEY_INVALID" in err_str or "denied access" in err_str:
                return {
                    'success': False,
                    'error': 'Gemini API key is invalid or lacks access. Use OpenRouter or generate a new key at https://aistudio.google.com/apikey.'
                }
            continue

    if not response or not hasattr(response, 'text') or not response.text:
        return {
            'success': False,
            'error': f'Gemini analysis failed: {str(last_error) if last_error else "No response"}'
        }

    parsed = parse_and_validate_ai_json(response.text)
    return {'success': True, 'data': parsed}


def analyze_tree_image(image_path):
    """
    Analyze tree image automatically using either:
    1. OpenRouter (if OPENROUTER_API_KEY is configured)
    2. Google Gemini Direct (if GEMINI_API_KEY is configured)
    """
    openrouter_key = os.environ.get('OPENROUTER_API_KEY')
    gemini_key = os.environ.get('GEMINI_API_KEY')
    
    # Check OpenRouter first
    if openrouter_key and openrouter_key.strip() and openrouter_key.strip() != 'your_openrouter_api_key_here':
        try:
            return analyze_with_openrouter(image_path, openrouter_key)
        except Exception as e:
            return {'success': False, 'error': f'OpenRouter processing failed: {str(e)}'}
            
    # Fallback to direct Gemini
    if gemini_key and gemini_key.strip() and gemini_key.strip() != 'your_gemini_api_key_here':
        try:
            return analyze_with_gemini(image_path, gemini_key)
        except Exception as e:
            return {'success': False, 'error': f'Gemini processing failed: {str(e)}'}
            
    return {
        'success': False,
        'error': 'No AI API Key found. Please add OPENROUTER_API_KEY or GEMINI_API_KEY to your .env file.'
    }
