# TODO: Loop Handling Design Analysis

## 1. Problem Statement

### Current Issue
The simplified dependency checking logic in `dynamic_order_calculator.py` creates a **deadlock** in loop scenarios, particularly visible in the `simple_iter` diagram.

### Example: simple_iter Diagram Structure
```
start ──→ printer ──→ condition ──┐
             ↑                     │
             └─────condfalse───────┘
                   condtrue
                      ↓
                     ask ──→ endpoint
```

### The Deadlock
- `printer` node has two inputs:
  1. Initial edge from `start`
  2. Loop-back edge from `condition_condfalse`
- With "ALL dependencies" rule, `printer` waits for both edges
- But `condition` can't execute until `printer` executes first
- **Result**: Circular dependency causing execution to hang

## 2. Root Cause Analysis

### Current Simplified Rules
1. **Condition nodes**: Execute when ANY dependency is satisfied (OR logic)
2. **Other nodes**: Execute when ALL dependencies are satisfied (AND logic)

### Why This Breaks Loops
- Loop-back edges are treated as regular dependencies
- Nodes with both initial and loop-back edges wait for ALL to be satisfied
- Creates impossible-to-satisfy circular dependencies

## 3. Design Options

### Option A: Condition-First Pattern
```
start ──→ condition ──→ printer ──→ condition (loop)
```
**Pros:**
- No ambiguity about dependencies
- Clean dependency graph

**Cons:**
- **Unintuitive**: What does condition check on first iteration?
- No data to evaluate (counter = 0?)
- Requires pre-initialization logic
- Less natural for users

### Option B: Job-First Pattern (Current Design)
```
start ──→ printer ──→ condition ──→ printer (loop)
```
**Pros:**
- **Natural do-while semantics**: Execute at least once
- Condition has actual data to check
- Intuitive for iteration counting
- Matches user expectations

**Cons:**
- Creates complex dependency scenarios
- Requires special handling for loop-back edges

### Option C: Smart Loop Handling (Recommended)
Keep Job-First pattern but intelligently handle loop-back edges:

**Rules:**
1. Identify loop-back edges (from condition nodes: `condtrue`/`condfalse`)
2. On first execution (execution_count = 0): Ignore loop-back edges
3. On subsequent executions: Consider loop-back edges for continuation

**Pros:**
- Preserves intuitive Job-First pattern
- Solves deadlock issue
- Backward compatible with existing diagrams
- Clear execution semantics

**Cons:**
- More complex implementation
- Requires execution count tracking
- Need to distinguish edge types

### Option D: Explicit Loop Constructs
Introduce dedicated loop nodes (ForLoop, WhileLoop, DoWhileLoop)

**Pros:**
- Clear loop semantics
- No ambiguity
- Familiar to programmers

**Cons:**
- Major breaking change
- Requires diagram migration
- More complex node types
- Less flexible than current approach

## 4. Detailed Analysis of Recommended Solution (Option C)

### Implementation Strategy

#### Phase 1: Edge Classification
```python
def classify_edge(edge):
    if edge.source_output in ["condtrue", "condfalse"]:
        return EdgeType.LOOP_BACK
    return EdgeType.NORMAL
```

#### Phase 2: Modified Dependency Check
```python
def _check_dependencies(self, node, edges, states, context):
    if node.type == NodeType.CONDITION:
        return any(satisfied(e) for e in edges)  # Keep ANY logic
    
    # Separate edge types
    normal_edges = [e for e in edges if not is_loop_back(e)]
    loop_edges = [e for e in edges if is_loop_back(e)]
    
    # Check execution count
    exec_count = context.get_node_execution_count(node.id)
    
    if exec_count == 0:
        # First execution: only check normal edges
        return all(satisfied(e) for e in normal_edges)
    else:
        # Subsequent: need at least one loop edge
        return any(satisfied(e) for e in loop_edges)
```

### Edge Cases to Consider

1. **Multiple Condition Nodes**
   - Node receives from multiple conditions
   - Each condition controls different loop
   - Solution: Group by source and check independently

2. **Nested Loops**
   - Inner and outer loop conditions
   - Multiple loop-back paths
   - Solution: Track which loop is active

3. **Mixed Dependencies**
   - Node has both loop and non-loop inputs
   - Example: Data input + loop control
   - Solution: Require non-loop on first run, any loop edge after

## 5. Migration Path

### Step 1: Update dynamic_order_calculator.py
- Implement smart loop handling
- Add execution count awareness
- Preserve backward compatibility

### Step 2: Testing
- Test with existing diagrams:
  - `simple_iter` (basic loop)
  - `nested_loops` (if exists)
  - `conditional_branches` (no loops)
- Ensure no regression

### Step 3: Documentation
- Update light diagram guide
- Add loop examples
- Document edge semantics

## 6. Alternative Considerations

### Loop Detection Algorithm
Instead of relying on edge naming (`condtrue`/`condfalse`), detect loops structurally:
```python
def detect_loops(diagram):
    # Use graph algorithms to find cycles
    # Mark edges that are part of cycles
    # More robust but computationally expensive
```

### Explicit Loop Annotation
Allow users to mark edges as loop-back:
```yaml
connections:
- from: condition_condfalse
  to: printer
  is_loop_back: true  # Explicit annotation
```

## 7. Decision Criteria

| Criteria | Option A | Option B | Option C | Option D |
|----------|----------|----------|----------|----------|
| Intuitiveness | ❌ | ✅ | ✅ | ✅ |
| Implementation Complexity | ✅ | ❌ | 🔶 | ❌ |
| Backward Compatibility | ❌ | ❌ | ✅ | ❌ |
| Flexibility | 🔶 | 🔶 | ✅ | 🔶 |
| Performance | ✅ | ✅ | ✅ | 🔶 |

## 8. Recommendation

**Implement Option C: Smart Loop Handling**

### Rationale
1. Preserves intuitive Job-First pattern that users expect
2. Solves the immediate deadlock issue
3. Maintains backward compatibility
4. Reasonable implementation complexity
5. Clear semantics for execution

### Next Steps
1. Update `_check_dependencies` in `dynamic_order_calculator.py`
2. Add loop-back edge detection
3. Implement execution-count-aware logic
4. Test with all example diagrams
5. Update documentation

## 9. Open Questions for Team Discussion

1. **Edge Naming Convention**: Should we rely on `condtrue`/`condfalse` naming or implement structural loop detection?

2. **Execution Limits**: Should we have built-in infinite loop protection beyond max_iteration?

3. **Loop Variables**: Should loop iteration count be accessible to nodes within the loop?

4. **Break/Continue**: Should we support early loop exit mechanisms?

5. **Parallel Loops**: How should we handle nodes that participate in multiple independent loops?

## 10. Example Test Cases

### Test 1: Simple Loop (simple_iter)
- Verify printer executes on start
- Verify condition evaluates after printer
- Verify loop continues on condfalse
- Verify loop exits on condtrue

### Test 2: No-Loop Conditional
- Verify normal conditional branches work
- No regression in non-loop scenarios

### Test 3: Nested Loops
- Create test diagram with nested loops
- Verify inner and outer loops work correctly

### Test 4: Multiple Inputs
- Node with loop-back + data input
- Verify correct triggering logic

---

**Author**: Assistant
**Date**: 2025-09-01
**Status**: For Team Discussion
**Priority**: High - Blocking loop execution


---

Short version: your analysis is spot-on, and Option C (“smart loop handling”) is the right direction. I’d tighten it a bit so it’s **structural** (no naming guesses), **local** (only relaxes deps for true loop-backs), and **future-proof** (moves us toward clear control/data semantics). Below is exactly how I’d change the current code, why it fixes `simple_iter`, and how to guard against edge cases.

---

# What’s good in your write-up

* You correctly identified the deadlock: non-condition nodes use **AND** over “all incoming edges,” so `printer` waits for both `start→printer` and `condition_condfalse→printer`, but `condition` can’t run until `printer` runs once. Classic do-while loop stall.
* Option C preserves the intuitive **job-first** (“do-while”) mental model and is backwards-compatible.

# The one thing to upgrade

Don’t decide “loop-back” by handle names (`condtrue`/`condfalse`). Some nodes sit after a condition (forward branch) while others close the loop (backedge). If we blindly ignore all condition edges on the first pass, we’ll accidentally fire *branch children* of a condition before the condition runs. So: **detect backedges structurally**.

> **Definition**: an incoming edge from Condition node `C → N` is a **loop-back** iff there is a path `N ⇒ … ⇒ C` in the graph.

That’s cheap to compute and cache, and it cleanly distinguishes “forward branch” vs “loop-back”.

---

# Minimal, surgical fix (in today’s code)

You already have everything needed:

* `dynamic_order_calculator.py` has `_check_dependencies(...)`.
* `ExecutionContext.get_node_execution_count(node_id)` exists.
* Condition branch choice is stored in `context.get_variable(f"branch[{condition_id}]")`.

### 1) Add a tiny reachability helper (with cache)

```python
# dynamic_order_calculator.py (class DomainDynamicOrderCalculator)

def __init__(self):
    self._reachability_cache: dict[tuple[int, str, str], bool] = {}

def _has_path(self, diagram, src_id, dst_id) -> bool:
    # cache by object id to avoid needing diagram.id
    key = (id(diagram), src_id, dst_id)
    if key in self._reachability_cache:
        return self._reachability_cache[key]

    adj = defaultdict(list)
    for e in diagram.edges:
        adj[e.source_node_id].append(e.target_node_id)

    seen, stack = set(), [src_id]
    ok = False
    while stack:
        n = stack.pop()
        if n == dst_id:
            ok = True
            break
        if n in seen: 
            continue
        seen.add(n)
        stack.extend(adj.get(n, []))

    self._reachability_cache[key] = ok
    return ok
```

### 2) Classify conditional incoming edges into forward vs loop-back

Inside `_check_dependencies(...)` (after you split `conditional_edges` and `non_conditional_edges`):

```python
exec_count = context.get_node_execution_count(node.id)

loop_back_edges = []
forward_cond_edges = []
for edge in conditional_edges:
    # loop-back if target can reach this condition
    if self._has_path(diagram, node.id, edge.source_node_id):
        loop_back_edges.append(edge)
    else:
        forward_cond_edges.append(edge)

# 1) All non-conditional edges must be satisfied (as today)
for edge in non_conditional_edges:
    if not self._is_dependency_satisfied(edge, node_states, context):
        return False

# 2) Forward condition edges must be satisfied (as today)
if forward_cond_edges:
    edges_by_cond = defaultdict(list)
    for e in forward_cond_edges:
        edges_by_cond[e.source_node_id].append(e)

    for cond_id, edges in edges_by_cond.items():
        source_state = node_states.get(cond_id)
        if not source_state or source_state.status == Status.PENDING:
            return False
        if not any(self._is_dependency_satisfied(e, node_states, context) for e in edges):
            return False

# 3) Loop-back edges:
#    - First execution: ignore them (do-while semantics)
#    - Subsequent executions: require that the active loop-back branch is satisfied
if loop_back_edges:
    if exec_count > 0:
        edges_by_cond = defaultdict(list)
        for e in loop_back_edges:
            edges_by_cond[e.source_node_id].append(e)
        for cond_id, edges in edges_by_cond.items():
            source_state = node_states.get(cond_id)
            if not source_state or source_state.status == Status.PENDING:
                # If the condition hasn't (re)run yet in this round, we can't continue the loop
                return False
            if not any(self._is_dependency_satisfied(e, node_states, context) for e in edges):
                return False
# If we got here, deps are satisfied
return True
```

> This exact change unblocks `printer` in `examples/simple_diagrams/simple_iter.light.yaml`:
>
> * First time, `exec_count == 0` → we ignore `condition→printer` loop-back, so `printer` runs.
> * After `printer` completes and `condition` executes, subsequent passes require the active loop-back branch, so the loop continues/terminates correctly.

### 3) (Optional) Add debug logs for transparency

Log *why* a node is blocked (missing which edge/branch). This makes diagram hangs self-explanatory in `--debug`.

---

# Why this is safer than “ignore all conditional edges on first run”

* It only relaxes **true backedges**, never forward branches; so we don’t trigger children of a condition prematurely.
* It composes well with nested and multiple loops—classification happens per incoming condition source.

---

# Edge cases & how this handles them

1. **Nodes that mix data inputs + loop control**
   ✔ Non-conditional (data) inputs still gate **every** execution. Only the *control* (loop-back) is relaxed on the first run.

2. **Nested loops**
   ✔ Each incoming condition source is checked independently; a loop-back from the inner condition is ignored on the very first execution of that node, but required thereafter.

3. **Multiple condition sources, some forward, some back**
   ✔ Forward ones are always enforced; backedges follow the first-run relax rule.

4. **Infinite loops**
   You already have `max_iteration` on `person_job`. Keep that guard, and consider adding a global `max_total_steps` per run to fail fast with a clear error that prints the smallest cycle.

---

# Medium-term: make the semantics explicit (clean model)

If you want to make this rock-solid and easier to reason about later:

* **Introduce control vs data edges.**
  Treat edges from `Start` and `Condition(cond*)` as **control**; others default to **data**.
  **Rule**: A node fires when **all required data** deps are present **and** at least one control signal is present.

  * First fire: control can be `Start→N` *or* another upstream control.
  * Loop continuation: control is the active loop-back branch.

* **SCC condensation** (optional enhancement).
  Precompute strongly connected components; any backedge shows up as an intra-SCC edge. Use that to label loop-back edges at compile time (so runtime is trivial and fast).

* **Add explicit “Merge” semantics.**
  Nodes with multiple control inputs behave like a Merge: “fire when a control token arrives, provided all required data deps are satisfied.” This matches TF/Beam/Dataflow mental models and removes ambiguity in user diagrams.

---

# Tests to add (fast, deterministic)

1. **Simple do-while (`simple_iter`)**

   * `printer` runs once before `condition`
   * On `condfalse`, `printer` runs again; on `condtrue`, loop exits and `ask→endpoint` runs.

2. **Pure forward branch**
   Node that only has `condition→child` edges must **not** run before condition executes.

3. **Mixed deps**
   Node with data input from `A` and loop-back from `condition`: ensure first run waits for `A` but not for `condition`.

4. **Nested loops**
   Two conditions in different cycles both targeting a node; verify first run + subsequent loop behavior is sane.

---

# Concrete next steps (file-level)

1. Implement `_has_path(...)` and the `_check_dependencies(...)` split **(dipeo/domain/execution/dynamic\_order\_calculator.py)**.
2. Add concise debug logs explaining blocks and chosen branches.
3. Add unit tests for the 4 cases above (fixtures under `examples/simple_diagrams` are fine).
4. (Optional) Emit a one-time warning when a node is classified with both forward and loop-back conditional edges; include IDs in the message to help users simplify their graphs.

If you want, I can draft the exact patch as a diff against your current file structure, plus a small test harness you can run with `dipeo run examples/simple_iter --light --debug`.
