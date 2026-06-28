from flask import Flask, request, jsonify
import uuid
import re
import math
from datetime import datetime

app = Flask(__name__)

# Simple in-memory audit log to store our structured records
audit_log_db = []

def analyze_stylometrics(text):
    """
    Signal 1: Analyzes sentence length variance.
    Returns a confidence score between 0.0 (High Human) and 1.0 (High AI).
    """
    # Split the text into sentences based on punctuation
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    
    # Fallback if text is too short or lacks punctuation
    if len(sentences) < 2:
        return 0.50 
    
    # Count the words in each sentence
    word_counts = [len(s.split()) for s in sentences]
    
    # Calculate the mean (average) sentence length
    mean_length = sum(word_counts) / len(word_counts)
    
    # Calculate the variance and standard deviation
    variance = sum((x - mean_length) ** 2 for x in word_counts) / len(word_counts)
    std_dev = math.sqrt(variance)
    
    # Calibrate to a 0.0 - 1.0 score:
    # Uniform text (std_dev ~ 2 words) -> AI (1.0)
    # Varied text (std_dev ~ 10 words) -> Human (0.0)
    raw_score = 1.0 - ((std_dev - 2) / 8)
    
    # Clamp the final score strictly between 0.0 and 1.0
    final_score = max(0.0, min(1.0, raw_score))
    return round(final_score, 2)


@app.route('/submit', methods=['POST'])
def submit():
    # 1. Catch the incoming data
    data = request.get_json()
    text = data.get('text', '')
    creator_id = data.get('creator_id', 'unknown')
    
    # 2. Generate the unique content ID
    content_id = str(uuid.uuid4())
    
    # 3. Run Signal 1 (Stylometric Heuristics)
    stylometric_score = analyze_stylometrics(text)
    
    # 4. Placeholders for Milestone 4 (where we add the LLM and final math)
    final_confidence_score = stylometric_score # Placeholder for now
    label = "PLACEHOLDER_LABEL"
    reasoning = "Signal 1 processed. Awaiting Signal 2 integration."
    
    # 5. Write to the structured audit log
    log_entry = {
        "content_id": content_id,
        "creator_id": creator_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "stylometric_score": stylometric_score,
        "final_confidence_score": final_confidence_score,
        "label": label,
        "status": "classified"
    }
    audit_log_db.append(log_entry)
    
    # 6. Respond to the user matching our API contract
    return jsonify({
        "content_id": content_id,
        "confidence_score": final_confidence_score,
        "label": label,
        "reasoning": reasoning
    }), 200

@app.route('/log', methods=['GET'])
def get_log():
    # A simple route so you can view your audit log in the browser
    return jsonify({"entries": audit_log_db}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5001)