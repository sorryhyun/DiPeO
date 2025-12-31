# ClaudeWorld Gameplay Turn - DiPeO Visual Prototype

This example demonstrates how to represent ClaudeWorld's multi-agent TRPG orchestration
system as a DiPeO light diagram.

## What is ClaudeWorld?

ClaudeWorld is a turn-based text adventure (TRPG) where AI agents collaborate to create
and run interactive worlds. It uses a **2-cell tape architecture**:

1. **Cell 1: NPC Reactions** - All NPCs at the player's location react concurrently
2. **Cell 2: Action Manager** - Interprets player action, coordinates sub-agents, generates narration

## DiPeO Diagram Structure

```
                                    ┌─────────────────┐
                                    │   Start Node    │
                                    │  (game state)   │
                                    └────────┬────────┘
                                             │
                            ┌────────────────┼────────────────┐
                            ▼                                  ▼
                ┌───────────────────────┐         ┌───────────────────────┐
                │   NPC Reactions       │         │   (context passed     │
                │   (sub_diagram)       │         │    directly)          │
                │   batch_parallel      │         │                       │
                └───────────┬───────────┘         └───────────┬───────────┘
                            │                                  │
                            └────────────────┬─────────────────┘
                                             ▼
                                ┌───────────────────────┐
                                │   Action Manager      │
                                │   (person_job)        │
                                │   Structured output   │
                                └───────────┬───────────┘
                                             │
                                             ▼
                                ┌───────────────────────┐
                                │   Parse Response      │
                                │   (code_job)          │
                                └───────────┬───────────┘
                                             │
                                             ▼
                                ┌───────────────────────┐
                                │   Format Output       │
                                │   (code_job)          │
                                └───────────┬───────────┘
                                             │
                                             ▼
                                ┌───────────────────────┐
                                │   Save Result         │
                                │   (endpoint)          │
                                └───────────────────────┘
```

## Files

| File | Description |
|------|-------------|
| `gameplay_turn.light.yaml` | Main diagram - full gameplay turn orchestration |
| `npc_reaction.light.yaml` | Sub-diagram - individual NPC reaction (called in batch) |

## Key Mappings

| ClaudeWorld Concept | DiPeO Equivalent |
|---------------------|------------------|
| 2-cell tape | Sequential node execution |
| Concurrent NPC reactions | `sub_diagram` with `batch_parallel: true` |
| Task(sub-agent) | `sub_diagram` node |
| Hidden agents | No direct equivalent (visual prototype) |
| MCP tools (change_stat, travel) | Embedded in structured JSON output |
| narration() tool | Parsed from `person_job` output |
| suggest_options() | Parsed from `person_job` output |

## How Tool Calls are Handled

Since DiPeO's `person_job` doesn't have native tool calling like Claude's MCP tools,
we use a **prompt-only approach**:

1. The Action Manager's prompt describes the expected output format (JSON)
2. The LLM outputs structured data including:
   - `narration` - The visible narrative
   - `stat_changes` - Mechanical effects (HP, stamina, etc.)
   - `suggestions` - Next action options
   - `ruling` - The adjudication outcome
3. A `code_job` parses the JSON to extract these components

This is a **visual prototype** - it demonstrates the flow without implementing
actual game state persistence.

## Running the Example

```bash
# Run the gameplay turn
dipeo run examples/claudeworld/gameplay_turn --light --debug --timeout=60

# Output will be saved to temp/claudeworld_turn_result.md
```

## Customizing

### Change the Player Action

Edit `gameplay_turn.light.yaml` and modify the `custom_data` in the Start node:

```yaml
custom_data:
  player_action: "I try to negotiate with the goblin"
  # ... other state
```

### Add More NPCs

Add entries to the `npcs` array:

```yaml
npcs:
  - name: "Goblin"
    personality: "Aggressive, cowardly when outnumbered"
    disposition: "hostile"
  - name: "Mysterious Stranger"
    personality: "Enigmatic, speaks in riddles"
    disposition: "neutral"
```

### Modify the Action Manager's Behavior

Edit the `ActionManager` person's `system_prompt` to change adjudication style.

## Limitations

1. **No persistent state**: This is a single-turn prototype
2. **No hidden messages**: All outputs are visible (unlike ClaudeWorld's hidden cells)
3. **No dynamic sub-agents**: ClaudeWorld uses Claude Agent SDK's Task tool for
   dynamic sub-agent invocation; DiPeO uses pre-defined sub_diagram nodes
4. **Tool simulation**: Tool calls are simulated via structured output, not native MCP

## See Also

- [ClaudeWorld Repository](https://github.com/xxx/claudecodeworld)
- [DiPeO Light Diagram Guide](../../docs/formats/comprehensive_light_diagram_guide.md)
- [Sub-Diagram Documentation](../../docs/formats/comprehensive_light_diagram_guide.md#8-sub_diagram-node)
