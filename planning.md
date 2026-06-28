# Planning Document: Provenance Guard

## Architecture

**Narrative:**
When a user submits a piece of writing, it is caught by the Flask web server dispatcher. First, Flask passes the text to the stylometric heuristic tool to analyze the purely structural style of the text. If this stylometric score is less than 0.25, the system immediately fast-tracks the result as human. If the score is 0.25 or higher, Flask passes the text to the LLM to check for semantic AI tendencies, and the two scores are averaged into a final confidence score. Before answering, Flask saves this score, the signals used, and the generated Transparency Label into the audit log database for a permanent record, and then responds to the user with the label and reasoning. 

For appeals, the user submits their unique `content_id` and reasoning to the `/appeal` endpoint. The system updates the submission's status to "under review" and attaches the appeal directly to the original audit log entry for a human reviewer.  This allows the user to not need to gather any additional info, but give the human reviewer access to all needed metadata.

**Diagram:**
========================================================================
                          SUBMISSION FLOW
========================================================================

[User Client]
      │ (POST /submit: text, creator_id)
      ▼
[Flask Dispatcher]
      │
      ▼
[Signal 2: Stylometric Heuristics]
      │
      ├── (Score < 0.25?) ── Yes ──> [Final Score = Stylometric Score] 
      │                                             │
      No (Score >= 0.25)                            │
      │                                             │
      ▼                                             │
[Signal 1: Groq LLM]                                │
      │                                             │
      ▼                                             │
[Math Logic: Average Both Scores] <─────────────────┘
      │
      ▼
[Transparency Label Engine] 
(0-0.25: High Confidence Human | 0.25-0.75: Uncertain | 0.75+: High Confidence AI)
      │
      ▼
[Audit Log Database] 
(Saves content_id, individual scores, final score, & label)
      │
      ▼
[User Client] 
(Returns content_id, final score, label, & reasoning)


========================================================================
                            APPEAL FLOW
========================================================================

[User Client]
      │ (POST /appeal: content_id, creator_reasoning)
      ▼
[Flask Dispatcher]
      │
      ▼
[Status Update Engine] -> Changes status to "under_review"
      │
      ▼
[Audit Log Database] -> Attaches appeal to original content_id row
      │
      ▼
[User Client] 
(Returns confirmation of appeal receipt)

---

## Detection Signals

**Signal 1: Stylometric Heuristics**
* **What it measures:** Analyzes purely the style and syntax of the text without semantic meaning, covering metrics like sentence length, vocabulary usage, and text patterns. Human text is naturally much more varied than uniform AI text.
* **Output:** A confidence score between 0.0 (High-Confidence Human) and 1.0 (High-Confidence AI).
* **Blind spot:** It can only detect patterns in syntax, not actual meaning. It might miss an AI-generated story that successfully mimics varied human speech tendencies but lacks coherent semantic meaning beneath the surface.

**Signal 2: LLM Analysis (Groq)**
* **What it measures:** Checks semantic patterns, evaluating AI tendencies such as unnatural switches between tones and meanings.
* **Output:** A confidence score between 0.0 and 1.0.
* **Blind spot:** It can fail to take into consideration overall structural quirks that giveaway AI generation. For example, it might struggle to properly evaluate a poem or song with a repeated section (like a chorus or a specific repeated style), missing structural context that human readers would understand.

**Combination Logic:**
Signals are combined conditionally to protect against false positives. The stylometric check runs first. If the score is below 0.25, the system bypasses the LLM and uses the stylometric score as the final score, since it most likely is human. This saves LLM processing power and permits for more false negatives than positives.  If it is 0.25 or higher, the LLM runs, and the two scores are averaged into the final confidence score.  

---

## Uncertainty Representation

* **0.00 – 0.24:** High-Confidence Human
* **0.25 – 0.74:** Uncertain
* **0.75 – 1.00:** High-Confidence AI

**Meaning of a 0.6 Score:** A score of 0.6 indicates that the text exhibits noticeable AI-like patterns (either in syntax uniformity or semantic tone), but not enough to definitively rule out a human author. It lands firmly in the "Uncertain" category.

**Calibration and Asymmetry Strategy:**
The system's logic is explicitly designed to reflect that a false positive (falsely accusing a human of using AI) is much worse than a false negative. By fast-tracking scores below 0.25, we ensure we are absolutely certain something is AI before labeling it as such, rather than blindly trusting a single stylometric check. Suspicious texts must trigger a "second opinion" (the LLM) and still average high enough to earn an AI label.  In case of the average score providing a tie, we favor giving a human score over an AI score.

---

## Transparency Label Design

Based on the final confidence score, the user will see one of the following exact text strings:

* **High-Confidence Human (0 - 0.24):** "Analysis indicates this content was highly likely written by a human."
* **Uncertain (0.25 - 0.74):** "Analysis shows mixed signals. The origin of this content is uncertain."
* **High-Confidence AI (0.75+):** "Analysis indicates this content was highly likely generated by AI."

---

## Appeals Workflow

* **Who can appeal:** Any user who submitted a piece of content. 
* **Information Provided:** The user must provide their unique `content_id` (received upon original submission) and their specific `creator_reasoning`.
* **System Actions:** The Flask server locates the corresponding entry in the audit log using the `content_id`, appends the creator's reasoning, and updates the `status` field to "under_review".
* **Reviewer View:** A human reviewer querying the database will immediately see the matched record, including the original text, the individual stylometric and LLM scores, the final average, and the creator's written defense, providing full context for a manual decision.

---

## Anticipated Edge Cases

1.  **Repetitive Creative Formatting:** A human-written poem or song that includes a heavily repeated section (like a chorus) or repeated stylistic choices. The stylometric tool might flag this heavy repetition as "uniform AI syntax," while the LLM might miss the artistic structural intention, leading to an unfair "Uncertain" or "AI" flag.
2.  **Highly Tuned AI Personas:** An AI-generated story explicitly prompted to include varied human speech tendencies and erratic sentence lengths. The stylometric tool might score this safely below 0.25, bypassing the LLM entirely and resulting in a false negative (labeling AI text as human).

---

## AI Tool Plan

* **M3 (Submission endpoint + first signal):** * *Inputs:* I will provide the "Architecture" diagram and the "Detection Signals" section.
    * *Prompt Request:* Generate the basic Flask app skeleton, the `POST /submit` route stub, and the Python function for the Stylometric Heuristics signal.
    * *Verification:* I will test the stylometric function with a few hardcoded strings in the terminal before wiring it into the Flask endpoint to ensure the math outputs a 0-1 score.
* **M4 (Second signal + confidence scoring):** * *Inputs:* I will provide the "Detection Signals", "Uncertainty Representation", and the Diagram.
    * *Prompt Request:* Generate the Groq LLM API call function and the specific conditional logic that averages the scores only if the stylometric score is >= 0.25.
    * *Verification:* I will run 4 distinct texts (clear AI, clear human, 2 borderline) through the system to ensure the conditional averaging works and scores vary meaningfully.
* **M5 (Production layer):** * *Inputs:* I will provide the "Transparency Label Design", "Appeals Workflow", and the Diagram.
    * *Prompt Request:* Generate the Python logic to map the final score to the exact label strings, and build the `POST /appeal` endpoint to update the audit log status.
    * *Verification:* I will use cURL or Postman to submit an appeal with a `content_id` and check the JSON audit log to ensure the status successfully changed to "under_review".