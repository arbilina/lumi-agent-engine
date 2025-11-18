# --- LUMI AGENTIC ENGINE (MVP V1) ---
# This code is hosted on Render and called by Voiceflow.

import json
import requests
from flask import Flask, request, jsonify, render_template_string # render_template_string is needed for the dashboard/test routes
from typing import Dict, List, Any, Optional
import traceback # Used for detailed error logging

# --- CONFIGURATION (UPDATED WITH YOUR CONFIRMED KEYS) ---
SUPABASE_URL = "https://lvhsgwnzubjrjqsqbrgh.supabase.co" 
SUPABASE_API_KEY = "sb_publishable_QstVjaJTgplUb-Z_cO_lbA_jw3gvnJz" 
SUPABASE_TABLE = "protocols" 
DASHBOARD_BASE_URL = "https://lumi-agent-engine.onrender.com/protocol" 

# --- FLASK APP INITIALIZATION ---
app = Flask(__name__)

# -------------------------------------------------------------------------
# --- API ENDPOINTS (TEST & UTILITY) ---
# -------------------------------------------------------------------------

@app.route('/')
def welcome_message():
    """Welcome message for a quick health check of the API deployment."""
    # This is the message the user should see if they hit the URL directly.
    return "Hello, I'm Lumi's Agentic Backend! The API is running correctly."

@app.route('/file-upload-test', methods=['POST'])
def file_upload_test():
    """
    Placeholder endpoint to confirm Voiceflow file upload mechanism is working.
    """
    try:
        data = request.json
        if data and 'file_url' in data:
            return jsonify({
                "status": "success",
                "message": "File upload confirmed! Data received from Voiceflow.",
                "received_file": data.get('file_name', 'N/A')
            }), 200
        else:
            return jsonify({
                "status": "warning",
                "message": "File upload test received data, but key fields were missing. Expected: file_url, file_name.",
                "received_data": data
            }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred during file upload test: {str(e)}",
        }), 500

# -------------------------------------------------------------------------
# --- CORE FUNCTIONS ---
# -------------------------------------------------------------------------

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

# --- NEW: MOCK AGENTIC PARSING LAYER ---
def parse_single_text_input(full_text: str, goals: str) -> Dict[str, Any]:
    """MOCK function to parse single text input into structured data."""
    
    full_text_lower = full_text.lower()

    parsed_data = {
        'symptoms': [],
        'medications': [],
        'conditions': [],
        'menopause_stage': 'perimenopause', # Default
        'lifestyle': {},
        'goals': [g.strip() for g in goals.split(',') if g.strip()]
    }

    # Symptom Parsing
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

    # Stress Parsing (Robustness Fix: Default stress level is 5 - Neutral)
    if 'high stress' in full_text_lower or 'very stressed' in full_text_lower:
        parsed_data['lifestyle']['stress_level'] = 9
    elif 'medium stress' in full_text_lower or 'bit stressed' in full_text_lower:
        parsed_data['lifestyle']['stress_level'] = 6
    else:
        parsed_data['lifestyle']['stress_level'] = 5 
        
    return parsed_data

# --- CORE LOGIC: SUPPLEMENT ENGINE (Blueprints 2, 3, 4, A, B, C) ---
def get_lumi_supplement_stack(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Runs the full agentic logic to generate a safe, personalised supplement stack."""

    # --- 0. EXTRACT & NORMALIZE INPUTS ---
    user_id = user_data.get('user_id', 'anon_user')
    
    symptoms = user_data.get('symptoms', [])  
    meds = user_data.get('medications', [])
    conditions = user_data.get('conditions', [])
    menopause_stage = user_data.get('menopause_stage', 'perimenopause').lower()
    
    # Lifestyle Inputs
    lifestyle = user_data.get('lifestyle', {})
    sleep_quality = lifestyle.get('sleep_quality', 'Fair') 
    stress_level = int(lifestyle.get('stress_level', 5)) 
    diet_notes = user_data.get('diet_notes', '').lower() 
    movement = user_data.get('movement', 'sedentary').lower() 
    
    raw_inputs = {
        "user_id": user_id,
        "symptoms": symptoms,
        "medications": meds,
        "conditions": conditions,
        "menopause_stage": menopause_stage,
        "lifestyle": lifestyle,
        "goals": user_data.get('goals', [])
    }

    # --- 1. INITIALIZE OUTPUT & SAFETY CHECKS (Blueprint 4/C) ---
    stack: Dict[str, Dict[str, Any]] = {} 
    warnings: List[str] = []
    
    # Safety Checks 
    meds_lower = [m.lower() for m in meds]
    conditions_lower = [c.lower() for c in conditions]
    
    if any(m in meds_lower for m in ['ssri', 'antidepressant', 'zoloft', 'prozac']):
        warnings.append("RISK: St. John's Wort is contraindicated with SSRIs and has been excluded.")
    if any('thyroid' in m for m in meds_lower):
        warnings.append("RISK: Ashwagandha is flagged due to potential interaction with thyroid medication. A replacement will be chosen.")
    if any(c in conditions_lower for c in ['liver disorder', 'liver disease']):
        warnings.append("RISK: Black Cohosh is avoided due to history of liver disorder.")
    if any(c in conditions_lower for c in ['estrogen-sensitive', 'breast cancer']):
        warnings.append("RISK: Phytoestrogens (like Soy, Red Clover) are avoided due to your medical history.")
    
    if conditions_lower:
        if not any(c in conditions_lower for c in ['iron deficiency', 'anemia']):
            warnings.append("NOTE: Iron is not recommended unless a deficiency is confirmed. Low energy will be supported with B-Vitamins and Magnesium.")

    # --- 2. SYMPTOM CLUSTER MATCHING (Blueprint 2/A) ---
    symptom_names = [s['name'].lower() for s in symptoms] 

    # Core Ingredients
    stack['Omega-3'] = {'rationale': 'Core anti-inflammatory and brain support.', 'dose': '2000mg EPA/DHA', 'cluster': 'Core'}
    stack['Magnesium Glycinate'] = {'rationale': 'Essential for over 300 bodily processes, including muscle relaxation, nerve function, and energy.', 'dose': '300mg', 'cluster': 'Core'}

    if any(s in symptom_names for s in ['brain fog', 'fatigue', 'low energy']):
        stack['B-Complex'] = {'rationale': 'Supports cellular energy production and cognitive clarity.', 'dose': 'High-strength B50 or B100', 'cluster': 'Energy'}

    if any(s in symptom_names for s in ['hot flashes', 'night sweats']):
        if "RISK: Black Cohosh" not in warnings:
            stack['Black Cohosh'] = {'rationale': 'Evidence-backed support for reducing vasomotor symptoms (hot flashes).', 'dose': '40mg', 'cluster': 'Hormone'}
        elif "RISK: Phytoestrogens" not in warnings:
            stack['Phytoestrogens (Red Clover)'] = {'rationALE': 'Alternative support for hot flashes.', 'dose': '40-80mg', 'cluster': 'Hormone'}
        stack['Vitamin E'] = {'rationale': 'May help reduce the severity of hot flashes.', 'dose': '400 IU', 'cluster': 'Hormone'}

    if any(s in symptom_names for s in ['anxiety', 'stress', 'overwhelm']):
        stack['L-Theanine'] = {'rationale': 'Promotes a calm, alert state without drowsiness.', 'dose': '200mg', 'cluster': 'Stress'}
        if "RISK: Ashwagandha" not in warnings:
            stack['Ashwagandha'] = {'rationale': 'Adaptogen to help the body manage cortisol and stress response.', 'dose': '300-500mg', 'cluster': 'Stress'}

    if any(s in symptom_names for s in ['bloating', 'gas', 'indigestion']):
        stack['Probiotic'] = {'rationale': 'Supports gut microbiome balance, which is key for digestion and reducing bloat.', 'dose': '20-50 Billion CFU', 'cluster': 'Gut'}
        stack['Digestive Enzymes'] = {'rationale': 'Assists with the breakdown of food to reduce indigestion and gas.', 'dose': '1 capsule with meals', 'cluster': 'Gut'}

    if any(s in symptom_names for s in ['hair loss', 'dry skin', 'brittle nails']):
        stack['Collagen'] = {'rationale': 'Provides key amino acids for hair, skin, and nail structure.', 'dose': '10-15g', 'cluster': 'Skin'}
        stack['Biotin'] = {'rationale': 'Supports keratin infrastructure, a key component of hair and nails.', 'dose': '5,000mcg', 'cluster': 'Skin'}
        stack['Vitamin C'] = {'rationale': 'Essential for collagen synthesis.', 'dose': '500-1000mg', 'cluster': 'Skin'}

    
    # --- 3. BEHAVIOUR-DRIVEN REFINEMENT (Blueprint 3/B) ---
    if sleep_quality == 'Poor':
        if 'L-Theanine' not in stack:
            stack['L-Theanine'] = {'rationale': 'Added to support sleep onset and quality due to poor sleep score.', 'dose': '200mg', 'cluster': 'Sleep'}
        if 'Magnesium Glycinate' in stack:
            stack['Magnesium Glycinate']['dose'] = '400mg' 
            stack['Magnesium Glycinate']['rationale'] += " (Dose increased to 400mg to support sleep quality.)"

    if stress_level >= 8:
        if 'Ashwagandha' not in stack and "RISK: Ashwagandha" not in warnings:
            stack['Ashwagandha'] = {'rationale': 'Added due to high reported stress level (8+).', 'dose': '300-500mg', 'cluster': 'Stress'}

    if 'low protein' in diet_notes and 'Collagen' not in stack:
        stack['Collagen'] = {'rationale': 'Added to supplement dietary protein intake for tissue repair.', 'dose': '10-15g', 'cluster': 'Skin'}

    if 'high sugar' in diet_notes:
        stack['Chromium'] = {'rationale': 'Helps support healthy blood sugar patterns.', 'dose': '200mcg', 'cluster': 'Metabolic'}

    if movement == 'weight_training':
        stack['Creatine'] = {'rationale': 'Supports muscle mass, strength, and cognitive function, especially beneficial during menopause.', 'dose': '5g', 'cluster': 'Movement'}

    # --- 4. FORMAT OUTPUT WITH LINKS (Blueprint D) ---
    brand_mapping = {
        'Magnesium Glycinate': {'product': 'Solgar Magnesium Glycinate', 'retailer': 'iHerb', 'link': 'https://www.iherb.com/r/solgar-magnesium-glycinate-90-vegetable-capsules-120-mg-per-capsule/150654'},
        'Black Cohosh': {'product': 'Holland & Barrett MenoCool Black Cohosh', 'retailer': 'Holland & Barrett', 'link': 'https://www.hollandandbarrett.com/shop/product/holland-barrett-menocool-black-cohosh-tablets-60035288'},
        'Omega-3': {'product': 'Solgar Triple Strength Omega-3', 'retailer': 'Holland & Barrett', 'link': 'https://www.hollandandbarrett.com/shop/product/solgar-triple-strength-omega-3-100-softgels-6100007208'},
        'L-Theanine': {'product': 'Solgar L-Theanine 200mg', 'retailer': 'iHerb', 'link': 'https://www.iherb.com/pr/solgar-l-theanine-200-mg-60-softgels/70362'},
        'B-Complex': {'product': 'Solgar B-Complex "50"', 'retailer': 'iHerb', 'link': 'https://www.iherb.com/pr/solgar-b-complex-50-vegetable-capsules/108987'},
        'Collagen': {'product': 'Vital Proteins Collagen Peptides', 'retailer': 'Amazon', 'link': 'https://www.amazon.co.uk/Vital-Proteins-Collagen-Peptides-Unflavored/dp/B00NLR1PX0'},
        'Creatine': {'product': 'Solgar Creatine Powder', 'retailer': 'Amazon', 'link': 'https://www.amazon.co.uk/Solgar-Creatine-Powder-3000-120/dp/B000Z9139G'}
    }

    final_stack_list: List[Dict[str, Any]] = []
    for name, details in stack.items():
        example = brand_mapping.get(name, {})
        final_stack_list.append({
            'supplement': name,
            'rationale': details['rationale'],
            'dose': details['dose'],
            'cluster': details['cluster'],
            'example_product': f"{example.get('product', f'A quality brand {name}')}",
            'link': example.get('link', 'SEARCH_REQUIRED')
        })
    
    # Robustness Fix: Determine if we used defaults for the summary
    if sleep_quality == 'Fair' and stress_level == 5:
        refinement_detail = "refined using a foundational approach for balanced hormone support."
    else:
        refinement_detail = f"refined based on your **{sleep_quality}** sleep and **{stress_level}/10** stress level."


    final_recommendation = {
        "full_stack": final_stack_list,
        # Use the new detail variable in the summary:
        "rationale_summary": f"Your plan was built using evidence-backed clusters, targeting your key symptoms and {refinement_detail}",
        "daily_plan": [
            f"**Morning (with breakfast):** {', '.join([s['supplement'] for s in final_stack_list if s['cluster'] in ['Energy', 'Gut', 'Skin', 'Metabolic', 'Movement']])}.", 
            f"**Evening (60 min before bed):** {', '.join([s['supplement'] for s in final_stack_list if s['cluster'] in ['Core', 'Sleep', 'Hormone', 'Stress']])}."
        ],
        "expected_benefit_timeline": "You may feel improvements in sleep and energy within 1-2 weeks. Hormonal, skin, and hair changes often take 6-12 weeks of consistent use.",
        "what_will_be_monitored": ["Symptom Intensity/Frequency", "Sleep Quality Score", "Stress Level"],
        "adjustments_plan": "We will perform a formal check-in in 7 days to monitor for side effects and adherence, and again at 30 days to assess improvements and modify your stack. (Blueprint 5)",
        "warnings": warnings,
    }
    
    # --- 5. DATA PERSISTENCE ---
    save_successful = save_to_supabase(user_id, final_recommendation, raw_inputs)
    
    # --- 6. FINAL OUTPUT FOR VOICEFLOW ---
    final_recommendation['db_save_status'] = 'SUCCESS' if save_successful else 'FAILED'
    final_recommendation['user_id'] = user_id
    final_recommendation['dashboard_url'] = f"{DASHBOARD_BASE_URL}/{user_id}"
    
    return final_recommendation

# -------------------------------------------------------------------------
# --- API ENDPOINT (Voiceflow Call) ---
# -------------------------------------------------------------------------

@app.route('/api/get-protocol', methods=['POST'])
def handle_get_protocol():
    voiceflow_input = {}
    
    try:
        voiceflow_input = request.json
        
        if not voiceflow_input or 'user_id' not in voiceflow_input or 'full_intake_text' not in voiceflow_input:
            return jsonify({"error": "Missing required data: user_id and full_intake_text are required from Voiceflow."}), 400

        user_id = voiceflow_input.get('user_id', 'anon_user')
        full_text = voiceflow_input.get('full_intake_text', '')
        goals_text = voiceflow_input.get('goals_text', '')
        
        parsed_data = parse_single_text_input(full_text, goals_text)
        
        protocol_input = {
            'user_id': user_id,
            'test_data': voiceflow_input.get('test_data', ''), 
            **parsed_data 
        }

        protocol = get_lumi_supplement_stack(protocol_input)
        # This returns the complete protocol data to Voiceflow for presentation to the user
        return jsonify(protocol), 200
            
    except Exception as e:
        user_id = voiceflow_input.get('user_id', 'unknown_user')
        print(f"Error in /api/get-protocol for user {user_id}: {traceback.format_exc()}")
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500


# --- MVP DASHBOARD PLACEHOLDER ROUTE (For a working link) ---
@app.route('/protocol/<user_id>', methods=['GET'])
def protocol_placeholder(user_id):
    """A simple placeholder page to confirm the Dashboard link works."""
    
    html_content = f"""
    <html>
        <head><title>Lumi Protocol Dashboard</title></head>
        <body style="font-family: sans-serif; padding: 20px;">
            <h1>Lumi Protocol for User ID: {user_id}</h1>
            <p style="color: green; font-weight: bold;">✅ Success! Your data has been securely saved.</p>
            <p>The full personalized dashboard experience is part of the V1 roadmap (H1 2025).</p>
            <p>For now, you can view the complete recommendations directly in the chat window.</p>
        </body>
    </html>
    """
    return render_template_string(html_content)

# --- Standard Flask entry point ---
if __name__ == '__main__':
    # NOTE: Render uses gunicorn, this is for local testing only
    app.run(debug=True, port=5001)
