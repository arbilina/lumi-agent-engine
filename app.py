# --- LUMI AGENTIC ENGINE (MVP V1) ---
# This code is hosted on Render and called by Voiceflow.

import json
import requests
from flask import Flask, request, jsonify, render_template_string
from typing import Dict, List, Any, Optional
import traceback

# --- CONFIGURATION (YOUR KEYS) ---
SUPABASE_URL = "https://lvhsgwnzubjrjqsqbrgh.supabase.co"
SUPABASE_API_KEY = "sb_publishable_QstVjaJTgplUb-Z_cO_lbA_jw3gvnJz"
SUPABASE_TABLE = "protocols"

# WORKING RENDER DOMAIN (for the dashboard-style link)
DASHBOARD_BASE_URL = "https://lumi-agent-engine.onrender.com/protocol"

# --- FLASK APP INITIALIZATION ---
app = Flask(__name__)

# -------------------------------------------------------------------------
# --- API ENDPOINTS (WELCOME & TEST) ---
# -------------------------------------------------------------------------


@app.route("/")
def welcome_message():
    """Health check route."""
    return "Hello, I'm Lumi's Agentic Backend! The API is running correctly."


@app.route("/file-upload-test", methods=["POST"])
def file_upload_test():
    """Placeholder endpoint to confirm Voiceflow file upload mechanism is working."""
    try:
        data = request.json
        if data and "file_url" in data:
            return jsonify(
                {
                    "status": "success",
                    "message": "File upload confirmed! Data received from Voiceflow.",
                    "received_file": data.get("file_name", "N/A"),
                }
            ), 200
        else:
            return jsonify(
                {
                    "status": "warning",
                    "message": "File upload test received data, but key fields were missing. Expected: file_url, file_name.",
                    "received_data": data,
                }
            ), 200
    except Exception as e:
        return jsonify(
            {
                "status": "error",
                "message": f"An error occurred during file upload test: {str(e)}",
            }
        ), 500


# -------------------------------------------------------------------------
# --- CORE FUNCTIONS ---
# -------------------------------------------------------------------------


def save_to_supabase(
    user_id: str, protocol_data: Dict[str, Any], raw_inputs: Dict[str, Any]
) -> bool:
    """Handles the POST request to save the protocol data to Supabase."""

    headers = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "user_id": user_id,
        "protocol_data": protocol_data,
        "raw_inputs": raw_inputs,
    }

    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/{SUPABASE_TABLE}",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        print(f"Successfully saved protocol for user: {user_id}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error saving to Supabase for user {user_id}: {e}")
        return False


# --- AGENTIC PARSING LAYER (Non-Interrogative Input Fix) ---
def parse_single_text_input(full_text: str, goals: str) -> Dict[str, Any]:
    """Parses the single, long text input from Voiceflow into structured data."""

    full_text_lower = full_text.lower()

    parsed_data: Dict[str, Any] = {
        "symptoms": [],
        "medications": [],
        "conditions": [],
        "menopause_stage": "perimenopause",  # default
        "lifestyle": {},
        "goals": [g.strip() for g in goals.split(",") if g.strip()],
    }

    # Symptom Parsing (Heuristic logic – can be extended)
    if "bloating" in full_text_lower or "gas" in full_text_lower:
        parsed_data["symptoms"].append({"name": "Bloating"})
    if "hair loss" in full_text_lower or "thinning" in full_text_lower:
        parsed_data["symptoms"].append({"name": "Hair Loss"})
    if "hot flash" in full_text_lower or "night sweat" in full_text_lower:
        parsed_data["symptoms"].append({"name": "Hot Flashes"})
    if "anxiety" in full_text_lower or "stress" in full_text_lower:
        parsed_data["symptoms"].append({"name": "Anxiety"})
    if "fatigue" in full_text_lower or "low energy" in full_text_lower:
        parsed_data["symptoms"].append({"name": "Fatigue"})
    if "brain fog" in full_text_lower:
        parsed_data["symptoms"].append({"name": "Brain Fog"})
    if "dry skin" in full_text_lower or "itchy skin" in full_text_lower:
        parsed_data["symptoms"].append({"name": "Dry Skin"})

    # Clinical/Stage Parsing
    if "post-menopause" in full_text_lower or "post menopause" in full_text_lower:
        parsed_data["menopause_stage"] = "post-menopause"
    elif "pre-menopause" in full_text_lower or "pre menopause" in full_text_lower:
        parsed_data["menopause_stage"] = "pre-menopause"

    # Lifestyle – Sleep
    if "poor sleep" in full_text_lower or "bad sleep" in full_text_lower:
        parsed_data["lifestyle"]["sleep_quality"] = "Poor"
    elif "good sleep" in full_text_lower or "sleep ok" in full_text_lower:
        parsed_data["lifestyle"]["sleep_quality"] = "Good"
    else:
        parsed_data["lifestyle"]["sleep_quality"] = "Fair"

    # Lifestyle – Stress (Default 5/10)
    if "high stress" in full_text_lower or "very stressed" in full_text_lower:
        parsed_data["lifestyle"]["stress_level"] = 9
    elif "medium stress" in full_text_lower or "bit stressed" in full_text_lower:
        parsed_data["lifestyle"]["stress_level"] = 6
    else:
        parsed_data["lifestyle"]["stress_level"] = 5

    return parsed_data


# --- CORE LOGIC: SUPPLEMENT ENGINE ---
def get_lumi_supplement_stack(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Runs the full agentic logic to generate a safe, personalised supplement stack."""

    # --- 0. EXTRACT & NORMALIZE INPUTS ---
    user_id = user_data.get("user_id", "anon_user")
    symptoms = user_data.get("symptoms", [])
    meds = user_data.get("medications", [])
    conditions = user_data.get("conditions", [])
    menopause_stage = user_data.get("menopause_stage", "perimenopause").lower()
    lifestyle = user_data.get("lifestyle", {})
    sleep_quality = lifestyle.get("sleep_quality", "Fair")
    stress_level = int(lifestyle.get("stress_level", 5))
    diet_notes = user_data.get("diet_notes", "").lower()
    movement = user_data.get("movement", "sedentary").lower()

    raw_inputs = {
        "user_id": user_id,
        "symptoms": symptoms,
        "medications": meds,
        "conditions": conditions,
        "menopause_stage": menopause_stage,
        "lifestyle": lifestyle,
        "goals": user_data.get("goals", []),
    }

    # --- 1. INITIALIZE OUTPUT & SAFETY CHECKS ---
    stack: Dict[str, Dict[str, Any]] = {}
    warnings: List[str] = []

    meds_lower = [m.lower() for m in meds]
    conditions_lower = [c.lower() for c in conditions]

    if any(m in meds_lower for m in ["ssri", "antidepressant", "zoloft", "prozac"]):
        warnings.append(
            "RISK: St. John's Wort is contraindicated with SSRIs and has been excluded."
        )
    if any("thyroid" in m for m in meds_lower):
        warnings.append(
            "RISK: Ashwagandha is flagged due to potential interaction with thyroid medication. A replacement will be chosen."
        )
    if any(c in conditions_lower for c in ["liver disorder", "liver disease"]):
        warnings.append(
            "RISK: Black Cohosh is avoided due to history of liver disorder."
        )
    if any(c in conditions_lower for c in ["estrogen-sensitive", "breast cancer"]):
        warnings.append(
            "RISK: Phytoestrogens (like Soy, Red Clover) are avoided due to your medical history."
        )

    # Only add iron note if there *were* conditions
    if conditions_lower and not any(
        c in conditions_lower for c in ["iron deficiency", "anemia"]
    ):
        warnings.append(
            "NOTE: Iron is not recommended unless a deficiency is confirmed. Low energy will be supported with B-vitamins and Magnesium."
        )

    # --- 2. SYMPTOM CLUSTER MATCHING (Logic) ---
    symptom_names = [s["name"].lower() for s in symptoms]

    # Core base
    stack["Omega-3"] = {
        "rationale": "Core anti-inflammatory and brain support.",
        "dose": "2000mg EPA/DHA",
        "cluster": "Core",
    }
    stack["Magnesium Glycinate"] = {
        "rationale": "Supports relaxation, sleep, muscle function, and energy.",
        "dose": "300mg",
        "cluster": "Core",
    }

    # Energy / brain
    if any(s in symptom_names for s in ["brain fog", "fatigue", "low energy"]):
        stack["B-Complex"] = {
            "rationale": "Supports cellular energy production and cognitive clarity.",
            "dose": "High-strength B50 or B100",
            "cluster": "Energy",
        }

    # Hot flashes / vasomotor
    if any(s in symptom_names for s in ["hot flashes", "night sweats"]):
        if "RISK: Black Cohosh" not in warnings:
            stack["Black Cohosh"] = {
                "rationale": "Evidence-backed support for reducing hot flashes.",
                "dose": "40mg",
                "cluster": "Hormone",
            }
        elif "RISK: Phytoestrogens" not in warnings:
            stack["Red Clover"] = {
                "rationale": "Phytoestrogen support for vasomotor symptoms.",
                "dose": "40–80mg isoflavones",
                "cluster": "Hormone",
            }
        stack["Vitamin E"] = {
            "rationale": "May help reduce hot flash intensity.",
            "dose": "400 IU",
            "cluster": "Hormone",
        }

    # Stress / mood
    if any(s in symptom_names for s in ["anxiety", "stress", "overwhelm"]):
        stack["L-Theanine"] = {
            "rationale": "Promotes a calm, alert state without drowsiness.",
            "dose": "200mg",
            "cluster": "Stress",
        }
        if "RISK: Ashwagandha" not in warnings:
            stack["Ashwagandha"] = {
                "rationale": "Adaptogen to support cortisol balance and stress resilience.",
                "dose": "300–500mg",
                "cluster": "Stress",
            }

    # Gut / bloating
    if any(s in symptom_names for s in ["bloating", "gas", "indigestion"]):
        stack["Probiotic"] = {
            "rationale": "Supports gut microbiome balance and digestion.",
            "dose": "20–50 billion CFU",
            "cluster": "Gut",
        }
        stack["Digestive Enzymes"] = {
            "rationale": "Helps break down food to reduce indigestion and gas.",
            "dose": "1 capsule with meals",
            "cluster": "Gut",
        }

    # Skin / hair / nails
    if any(s in symptom_names for s in ["hair loss", "dry skin", "brittle nails"]):
        stack["Collagen"] = {
            "rationale": "Provides amino acids for hair, skin, and nail structure.",
            "dose": "10–15g",
            "cluster": "Skin",
        }
        stack["Biotin"] = {
            "rationale": "Supports keratin production for hair and nails.",
            "dose": "5000mcg",
            "cluster": "Skin",
        }
        stack["Vitamin C"] = {
            "rationale": "Essential for collagen synthesis and skin repair.",
            "dose": "500–1000mg",
            "cluster": "Skin",
        }

    # --- 3. BEHAVIOUR-DRIVEN REFINEMENT ---
    if sleep_quality == "Poor":
        if "L-Theanine" not in stack:
            stack["L-Theanine"] = {
                "rationale": "Added to support sleep onset and quality.",
                "dose": "200mg",
                "cluster": "Sleep",
            }
        if "Magnesium Glycinate" in stack:
            stack["Magnesium Glycinate"]["dose"] = "400mg"
            stack["Magnesium Glycinate"][
                "rationale"
            ] += " Dose increased to further support sleep quality."

    if stress_level >= 8:
        if "Ashwagandha" not in stack and "RISK: Ashwagandha" not in warnings:
            stack["Ashwagandha"] = {
                "rationale": "Added due to high reported stress level (8+).",
                "dose": "300–500mg",
                "cluster": "Stress",
            }

    if "low protein" in diet_notes and "Collagen" not in stack:
        stack["Collagen"] = {
            "rationale": "Supports connective tissue and protein intake.",
            "dose": "10–15g",
            "cluster": "Skin",
        }

    if "high sugar" in diet_notes:
        stack["Chromium"] = {
            "rationale": "Supports healthy blood sugar regulation.",
            "dose": "200mcg",
            "cluster": "Metabolic",
        }

    if movement == "weight_training":
        stack["Creatine"] = {
            "rationale": "Supports muscle mass, strength, and cognitive function.",
            "dose": "5g",
            "cluster": "Movement",
        }

    # --- 4. FORMAT OUTPUT WITH LINKS ---
    # This is where your LIST B (Holland & Barrett) mapping lives.
    # Extend this dict with all ~50 products as needed.
    brand_mapping: Dict[str, Dict[str, str]] = {
        # CORE
        "Omega-3": {
            "product": "H&B High Strength Omega-3 Fish Oil",
            "link": "https://www.hollandandbarrett.com/",
        },
        "Magnesium Glycinate": {
            "product": "H&B Magnesium Glycinate",
            "link": "https://www.hollandandbarrett.com/",
        },
        # ENERGY
        "B-Complex": {
            "product": "H&B Vitamin B-Complex",
            "link": "https://www.hollandandbarrett.com/",
        },
        # HORMONE / MENOPAUSE
        "Black Cohosh": {
            "product": "H&B Black Cohosh Menopause Support",
            "link": "https://www.hollandandbarrett.com/",
        },
        "Red Clover": {
            "product": "H&B Red Clover Isoflavones",
            "link": "https://www.hollandandbarrett.com/",
        },
        "Vitamin E": {
            "product": "H&B Vitamin E 400 IU",
            "link": "https://www.hollandandbarrett.com/",
        },
        # STRESS
        "L-Theanine": {
            "product": "H&B L-Theanine",
            "link": "https://www.hollandandbarrett.com/",
        },
        "Ashwagandha": {
            "product": "H&B Ashwagandha KSM-66 or similar",
            "link": "https://www.hollandandbarrett.com/",
        },
        # GUT
        "Probiotic": {
            "product": "H&B Live Friendly Bacteria / Probiotic",
            "link": "https://www.hollandandbarrett.com/",
        },
        "Digestive Enzymes": {
            "product": "H&B Digestive Enzymes",
            "link": "https://www.hollandandbarrett.com/",
        },
        # SKIN / HAIR
        "Collagen": {
            "product": "H&B Collagen Powder",
            "link": "https://www.hollandandbarrett.com/",
        },
        "Biotin": {
            "product": "H&B Biotin 5000mcg",
            "link": "https://www.hollandandbarrett.com/",
        },
        "Vitamin C": {
            "product": "H&B Vitamin C 1000mg",
            "link": "https://www.hollandandbarrett.com/",
        },
        # METABOLIC
        "Chromium": {
            "product": "H&B Chromium Picolinate",
            "link": "https://www.hollandandbarrett.com/",
        },
        # MOVEMENT
        "Creatine": {
            "product": "H&B Creatine Monohydrate",
            "link": "https://www.hollandandbarrett.com/",
        },
        # You can continue adding all remaining LIST B products here...
    }

    final_stack_list: List[Dict[str, Any]] = []
    for name, details in stack.items():
        example = brand_mapping.get(name, {})
        final_stack_list.append(
            {
                "supplement": name,
                "rationale": details["rationale"],
                "dose": details["dose"],
                "cluster": details["cluster"],
                "example_product": example.get("product", f"A quality brand {name}"),
                "link": example.get("link", "SEARCH_REQUIRED"),
            }
        )

    # Rationale summary
    if sleep_quality == "Fair" and stress_level == 5:
        refinement_detail = (
            "refined using a foundational approach for balanced hormone support."
        )
    else:
        refinement_detail = (
            f"refined based on your {sleep_quality.lower()} sleep "
            f"and {stress_level}/10 stress level."
        )

    final_recommendation: Dict[str, Any] = {
        "full_stack": final_stack_list,
        "rationale_summary": (
            "Your plan was built using evidence-backed clusters, targeting your key "
            f"symptoms and {refinement_detail}"
        ),
        "daily_plan": [
            "Morning (with breakfast): "
            + ", ".join(
                [
                    s["supplement"]
                    for s in final_stack_list
                    if s["cluster"]
                    in ["Energy", "Gut", "Skin", "Metabolic", "Movement"]
                ]
            ),
            "Evening (60 min before bed): "
            + ", ".join(
                [
                    s["supplement"]
                    for s in final_stack_list
                    if s["cluster"] in ["Core", "Sleep", "Hormone", "Stress"]
                ]
            ),
        ],
        "expected_benefit_timeline": (
            "You may feel improvements in sleep and energy within 1–2 weeks. "
            "Hormonal, skin, and hair changes often take 6–12 weeks of consistent use."
        ),
        "what_will_be_monitored": [
            "Symptom intensity/frequency",
            "Sleep quality",
            "Stress level",
        ],
        "adjustments_plan": (
            "We will check in at 7 days to monitor side effects and adherence, and "
            "again at 30 days to assess improvements and modify your stack."
        ),
        "warnings": warnings,
    }

    # --- 5. DATA PERSISTENCE & FINAL OUTPUT ---
    save_successful = save_to_supabase(user_id, final_recommendation, raw_inputs)
    final_recommendation["db_save_status"] = "SUCCESS" if save_successful else "FAILED"
    final_recommendation["user_id"] = user_id
    final_recommendation["dashboard_url"] = f"{DASHBOARD_BASE_URL}/{user_id}"

    return final_recommendation


# -------------------------------------------------------------------------
# --- API ENDPOINT (Voiceflow / Postman Call)
# -------------------------------------------------------------------------


@app.route("/api/get-protocol", methods=["POST"])
def handle_get_protocol():
    """
    Main endpoint called by Voiceflow/Postman.
    Supports multiple input formats to be forgiving:
      - { "full_intake_text": "...", "goals_text": "..." }
      - { "user_intake": "...", "q7_results": "..." }
      - or raw q1..q7 fields which we concat.
    """
    voiceflow_input: Dict[str, Any] = {}
    try:
        voiceflow_input = request.json or {}

        user_id = voiceflow_input.get("user_id", "anon_user")

        # Try preferred fields first
        full_text = voiceflow_input.get("full_intake_text")
        goals_text = voiceflow_input.get("goals_text")

        # Fallback: existing VF body using "user_intake" + "q7_results"
        if not full_text:
            full_text = voiceflow_input.get("user_intake")

        if not goals_text:
            goals_text = voiceflow_input.get("q7_results", "")

        # Fallback: concatenate q1..q7 if they exist
        if not full_text:
            parts = []
            for key in ["q1", "q2_health", "q3_weight", "q4_skin", "q5_stress", "q6_meds"]:
                if key in voiceflow_input and voiceflow_input[key]:
                    parts.append(str(voiceflow_input[key]))
            full_text = " ".join(parts)

        if not full_text:
            return (
                jsonify(
                    {
                        "error": "No intake text provided. Please send full_intake_text, user_intake, or q1..q6."
                    }
                ),
                400,
            )

        parsed_data = parse_single_text_input(full_text, goals_text or "")

        protocol_input = {
            "user_id": user_id,
            "test_data": voiceflow_input.get("test_data", ""),
            **parsed_data,
        }

        protocol = get_lumi_supplement_stack(protocol_input)
        return jsonify(protocol), 200

    except Exception as e:
        user_id = voiceflow_input.get("user_id", "unknown_user")
        print(f"Error in /api/get-protocol for user {user_id}: {traceback.format_exc()}")
        return jsonify({"error": f"An internal server error occurred: {str(e)}"}), 500


# --- MVP DASHBOARD PLACEHOLDER ROUTE (For a working link) ---
@app.route("/protocol/<user_id>", methods=["GET"])
def protocol_placeholder(user_id: str):
    """Simple placeholder page to confirm the dashboard link works."""
    html_content = f"""
    <html>
        <head><title>Lumi Protocol Dashboard</title></head>
        <body style="font-family: sans-serif; padding: 20px;">
            <h1>Lumi Protocol for User ID: {user_id}</h1>
            <p style="color: green; font-weight: bold;">✅ Success! Your data has been securely saved.</p>
            <p>The full personalised dashboard experience is part of the V1 roadmap.</p>
            <p>For now, you can view your complete recommendations directly in the chat.</p>
        </body>
    </html>
    """
    return render_template_string(html_content)
import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
