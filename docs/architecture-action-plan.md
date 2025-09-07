# DiPeO Architecture Action Plan

*Generated from TODO.md investigation - 2025-09-07*

## 🎯 Priority 1: Complete Mixin Migration (Week 1)

### Services to Migrate
1. `EnvironmentAPIKeyService` → Use `LoggingMixin, InitializationMixin`
2. `APIKeyService` → Use `LoggingMixin, InitializationMixin`  
3. `ParserService` → Use `LoggingMixin, InitializationMixin, CachingMixin`
4. `IntegratedApiService` → Use `LoggingMixin, InitializationMixin, ConfigurationMixin`

### Migration Steps
```python
# Before (BaseService)
class APIKeyService(BaseService):
    def __init__(self):
        super().__init__()
        
# After (Mixins)
class APIKeyService(LoggingMixin, InitializationMixin):
    def __init__(self):
        LoggingMixin.__init__(self)
        InitializationMixin.__init__(self)
```

### Success Criteria
- [ ] All 4 services migrated
- [ ] BaseService class removed
- [ ] All tests passing
- [ ] No performance regression

## 🎯 Priority 2: Document Code Generation (Week 1)

### Create Documentation
```markdown
# Code Generation Workflow

## Directory Structure
- `dipeo/diagram_generated/` - Active code
- `dipeo/diagram_generated_staged/` - Review staging

## Commands
1. `make codegen` - Generate to staged
2. `make diff-staged` - Review changes
3. `make apply-syntax-only` - Apply without type checking
4. `make apply` - Apply with full validation
```

### Files to Update
- [ ] `/docs/projects/code-generation-workflow.md` (create)
- [ ] `/CLAUDE.md` (add workflow section)
- [ ] `/Makefile` (add inline comments)

## 🎯 Priority 3: Clean Up Event System (Week 2)

### Tasks
1. **Remove ports.py wrapper**
   - Update all imports from `ports` to `unified_ports`
   - Delete `/dipeo/domain/ports.py`
   
2. **Update imports** (28 files)
   ```python
   # Change from:
   from dipeo.domain.ports import EventBus
   
   # To:
   from dipeo.domain.unified_ports import EventBus
   ```

## 🎯 Priority 4: Add Persistence (Week 2-3)

### Implement SQLite Repository
```python
# New file: dipeo/infrastructure/repositories/implementations/sqlite/
class SqliteConversationRepository(ConversationRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    async def save(self, conversation: Conversation):
        # SQLite implementation
```

### Update Service Registry
```python
# infrastructure_container.py
repository_type = config.get("repository_type", "memory")
if repository_type == "sqlite":
    repo = SqliteConversationRepository(config["db_path"])
else:
    repo = InMemoryConversationRepository()
```

## 📊 Metrics Tracking

### Before Migration
| Metric | Current |
|--------|---------|
| BaseService Users | 4 |
| Mixin Users | 2 |
| Test Coverage | 72% |
| Import Depth | 3-4 |

### Target After Migration  
| Metric | Target |
|--------|--------|
| BaseService Users | 0 |
| Mixin Users | 6 |
| Test Coverage | 80%+ |
| Import Depth | 2-3 |

## ✅ Quick Wins (Can Do Now)

```bash
# Remove unused imports
find . -name "*.py" -exec autoflake --remove-unused-variables --in-place {} \;

# Delete empty __init__.py files
find . -name "__init__.py" -size 0 -delete

# Remove commented code
grep -r "^#.*TODO\|FIXME\|XXX" --include="*.py" 

# Consolidate error messages
grep -r "raise.*Error" --include="*.py" | sort | uniq -c | sort -rn
```

## 🚫 Don't Do Yet

1. **Don't optimize adapters** - They work correctly
2. **Don't change repository interfaces** - Add new implementations instead
3. **Don't refactor handlers** - Focus on services first
4. **Don't modify generated code** - Only change generators

## 📅 Timeline

### Week 1
- Mon-Tue: Migrate 2 services
- Wed-Thu: Migrate 2 services, remove BaseService
- Fri: Document code generation

### Week 2  
- Mon-Tue: Clean up event system
- Wed-Fri: Implement SQLite repository

### Week 3
- Mon-Tue: Testing and validation
- Wed-Thu: Performance benchmarking
- Fri: Documentation updates

## 🔄 Daily Checklist

- [ ] Run tests after each change
- [ ] Update migration tracking
- [ ] Commit with descriptive messages
- [ ] Review performance metrics
- [ ] Update this document

## 📈 Success Metrics

1. **Code Quality**
   - Zero BaseService dependencies
   - Consistent mixin usage
   - Clean import structure

2. **Performance**
   - No initialization regression
   - Memory usage stable
   - Event latency unchanged

3. **Developer Experience**  
   - Clear documentation
   - Obvious patterns
   - Easy onboarding

## 🚀 Next Phase (After Week 3)

Once migration complete:
1. Optimize mixin combinations
2. Add more repository implementations (Redis, PostgreSQL)
3. Improve adapter testing
4. Flatten import structure
5. Add architecture decision records (ADRs)

---

*Use this action plan alongside the detailed investigation report (architecture-investigation-report.md)*
