# --- LUMI AGENTIC ENGINE (MVP V1) ---
# This code is hosted on Render and called by Voiceflow.

import json
import requests
from flask import Flask, request, jsonify, render_template_string # render_template_string is needed for the dashboard route
from typing import Dict, List, Any, Optional

# --- CONFIGURATION (UPDATED WITH YOUR CONFIRMED KEYS) ---
SUPABASE_URL = "https://lvhsgwnzubjrjqsqbrgh.supabase.co" 
SUPABASE_API_KEY = "sb_publishable_QstVjaJTgplUb-Z_cO_lbA_jw3gvnJz" 
SUPABASE_TABLE = "protocols" 
# FIX 1: Change to the live Render domain to fix the broken link
DASHBOARD_BASE_URL = "https://lumi-agent-engine.onrender.com/protocol" 

# --- FLASK APP INITIALIZATION ---
app = Flask(__name__)

# --- DATABASE FUNCTION (Blueprint 8: Data Persistence) ---
def save_to_supabase(user_id: str, protocol_data: Dict[str, Any], raw_inputs: Dict[str, Any]) -> bool:
    """Handles the POST request to save the protocol data to Supabase."""
    
    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "user_id": user_id,
        "protocol_data": protocol_data, 
        "raw_inputs": raw_inputs      
    }
    
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}",
            headers=headers,
            json=payload
        )
        response.raise_for_status() 
        print(f"Successfully saved protocol for user: {user_id}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error saving to Supabase for user {user_id}: {e}")
        return False

# --- NEW: MOCK AGENTIC PARSING LAYER (To handle single text input from Voiceflow) ---
def parse_single_text_input(full_text: str, goals: str) -> Dict[str, Any]:
    """
    MOCK function to simulate an LLM call that parses the single, long text input 
    from Voiceflow into the structured dictionary needed by the supplement engine.
    
    NOTE: This logic is a simplified heuristic placeholder. In production, 
    this must be replaced by a dedicated LLM call with a structured output (e.g., using Pydantic).
    """
    full_text_lower = full_text.lower()

    parsed_data = {
        'symptoms': [],
        'medications': [],
        'conditions': [],
        'menopause_stage': 'perimenopause', # Default
        'lifestyle': {},
        'goals': goals.split(',')
    }

    # Symptom Parsing (Heuristic based on your previous examples)
    if 'bloating' in full_text_lower or 'gas' in full_text_lower:
        parsed_data['symptoms'].append({'name': 'Bloating'})
    if 'hair loss' in full_text_lower or 'thinning' in full_text_lower:
        parsed_data['symptoms'].append({'name': 'Hair Loss'})
    if 'hot flash' in full_text_lower or 'night sweat' in full_text_lower:
        parsed_data['symptoms'].append({'name': 'Hot Flashes'})
    if 'anxiety' in full_text_lower or 'stress' in full_text_lower:
        parsed_data['symptoms'].append({'name': 'Anxiety'})

    # Clinical/Stage Parsing
    if 'post-menopause' in full_text_lower or 'post menopause' in full_text_lower:
        parsed_data['menopause_stage'] = 'post-menopause'
    elif 'pre-menopause' in full_text_lower or 'pre menopause' in full_text_lower:
        parsed_data['menopause_stage'] = 'pre-menopause'
    
    # Lifestyle Parsing
    if 'poor sleep' in full_text_lower or 'bad sleep' in full_text_lower:
        parsed_data['lifestyle']['sleep_quality'] = 'Poor'
    elif 'good sleep' in full_text_lower or 'sleep ok' in full_text_lower:
        parsed_data['lifestyle']['sleep_quality'] = 'Good'
    else:
        parsed_data['lifestyle']['sleep_quality'] = 'Fair'

    # Stress Parsing (Simple heuristic)
    if 'high stress' in full_text_lower or 'very stressed' in full_text_lower:
        parsed_data['lifestyle']['stress_level'] = 9
    elif 'medium stress' in full_text_lower or 'bit stressed' in full_text_lower:
        parsed_data['lifestyle']['stress_level'] = 6
    else:
        parsed_data['lifestyle']['stress_level'] = 3
        
    return parsed_data

# --- CORE LOGIC: SUPPLEMENT ENGINE (Blueprints 2, 3, 4, A, B, C) ---
def get_lumi_supplement_stack(user_data: Dict[str, Any]) ->
