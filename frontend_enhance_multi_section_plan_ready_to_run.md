# Goal

Turn `frontend_enhance` into a multi‑section generator that:

1. understands the user’s frontend ask, 2) splits it into N sections, and 3) implements each section in parallel using the existing iterative loop (prompt→code→evaluate→refine). This reuses the current agents and scripts, avoids hardcoding N nodes, and records what prompts worked.

---

## Diagram A — `projects/frontend_enhance/multi_section.light.yaml`

```yaml
version: light

persons:
  Section Planner:
    service: openai
    model: gpt-5-nano-2025-08-07
    api_key_id: APIKEY_52609F
    system_prompt: |
      You are a senior product/front-end architect. Given app requirements, split work into sections
      (pages, features, or components). Output strict JSON with:
      [ { "id": "kebab-case", "title": "", "description": "", "acceptance": ["..."], "prompt_context": { ... } } ]
      Keep ids short and unique. Do not include commentary.

  # Reuse the existing three for Section implementation sub-diagram
  Prompt Designer:
    service: openai
    model: gpt-5-nano-2025-08-07
    api_key_id: APIKEY_52609F
  Frontend Generator:
    service: openai
    model: gpt-5-nano-2025-08-07
    api_key_id: APIKEY_52609F
  Code Evaluator:
    service: openai
    model: gpt-5-nano-2025-08-07
    api_key_id: APIKEY_52609F

nodes:
  - label: Start
    type: start
    position: {x: 60, y: 200}
    props:
      trigger_mode: manual
      custom_data:
        # Optionally pass a free-form user ask at run time
        # user_request: "Build a SaaS dashboard with auth, team management, and billing"
        
  - label: Load Config
    type: db
    position: {x: 220, y: 200}
    props:
      operation: read
      sub_type: file
      source_details: projects/frontend_enhance/frontend_enhance_config.json

  - label: Understand Requirements
    type: person_job
    position: {x: 460, y: 200}
    props:
      person: Section Planner
      max_iteration: 1
      memory_profile: MINIMAL
      default_prompt: |
        Convert this into a JSON section plan (no comments):
        App config: {{config}}
        User request (optional): {{user_request}}

  - label: Parse Sections
    type: code_job
    position: {x: 720, y: 200}
    props:
      language: python
      code: |
        import json
        body = json.loads(understanding)
        assert isinstance(body, list) and body, "Planner must return a non-empty JSON array"
        # Light batch expects an array under a key
        result = {"sections": body, "target_score": json.loads(config).get("target_score", 85)}

  - label: Implement Sections
    type: sub_diagram
    position: {x: 980, y: 200}
    props:
      diagram_name: projects/frontend_enhance/section_implementor
      diagram_format: light
      passInputData: true
      batch: true
      batch_input_key: sections
      batch_parallel: true

  - label: Aggregate Results
    type: code_job
    position: {x: 1260, y: 200}
    props:
      language: python
      code: |
        import statistics
        scores = [it.get("score", 0) for it in batch_results]
        ok = all(s >= target_score for s in scores)
        result = {
          "sections_done": len(scores),
          "scores": scores,
          "min_score": min(scores) if scores else 0,
          "avg_score": round(statistics.mean(scores), 2) if scores else 0,
          "target": target_score,
          "success": ok,
        }

  - label: Save Summary
    type: endpoint
    position: {x: 1540, y: 200}
    props:
      file_format: json
      save_to_file: true
      file_path: projects/frontend_enhance/generated/results.multi_section.json

connections:
  - {from: Start, to: Load Config}
  - {from: Load Config, to: Understand Requirements, label: config}
  - {from: Start, to: Understand Requirements, label: user_request}
  - {from: Understand Requirements, to: Parse Sections, label: understanding}
  - {from: Parse Sections, to: Implement Sections, content_type: object}
  - {from: Implement Sections, to: Aggregate Results, label: batch_results, content_type: object}
  - {from: Parse Sections, to: Aggregate Results, label: target_score, content_type: object}
  - {from: Aggregate Results, to: Save Summary, content_type: object}
```

---

## Diagram B — `projects/frontend_enhance/section_implementor.light.yaml`

> Executes the **existing frontend\_enhance iterative loop** per section and returns `{ id, score, app_path, prompt, feedback }` for aggregation.

```yaml
version: light

persons:
  Prompt Designer:
    service: openai
    model: gpt-5-nano-2025-08-07
    api_key_id: APIKEY_52609F
    system_prompt: |
      You are an expert in prompt engineering for code generation. Improve prompts rapidly.
  Frontend Generator:
    service: openai
    model: gpt-5-nano-2025-08-07
    api_key_id: APIKEY_52609F
    system_prompt: |
      You are an expert React/TypeScript engineer. Generate production-ready code only.
  Code Evaluator:
    service: openai
    model: gpt-5-nano-2025-08-07
    api_key_id: APIKEY_52609F
    system_prompt: |
      You are a strict frontend quality reviewer. Score 0–100 and give prompt-centered feedback.

nodes:
  - label: Start
    type: start
    position: {x: 60, y: 240}

  - label: Prepare Context
    type: code_job
    position: {x: 260, y: 240}
    props:
      language: python
      code: |
        import json
        # 'item' arrives from the batch parent and contains one section
        sec = item
        cfg = json.loads(config)
        result = {
          "section": sec,
          "section_id": sec["id"],
          "target_score": cfg.get("target_score", 85),
          "prompt_requirements": cfg.get("prompt_requirements", []),
          "framework": cfg.get("framework", "react"),
          "app_type": cfg.get("app_type", "dashboard"),
        }

  - label: Generate Prompt
    type: person_job
    position: {x: 520, y: 240}
    props:
      person: Prompt Designer
      first_prompt_file: projects/frontend_enhance/prompts/prompt_generator_first.txt
      prompt_file: projects/frontend_enhance/prompts/prompt_generator.txt
      max_iteration: 3
      memory_profile: ONLY_I_SENT
      default_prompt: |
        Section: {{section.title}}
        Description: {{section.description}}
        Acceptance: {{section.acceptance}}
        Framework: {{framework}} / App Type: {{app_type}}
        Global requirements: {{prompt_requirements}}
        Create the *best* prompt to generate just this section.

  - label: Generate Frontend Code
    type: person_job
    position: {x: 820, y: 240}
    props:
      person: Frontend Generator
      max_iteration: 1
      memory_profile: FOCUSED
      default_prompt: |
        Use this prompt to generate the section code:
        {{Generate Prompt}}

  - label: Evaluate Generated Code
    type: person_job
    position: {x: 1080, y: 240}
    props:
      person: Code Evaluator
      max_iteration: 1
      memory_profile: FULL
      prompt_file: projects/frontend_enhance/prompts/code_evaluator.txt

  - label: Check Quality Target
    type: condition
    position: {x: 1340, y: 240}
    props:
      condition_type: custom
      expression: int(code_evaluation.get("score", 0)) >= int(target_score)

  - label: Detect Max Iterations
    type: condition
    position: {x: 1340, y: 420}
    props:
      condition_type: detect_max_iterations

  - label: Extract and Setup App
    type: code_job
    position: {x: 1620, y: 220}
    props:
      language: python
      filePath: projects/frontend_enhance/code/extract_and_setup_app.py
      functionName: main

  - label: Save Prompt & Feedback
    type: db
    position: {x: 1880, y: 220}
    props:
      operation: write
      sub_type: file
      format: json
      source_details: projects/frontend_enhance/generated/results.json

  - label: Return Result
    type: code_job
    position: {x: 2140, y: 220}
    props:
      language: python
      code: |
        # Normalize return payload to a compact object per section
        result = {
          "id": section_id,
          "score": int(code_evaluation.get("score", 0)),
          "app_path": (extract_result or {}).get("app_path"),
          "prompt": str(Generate_Prompt),
          "feedback": code_evaluation,
        }

  - label: Stop (Max Iterations)
    type: endpoint
    position: {x: 1620, y: 520}
    props:
      file_format: txt
      save_to_file: false

connections:
  - {from: Start, to: Prepare Context}
  - {from: Prepare Context, to: Generate Prompt, content_type: object}
  - {from: Generate Prompt, to: Generate Frontend Code, content_type: raw_text}
  - {from: Generate Frontend Code, to: Evaluate Generated Code, label: generated_code, content_type: object}
  - {from: Evaluate Generated Code, to: Check Quality Target, label: code_evaluation, content_type: object}
  - {from: Check Quality Target_condtrue, to: Extract and Setup App, label: generated_code, content_type: object}
  - {from: Check Quality Target_condtrue, to: Extract and Setup App, label: section_id, content_type: object}
  - {from: Extract and Setup App, to: Save Prompt & Feedback, label: extract_result, content_type: object}
  - {from: Generate Prompt, to: Save Prompt & Feedback, label: prompt_text, content_type: raw_text}
  - {from: Evaluate Generated Code, to: Save Prompt & Feedback, label: code_evaluation, content_type: object}
  - {from: Save Prompt & Feedback, to: Return Result, content_type: object}
  - {from: Check Quality Target_condfalse, to: Detect Max Iterations}
  - {from: Detect Max Iterations_condtrue, to: Stop (Max Iterations)}
  - {from: Detect Max Iterations_condfalse, to: Generate Prompt, label: feedback, content_type: object}
```

### Notes

- The parent passes `config` and each `item` (a section) to this sub‑diagram via `passInputData: true` + `batch: true`.
- We keep **Prompt Designer** memory as `ONLY_I_SENT` (fast iteration), **Generator** as `FOCUSED`, **Evaluator** as `FULL`.
- We log per‑section prompt + evaluation into `projects/frontend_enhance/generated/results.json` so you can build a prompt library later.

---

## (Tiny) patch — allow naming per‑section app outputs

Add an optional `app_name` override to the existing extractor so each section writes to its own folder (e.g., `section-auth`, `section-billing`).

`projects/frontend_enhance/code/extract_and_setup_app.py`

```diff
 def main(inputs):
@@
-    # Parse the generated code from JSON
-    generated_code = inputs.get('generated_code', '')
+    # Parse inputs
+    generated_code = inputs.get('generated_code', '')
+    app_name_override = inputs.get('app_name')  # optional
@@
-    # Determine app name from content
-    app_name = get_app_name_from_content(files)
+    # Determine app name from content (or override)
+    app_name = app_name_override or get_app_name_from_content(files)
```

Then pass it from the sub‑diagram by adding an extra connection (already labeled `section_id` above) and adjusting the node like this:

```yaml
  - label: Extract and Setup App
    type: code_job
    props:
      language: python
      filePath: projects/frontend_enhance/code/extract_and_setup_app.py
      functionName: main
    # (no YAML change needed — inputs from connections become kwargs)
```

The extractor will receive `{ generated_code, section_id }`; inside `main()` the `app_name_override = inputs.get('app_name')` can be switched to `inputs.get('section_id')` if you prefer reusing that directly.

---

## How to run

```bash
# 1) Drop both YAML files into projects/frontend_enhance/
# 2) (Optional) Apply the small extractor patch above
# 3) Execute the parent diagram
 dipeo run projects/frontend_enhance/multi_section --light --debug --timeout=240 \
   --input-data '{"user_request":"Build a SaaS dashboard with auth, team management, billing"}'
```

That will produce per‑section apps under `projects/frontend_enhance/*-app` (or `section-<id>` if you wire the override), plus an overall `results.multi_section.json`.

---

## Extras you can add later

- **Retry weak sections only**: In the parent diagram, add a condition after `Aggregate Results` that filters sections with `score < target` and re‑runs the sub‑diagram with just those.
- **Prompt library**: Append `{section_id, prompt_text, score}` to `projects/frontend_enhance/generated/prompt_library.jsonl` via a small `db` write in `Save Prompt & Feedback`.
- **PersonBatch alternative**: You could replace the sub‑diagram with a `person_batch_job` if you want a single person to implement 1‑hop tasks across many items; this design keeps the full iterate→evaluate loop per section.

