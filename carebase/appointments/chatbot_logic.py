import re
from groq import Groq

client = Groq(api_key="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")

def get_medical_advice(user_input):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    # UPDATE 1: Strict prompt demanding a numbered list
                    "content": "You are a medical triage AI. Return the analysis EXACTLY in this format: SPECIALTY: [name], DIAGNOSIS: [conditions], PRECAUTIONS: [List exactly 3 distinct, numbered precautionary steps]."
                },
                {
                    "role": "user",
                    "content": f"Analyze these symptoms: {user_input}"
                }
            ],
            model="llama-3.1-8b-instant", 
            temperature=0.2, 
        )
        
        full_text = chat_completion.choices[0].message.content
        clean_text = full_text.replace("*", "")
        
        specialty = "General"
        diagnosis = "Analysis unavailable"
        precautions = "Please consult a doctor."
        
        spec_match = re.search(r"SPECIALTY:\s*(.*?)(?=,\s*DIAGNOSIS:|$)", clean_text, re.IGNORECASE)
        diag_match = re.search(r"DIAGNOSIS:\s*(.*?)(?=,\s*PRECAUTIONS:|$)", clean_text, re.IGNORECASE)
        
        # UPDATE 2: Added re.DOTALL so it captures multi-line lists perfectly
        prec_match = re.search(r"PRECAUTIONS:\s*(.*)", clean_text, re.IGNORECASE | re.DOTALL)
        
        if spec_match: specialty = spec_match.group(1).strip()
        if diag_match: diagnosis = diag_match.group(1).strip()
        if prec_match: precautions = prec_match.group(1).strip()
            
        return specialty, diagnosis, precautions
        
    except Exception as e:
        print(f"🚨 Groq AI Logic Error: {e}")
        return "General Medicine", "Service currently unavailable", "Please consult a doctor immediately."