# DiPeO Project Todos

## Completed (2025-10-05)

### Metrics Tracking System Enhancement
All metrics tracking implementation tasks have been completed:
- ✅ Modified service.py to track API calls hierarchically using phase names like "memory_selection__api_call"
- ✅ Updated display.py to aggregate and display hierarchical phases with nested timing structure and overhead calculation
- ✅ Enhanced metrics_observer.py to preserve hierarchical phase names
- ✅ Tested implementation with simple_iter diagram
- ✅ Verified metrics breakdown output shows correct hierarchical display

**Impact**: The metrics system now correctly displays hierarchical timing structure, showing API calls within their execution context (memory_selection vs completion), accurate call counts, and overhead calculations for optimization targeting.

---

## Future Optimization Opportunities

Based on the enhanced metrics system, potential optimization areas:

1. **Memory Selection Preprocessing** (if metrics reveal slowness):
   - Reduce MEMORY_HARD_CAP (150 → 50-75)
   - More aggressive pre-filtering
   - Cache scoring results

2. **Prompt Building Optimization**:
   - Reduce snippet lengths
   - Simplify selection prompt
   - Cache prompt templates

3. **Parallel Processing**:
   - Verify nodes execute in parallel
   - Check if memory selection blocks parallelization
