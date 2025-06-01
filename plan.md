# DiPeO Web App Code Consolidation Plan

## Executive Summary

The `apps/web` codebase contains significant redundancy and opportunities for consolidation. This plan identifies 19 specific areas for improvement that would reduce codebase size by approximately 25-30% while improving maintainability and developer experience.

## Key Findings

### Code Duplication Metrics
- **12+ node components** following nearly identical patterns (80% code overlap)
- **3 separate property form hooks** with overlapping functionality  
- **2 duplicate nodeHelpers.js** files with different utilities
- **7+ base executor classes** with similar validation patterns
- **Extensive form components** that should be shared across features

## Consolidation Roadmap

### ✅ Phase 1: High-Impact, Low-Risk (COMPLETED)

#### Summary of Completed Tasks:
- **1.1 Merged duplicate nodeHelpers files** - Created unified `/shared/utils/nodeHelpers.ts`, removed 2 files
- **1.2 Removed ContextMenu wrapper** - Integrated logic into base component, removed 1 file  
- **1.3 Moved generic form components** - Created `/shared/components/forms/`, improved reusability
- **Total savings**: ~290 lines consolidated, 3 files removed

### Phase 2: Medium-Impact, Medium-Risk (3-5 days)

#### 2.1 **Consolidate Property Form Hooks** ⭐️ PRIORITY 1
**Current State:**
```typescript
// 3 separate hooks with overlapping functionality
/features/diagram/hooks/ui-hooks/usePropertyForm.ts (base - 80 lines)
/features/properties/hooks/usePropertyForm.ts (wrapper - 30 lines)  
/features/properties/hooks/usePropertyFormState.ts (advanced - 150 lines)
```
**Solution:**
```typescript
// New consolidated hook in /shared/hooks/usePropertyForm.ts
export function usePropertyForm<T>(options: {
  initialData: T;
  nodeId?: string;
  enableValidation?: boolean;
  enableAutoSave?: boolean;
  enableStoreIntegration?: boolean;
  onUpdate?: (data: T) => void;
}) {
  // Unified implementation combining all three hooks
}
```
**Estimated savings:** 80 lines, 2 files removed, simpler API

#### 2.2 **Create ConfigurableNodeWrapper Component** ⭐️ PRIORITY 2
**Current State:**
```typescript
// 7+ node components with 80% identical code
StartNode.tsx (40 lines)
JobNode.tsx (60 lines)  
PersonJobNode.tsx (80 lines)
ConditionNode.tsx (70 lines)
DBNode.tsx (50 lines)
EndpointNode.tsx (45 lines)
PersonBatchJobNode.tsx (75 lines)
```
**Solution:**
```typescript
// New unified component
const ConfigurableNodeWrapper: React.FC<{
  id: string;
  data: any;
  selected: boolean;
  config: NodeConfig;
}> = ({ id, data, selected, config }) => {
  const specificLogic = useNodeTypeLogic(config.type);
  
  return (
    <GenericNode id={id} data={data} selected={selected} nodeType={config.reactFlowType}>
      <NodeContent config={config} data={data} {...specificLogic} />
    </GenericNode>
  );
};
```
**Estimated savings:** 300+ lines, 6+ files reduced to 1-2 components

#### 2.3 **Merge Node Operation Hooks** ⭐️ PRIORITY 3
**Current State:**
```
/features/nodes/hooks/useNodeOperations.ts (60 lines)
/features/nodes/hooks/useNodeDrag.ts (40 lines)
/features/nodes/hooks/useNodeConfig.ts (30 lines)
```
**Solution:**
```typescript
// Consolidated hook in /shared/hooks/useNode.ts
export function useNode(nodeId: string) {
  const operations = useNodeOperations(nodeId);
  const drag = useNodeDrag(nodeId);
  const config = useNodeConfig(nodeId);
  
  return {
    ...operations,
    ...drag,
    ...config,
    // Provide grouped access for selective usage
    operations,
    drag,
    config
  };
}
```
**Estimated savings:** 50 lines, simpler import patterns

### Phase 3: Advanced Consolidation (5-7 days)

#### 3.1 **Enhanced Executor Base Classes** ⭐️ PRIORITY 2
**Current State:**
```typescript
// Similar patterns across 7+ executor classes
ClientSafeExecutor, ServerOnlyExecutor (base classes)
StartExecutor, JobExecutor, ConditionExecutor... (implementations)
```
**Solution:**
```typescript
// Enhanced base classes with common patterns
export abstract class EnhancedClientSafeExecutor extends ClientSafeExecutor {
  protected validateCommonInputs(inputs: any): ValidationResult {
    // Common validation patterns extracted
  }
  
  protected createStandardResult(data: any): ExecutionResult {
    // Standard result creation patterns
  }
  
  protected handleStandardErrors(error: Error): void {
    // Common error handling
  }
}
```
**Estimated savings:** 100+ lines of duplicate validation/error handling

#### 3.2 **Generic Form Field Renderer** ⭐️ PRIORITY 3
**Current State:**
```typescript
// Specialized form components for each field type
PersonSelectionField, LabelPersonRow, IterationCountField
```
**Solution:**
```typescript
// Configuration-driven field renderer
const FormFieldRenderer: React.FC<{
  fieldConfig: FieldConfig;
  value: any;
  onChange: (value: any) => void;
}> = ({ fieldConfig, value, onChange }) => {
  switch (fieldConfig.type) {
    case 'person-selection':
      return <PersonSelectionRenderer {...fieldConfig} value={value} onChange={onChange} />;
    // ... other field types
  }
};
```
**Estimated savings:** 150+ lines, more maintainable field system

#### 3.3 **Store Consolidation Opportunities** ⭐️ PRIORITY 4
**Current Assessment:**
- **consolidatedDiagramStore**: Well-designed, no major issues (290 lines)
- **consolidatedUIStore**: Good separation of concerns (95 lines)
- **executionStore**: Simple and focused (63 lines)
- **historyStore**: Complex but necessary for undo/redo (229 lines)

**Minor Optimizations:**
- Extract CRUD utilities from consolidatedDiagramStore to shared utilities
- Consider splitting large `addNode` method into smaller functions
- **Estimated savings:** 50+ lines via extraction

### Phase 4: Advanced Optimizations (3-4 days)

#### 4.1 **Type Definition Reorganization** ⭐️ PRIORITY 3
**Current State:**
```
/shared/types/ (main type definitions)
/features/conversation/types.ts (feature-specific)
```
**Solution:**
- Move broadly useful types to shared
- Create domain-specific type files (messaging.ts, execution.ts)
- **Estimated impact:** Better type reusability, reduced imports

#### 4.2 **Shared Component Library Enhancement** ⭐️ PRIORITY 4
**Create New Shared Categories:**
```
/shared/components/
├── forms/          # Generic form components
├── feedback/       # Loading, error states  
├── data/          # Data display components
└── layout/        # Layout utilities
```

## Implementation Priority Matrix

| Task | Impact | Risk | Effort | Priority |
|------|--------|------|--------|----------|
| Merge nodeHelpers files | High | Low | 1h | P1 |
| Remove ContextMenu wrapper | High | Low | 2h | P1 |
| Consolidate property hooks | High | Medium | 1d | P1 |
| Move form components to shared | Medium | Low | 4h | P2 |
| Create ConfigurableNodeWrapper | High | Medium | 2d | P2 |
| Enhanced executor base classes | Medium | Medium | 1.5d | P2 |
| Merge node operation hooks | Medium | Low | 4h | P3 |
| Generic form field renderer | Medium | High | 2d | P3 |
| Type reorganization | Low | Low | 1d | P3 |
| Store optimizations | Low | Low | 4h | P4 |

## Expected Outcomes

### Quantitative Benefits
- **Files Reduced:** ~12-15 files eliminated
- **Lines of Code:** 25-30% reduction in component/hook files
- **Bundle Size:** Estimated 10-15% reduction through better tree shaking
- **Import Statements:** 40% reduction in component imports

### Qualitative Benefits
- **Developer Experience:** Simpler API surface, fewer files to navigate
- **Maintainability:** Single source of truth for common patterns
- **Consistency:** Unified patterns across features
- **Performance:** Reduced bundle duplication, better code splitting

## Risk Mitigation

### Phase 1 (Low Risk)
- Simple file merges and moves
- Full test coverage for moved utilities
- Gradual migration with deprecation warnings

### Phase 2 (Medium Risk)
- Feature flags for new consolidated components
- A/B testing between old and new hook implementations
- Rollback plan for each major change

### Phase 3 (Higher Risk)
- Extensive testing of executor changes
- Staged rollout of generic field renderer
- Backup branches for complex refactors

## Implementation Guidelines

### Code Quality Standards
1. **Zero Breaking Changes:** All consolidations must maintain API compatibility
2. **Test Coverage:** Maintain or improve test coverage for all changes
3. **Performance:** Bundle analysis before/after each phase
4. **Documentation:** Update component documentation and examples

### Migration Strategy
1. **Parallel Implementation:** Build new consolidated components alongside existing ones
2. **Gradual Migration:** Migrate features one at a time
3. **Deprecation Warnings:** Provide clear migration paths
4. **Performance Monitoring:** Track bundle size and runtime performance

## Success Metrics

### Phase 1 Completion (Week 1)
- [x] 2 duplicate utility files merged
- [x] 1 unnecessary wrapper removed  
- [x] Basic form components moved to shared
- [x] Bundle size reduction: 5-8%

### Phase 2 Completion (Week 3)
- [ ] Property hooks consolidated
- [ ] Node components reduced from 7+ to 2
- [ ] Node operation hooks merged
- [ ] Bundle size reduction: 15-20%

### Phase 3 Completion (Week 5)
- [ ] Enhanced executor base classes implemented
- [ ] Generic form field renderer functional
- [ ] Bundle size reduction: 25-30%

## Next Steps

1. **Phase 1 Complete:** Low-risk consolidation tasks completed successfully
2. **Begin Phase 2:** Start with property form hooks consolidation
3. **Monitor Performance:** Check bundle size impact of Phase 1 changes
4. **Continuous Integration:** Ensure all changes pass existing tests
5. **Progress Tracking:** Weekly reviews of consolidation progress

This plan provides a systematic approach to reducing code redundancy while maintaining system stability and improving developer experience.