from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer, TrainingArguments, Trainer
import torch

# 1. Define a tiny dataset (In a real project, you'd use a CSV from Kaggle)
data = [
    {"text": "I have a sharp pain in my chest and left arm", "label": 0}, # Cardiology
    {"text": "My head is spinning and I have a migraine", "label": 1},   # Neurology
    {"text": "I think I broke my ankle playing football", "label": 2},  # Orthopedics
]

# 2. Load a Pre-trained model (DistilBERT is fast)
model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)

# 3. The "Inference" Function
# For your presentation, you can start with a zero-shot classifier 
# which doesn't even need training to understand basic medical terms!
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

def get_medical_advice(user_input):
    labels = ["Cardiology", "Neurology", "Orthopedics", "Pediatrics"]
    result = classifier(user_input, candidate_labels=labels)
    
    # Returns the top specialty suggested by the AI
    return result['labels'][0], result['scores'][0]

# Test it
spec, confidence = get_medical_advice("My heart feels like it is skipping beats")
print(f"Suggested: {spec} (Confidence: {confidence:.2f})")