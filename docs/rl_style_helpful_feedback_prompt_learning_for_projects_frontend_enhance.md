# RL‑style Helpful Feedback & Prompt Learning for `projects/frontend_enhance`

This adds a **bandit‑style prompt learning loop** on top of the existing `frontend_enhance` pipeline. It logs every prompt → outcome pair, distills **helpful feedback** from the evaluator, and selects the next prompt variant using a lightweight multi‑armed bandit—so it works even with a tiny local model (≈3B) on 8GB VRAM.

---

## What you get

1. **Helpful feedback agent** that turns raw evaluator output into short, actionable bullets tied to prompt sections.
2. **Prompt ledger** (`JSONL`) that records prompt text, hashes, scores, pass/fail signals, and diffs.
3. **Bandit selector** (UCB / Thompson) that picks the next prompt template/variant to try.
4. **Minimal diffs to `test.light.yaml`**—drop‑in nodes and connections.
5. **Local LLM ready** (Ollama adapter supported in repo). The heavy work (code eval) stays deterministic; only feedback/summarization uses a small LLM.

---

## Files to add

Create a new folder:
```
projects/frontend_enhance/rl_feedback/
├─ code/
│  ├─ prompt_bandit.py
│  └─ feedback_utils.py
├─ prompts/
│  └─ feedback_critic.txt
└─ schemas/
   └─ outcome.schema.json
```

### `projects/frontend_enhance/rl_feedback/schemas/outcome.schema.json`
A strict envelope for evaluator results we log and learn from:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["score", "metrics", "issues", "generated_prompt"],
  "properties": {
    "score": {"type": "number", "minimum": 0, "maximum": 100},
    "metrics": {
      "type": "object",
      "properties": {
        "compile_ok": {"type": "boolean"},
        "a11y": {"type": "number"},
        "perf": {"type": "number"},
        "tests": {"type": "number"}
      },
      "additionalProperties": true
    },
    "issues": {"type": "array", "items": {"type": "string"}},
    "generated_prompt": {
      "type": "object",
      "required": ["prompt_text"],
      "properties": {
        "prompt_text": {"type": "string"},
        "sections": {"type": "array", "items": {"type": "string"}},
        "template_id": {"type": "string"}
      },
      "additionalProperties": true
    }
  },
  "additionalProperties": true
}
```

### `projects/frontend_enhance/rl_feedback/prompts/feedback_critic.txt`
A tiny prompt for a small local LLM to transform evaluator output → succinct, actionable guidance.
```
You are a FEEDBACK CRITIC for prompt engineering.
INPUTS
- candidate prompt (text + optional sections)
- evaluator outcome: score (0-100) + metrics (compile_ok, a11y, perf, tests, etc.) + issues[]
TASK
- Produce actionable feedback that edits the prompt (NOT the code) to improve the next try.
- Tie each bullet to a prompt section or add a new section name if missing.
- Keep it brief and explicit; no fluff.
OUTPUT JSON (strict):
{
  "what_worked": ["..."],
  "what_failed": ["..."],
  "edits": [ {"section": "<name>", "change": "replace|insert|remove", "instruction": "1-line action"} ],
  "next_prompt_hints": ["short directive lines to append"]
}
```

### `projects/frontend_enhance/rl_feedback/code/feedback_utils.py`
Utility helpers shared by nodes.
```python
import hashlib, json, time, os
from typing import Any, Dict

LEDGER_PATH = "projects/frontend_enhance/generated/prompt_ledger.jsonl"
BEST_LIBRARY = "projects/frontend_enhance/generated/prompt_library.json"

os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)

def text_hash(txt: str) -> str:
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()[:16]

def append_ledger(record: Dict[str, Any], ledger_path: str = LEDGER_PATH) -> None:
    record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **record}
    with open(ledger_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def load_ledger(ledger_path: str = LEDGER_PATH):
    if not os.path.exists(ledger_path):
        return []
    with open(ledger_path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def update_topk_library(k: int = 5, ledger_path: str = LEDGER_PATH, out: str = BEST_LIBRARY):
    rows = load_ledger(ledger_path)
    # score first, tie-breaker: compile_ok then recency
    rows.sort(key=lambda r: (r.get("score", 0), r.get("metrics", {}).get("compile_ok", False), r.get("ts")), reverse=True)
    top = {}
    for r in rows:
        pid = r.get("generated_prompt", {}).get("template_id") or text_hash(r.get("generated_prompt", {}).get("prompt_text", ""))
        if pid not in top:
            top[pid] = {
                "prompt_text": r["generated_prompt"]["prompt_text"],
                "template_id": pid,
                "best_score": r.get("score", 0),
                "last_ts": r["ts"]
            }
        if len(top) >= k:
            break
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"top": list(top.values())}, f, ensure_ascii=False, indent=2)
```

### `projects/frontend_enhance/rl_feedback/code/prompt_bandit.py`
Bandit selection + logging. Uses **UCB1** by default, falls back to **ε‑greedy** when little data.
```python
from typing import Any, Dict, List
import json, math, random
from .feedback_utils import append_ledger, load_ledger, update_topk_library, text_hash

# === RECORD OUTCOME ===
# Inputs expected via code_job kwargs: score, metrics, issues, generated_prompt, feedback
# Return value is ignored; we append to ledger and refresh the top-k library

def record_result(**kwargs) -> Dict[str, Any]:
    payload = {
        "score": float(kwargs.get("score", 0)),
        "metrics": kwargs.get("metrics", {}),
        "issues": kwargs.get("issues", []),
        "generated_prompt": kwargs.get("generated_prompt", {}),
        "feedback": kwargs.get("feedback", {})
    }
    if "prompt_text" in payload["generated_prompt"]:
        payload["generated_prompt"]["hash"] = text_hash(payload["generated_prompt"]["prompt_text"])
    append_ledger(payload)
    update_topk_library()
    return {"logged": True}

# === SELECT NEXT PROMPT VARIANT ===
# Inputs: candidates (list[str] or list[{prompt_text, template_id}]), target_score, min_explore (int)
# Output: {"selected": {"prompt_text": str, "template_id": str}}

def _canonicalize_candidates(cands: Any) -> List[Dict[str, str]]:
    items: List[Dict[str, str]] = []
    if isinstance(cands, list):
        for c in cands:
            if isinstance(c, str):
                items.append({"prompt_text": c, "template_id": text_hash(c)})
            elif isinstance(c, dict) and "prompt_text" in c:
                tid = c.get("template_id") or text_hash(c["prompt_text"])
                items.append({"prompt_text": c["prompt_text"], "template_id": tid})
    return items


def select_next(**kwargs) -> Dict[str, Any]:
    candidates = _canonicalize_candidates(kwargs.get("candidates", []))
    target = float(kwargs.get("target_score", 85))
    min_explore = int(kwargs.get("min_explore", 2))

    ledger = load_ledger()
    # Aggregate per template_id
    stats: Dict[str, Dict[str, float]] = {}
    for r in ledger:
        gp = r.get("generated_prompt", {})
        tid = gp.get("template_id") or gp.get("hash") or text_hash(gp.get("prompt_text", ""))
        s = stats.setdefault(tid, {"n": 0.0, "sum": 0.0})
        s["n"] += 1
        s["sum"] += float(r.get("score", 0.0))

    # If any candidate is unseen fewer than min_explore times, explore it first
    for c in candidates:
        tid = c["template_id"]
        n = stats.get(tid, {}).get("n", 0)
        if n < min_explore:
            return {"selected": c, "strategy": "cold_start"}

    # UCB1 on normalized rewards (score/target clipped to [0,1])
    total_n = sum(int(v["n"]) for v in stats.values()) or 1
    def ucb(mean, n, t):
        return mean + math.sqrt(2.0 * math.log(t) / max(n, 1))

    best = None
    best_ucb = -1.0
    for c in candidates:
        tid = c["template_id"]
        s = stats.get(tid, {"n": 0.0, "sum": 0.0})
        n = s["n"] or 1
        mean = (s["sum"] / n) / max(target, 1.0)
        val = ucb(mean, n, total_n)
        if val > best_ucb:
            best_ucb = val
            best = c

    if best is None and candidates:
        best = random.choice(candidates)
    return {"selected": best or {}, "strategy": "ucb1"}
```

---

## Light‑diagram changes

Below is a **surgical patch** for `projects/frontend_enhance/test.light.yaml`. Paste the blocks into the existing diagram. Labels are unique, so it won’t clash.

### 1) Add a small local person (Feedback Critic)
Under `persons:`:
```yaml
  Feedback Critic:
    service: ollama          # fallback: openai (gpt-5-nano-2025-08-07)
    model: qwen2.5:3b-instruct
    system_prompt: |
      You turn evaluator results into succinct, actionable prompt edits.
      Keep answers JSON-only as specified by the prompt file.
```
> If you don’t run Ollama, replace with your hosted small model.

### 2) Make `Generate Prompt` return structured JSON
Change the node to add `text_format` so downstream nodes can read `prompt_text` reliably:
```yaml
- label: Generate Prompt
  type: person_job
  props:
    person: Prompt Designer
    first_prompt_file: prompt_generator_first.txt
    prompt_file: prompt_generator.txt
    max_iteration: 3
    memory_profile: ONLY_I_SENT
    text_format: |
      {"type":"object","properties":{"prompt_text":{"type":"string"},"sections":{"type":"array","items":{"type":"string"}},"template_id":{"type":"string"}},"required":["prompt_text"]}
```

### 3) New nodes (add after "Evaluate Generated Code")
```yaml
- label: Validate Outcome
  type: json_schema_validator
  position: {x: 1120, y: 540}
  props:
    schema: {{file("projects/frontend_enhance/rl_feedback/schemas/outcome.schema.json")}}
    strict: false

- label: Summarize Helpful Feedback
  type: person_job
  position: {x: 1280, y: 540}
  props:
    person: Feedback Critic
    prompt_file: rl_feedback/prompts/feedback_critic.txt
    max_iteration: 1
    memory_profile: MINIMAL

- label: Update Prompt Ledger
  type: code_job
  position: {x: 1440, y: 540}
  props:
    language: python
    code: projects/frontend_enhance/rl_feedback/code/prompt_bandit.py
    functionName: record_result

- label: Select Next Prompt
  type: code_job
  position: {x: 1600, y: 540}
  props:
    language: python
    code: projects/frontend_enhance/rl_feedback/code/prompt_bandit.py
    functionName: select_next
```

### 4) Wire up the connections
Replace the single edge from `Check Quality Target_condfalse → Detect Max Iterations` with the following chain that adds feedback + selection, and then rejoins the loop:
```yaml
# From evaluation to outcome envelope
- {from: Evaluate Generated Code, to: Validate Outcome, label: outcome, content_type: object}

# Critic turns outcome → actionable edits (JSON)
- {from: Validate Outcome, to: Summarize Helpful Feedback, label: outcome, content_type: object}

# Log to ledger (for learning)
- {from: Summarize Helpful Feedback, to: Update Prompt Ledger, label: feedback, content_type: object}

# Optional candidate templates: pass current + top-K from library (if present)
- {from: Update Prompt Ledger, to: Select Next Prompt, label: ledger_state, content_type: object}

# Re-enter loop with feedback payload; selector result is available as `selected` (template + text)
- {from: Summarize Helpful Feedback, to: Generate Prompt, label: feedback, content_type: object}
- {from: Select Next Prompt, to: Generate Prompt, label: selected, content_type: object}

# Keep max-iteration guard
- {from: Check Quality Target_condfalse, to: Detect Max Iterations}
- {from: Detect Max Iterations_condfalse, to: Generate Prompt}
- {from: Detect Max Iterations_condtrue, to: Stop if Max Iterations}
```

> The `Generate Prompt` prompt can use `{{selected.prompt_text}}` and the critic’s `{{feedback.edits}}` to concretely rewrite the next prompt.

---

## How the loop approximates RL

- **Policy**: the prompt template/edits we choose. The bandit’s **UCB1** balances exploration and exploitation across templates.
- **Environment recognizer**: deterministic evaluator metrics (compile_ok, a11y, perf, tests) + score; the critic compresses this into **prompt‑level actions**.
- **Reward**: normalized score (score/target) and compile_ok bonus; this is what the bandit optimizes.

This is intentionally light‑weight (no gradients, no GPU training) yet yields the same *learning from rollouts* intuition.

---

## Local LLM knobs (8GB VRAM)

- Run the **Feedback Critic** on a 3B model (e.g., Qwen2.5‑3B via Ollama). Keep `max_iteration: 1` and short prompts.
- Keep evaluator on your hosted model (it already exists) to avoid local GPU usage.
- Use memory profiles to cap context:
  - `Generate Prompt`: `ONLY_I_SENT` (only its own prior messages)
  - `Feedback Critic`: `MINIMAL` (system + last 5)
  - `Code Evaluator`: `GOLDFISH` (already set) to avoid drift

---

## Quick run

1. Add files above.
2. Patch `test.light.yaml` as shown.
3. Run:
   ```bash
   dipeo run projects/frontend_enhance/test --light --debug --timeout=180
   ```
4. Results:
   - `projects/frontend_enhance/generated/prompt_ledger.jsonl` (full history)
   - `projects/frontend_enhance/generated/prompt_library.json` (top‑K prompts)
   - Usual generated app + README as before

---

## Optional: batch candidate prompts (faster convergence)

Add a `person_batch_job` to emit 2–3 prompt candidates per iteration and evaluate them in parallel using a sub‑diagram that reuses your existing **Generate → Evaluate** slice. Keep batch size small to respect tokens/latency. (Can be added later without changing the ledger/selector.)

---

## Minimal prompt changes (example)

In `prompt_generator.txt`, allow using selector output if present:
```
If {{selected.prompt_text}} exists, start from it; otherwise use the base template.
Apply the following edits strictly:
{{#each feedback.edits}}
- Section "{{section}}": {{change}} → {{instruction}}
{{/each}}
Return JSON with prompt_text (final) and sections (updated list).
```
