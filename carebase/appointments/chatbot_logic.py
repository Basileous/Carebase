import re

import requests
from django.conf import settings


KEYWORD_RULES = [
    {
        "specialty": "Cardiology",
        "keywords": {
            "chest pain",
            "heart",
            "palpitation",
            "palpitations",
            "shortness of breath",
            "left arm",
            "blood pressure",
            "bp",
        },
        "diagnosis": "Possible heart or blood pressure related symptoms",
        "precautions": (
            "1. Avoid physical exertion and rest in a comfortable position.\n"
            "2. Seek urgent medical help if chest pain, sweating, or breathlessness is severe.\n"
            "3. Keep a record of pulse, blood pressure, and symptom duration."
        ),
    },
    {
        "specialty": "Neurology",
        "keywords": {
            "headache",
            "migraine",
            "dizziness",
            "seizure",
            "numbness",
            "weakness",
            "faint",
            "vertigo",
        },
        "diagnosis": "Possible neurological symptoms such as migraine, dizziness, or nerve-related discomfort",
        "precautions": (
            "1. Rest in a quiet place and avoid bright light or screen strain.\n"
            "2. Drink water and note any numbness, weakness, confusion, or vision changes.\n"
            "3. Seek urgent care if symptoms are sudden, severe, or one-sided."
        ),
    },
    {
        "specialty": "Orthopedics",
        "keywords": {
            "fracture",
            "broken",
            "sprain",
            "ankle",
            "knee",
            "bone",
            "joint",
            "back pain",
            "shoulder",
        },
        "diagnosis": "Possible bone, joint, muscle, or injury-related symptoms",
        "precautions": (
            "1. Avoid putting weight or pressure on the painful area.\n"
            "2. Apply a cold pack wrapped in cloth for short intervals.\n"
            "3. Visit a doctor for examination and imaging if swelling, deformity, or severe pain is present."
        ),
    },
    {
        "specialty": "Pediatrics",
        "keywords": {
            "child",
            "baby",
            "infant",
            "toddler",
            "kid",
            "children",
            "newborn",
        },
        "diagnosis": "Child health symptoms requiring pediatric assessment",
        "precautions": (
            "1. Monitor temperature, feeding, hydration, and activity level.\n"
            "2. Avoid giving adult medicines to children without medical advice.\n"
            "3. Seek urgent care for breathing difficulty, persistent fever, dehydration, or unusual drowsiness."
        ),
    },
    {
        "specialty": "Dermatology",
        "keywords": {
            "rash",
            "skin",
            "itch",
            "itching",
            "acne",
            "allergy",
            "hives",
            "eczema",
            "spots",
        },
        "diagnosis": "Possible skin irritation, allergy, infection, or dermatological condition",
        "precautions": (
            "1. Avoid scratching and keep the affected area clean and dry.\n"
            "2. Stop using any new cream, soap, or product that may have triggered symptoms.\n"
            "3. Consult a doctor if rash spreads, becomes painful, or comes with fever."
        ),
    },
    {
        "specialty": "General Medicine",
        "keywords": {
            "fever",
            "cough",
            "cold",
            "flu",
            "throat",
            "sore throat",
            "nausea",
            "vomit",
            "vomiting",
            "diarrhea",
            "stomach",
            "fatigue",
            "body pain",
        },
        "diagnosis": "Possible general illness such as infection, flu, stomach upset, or fatigue",
        "precautions": (
            "1. Rest, drink fluids, and monitor temperature and symptom changes.\n"
            "2. Avoid self-medicating with antibiotics or strong painkillers.\n"
            "3. Consult a doctor if symptoms worsen, persist, or include breathing difficulty."
        ),
    },
]


def _fallback_advice(user_input=""):
    text = (user_input or "").lower()

    best_rule = None
    best_score = 0
    for rule in KEYWORD_RULES:
        score = sum(1 for keyword in rule["keywords"] if keyword in text)
        if score > best_score:
            best_rule = rule
            best_score = score

    if not best_rule:
        best_rule = KEYWORD_RULES[-1]

    return best_rule["specialty"], best_rule["diagnosis"], best_rule["precautions"]


def _call_xai_chat_completion(user_input):
    api_key = getattr(settings, "XAI_API_KEY", "")
    if not api_key:
        return None

    response = requests.post(
        getattr(settings, "XAI_RESPONSES_URL", "https://api.x.ai/v1/responses"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": getattr(settings, "XAI_MODEL", "grok-4.3"),
            "store": False,
            "input": [
                {
                    "role": "system",
                    "content": (
                        "You are a medical triage AI. Return the analysis EXACTLY "
                        "in this format: SPECIALTY: [name], DIAGNOSIS: [conditions], "
                        "PRECAUTIONS: [List exactly 3 distinct, numbered precautionary steps]."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Analyze these symptoms: {user_input}",
                },
            ],
        },
        timeout=30,
    )
    response.raise_for_status()
    return _extract_response_text(response.json())


def _extract_response_text(payload):
    if payload.get("output_text"):
        return payload["output_text"]

    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                return content.get("text", "")

    return ""


def get_medical_advice(user_input):
    try:
        full_text = _call_xai_chat_completion(user_input)
        if not full_text:
            return _fallback_advice(user_input)

        clean_text = full_text.replace("*", "")

        specialty = "General"
        diagnosis = "Analysis unavailable"
        precautions = "Please consult a doctor."

        spec_match = re.search(
            r"SPECIALTY:\s*(.*?)(?=,\s*DIAGNOSIS:|$)",
            clean_text,
            re.IGNORECASE,
        )
        diag_match = re.search(
            r"DIAGNOSIS:\s*(.*?)(?=,\s*PRECAUTIONS:|$)",
            clean_text,
            re.IGNORECASE,
        )
        prec_match = re.search(
            r"PRECAUTIONS:\s*(.*)",
            clean_text,
            re.IGNORECASE | re.DOTALL,
        )

        if spec_match:
            specialty = spec_match.group(1).strip()
        if diag_match:
            diagnosis = diag_match.group(1).strip()
        if prec_match:
            precautions = prec_match.group(1).strip()

        return specialty, diagnosis, precautions

    except Exception as exc:
        print(f"xAI Grok Logic Error: {exc}")
        return _fallback_advice(user_input)
