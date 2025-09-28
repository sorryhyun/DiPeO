# TODO

## IR builder re-architecture

**Observations**
- Backend, frontend, and strawberry builders all mix extraction, transformation, and assembly logic inside domain-specific modules.
- Cross-domain dependencies already exist (e.g. strawberry builder imports backend extractors and shared `TypeConverter` helpers), which makes the current separation feel arbitrary and hard to extend.
- Utility functions such as node spec extraction, domain model shaping, and GraphQL operation handling are duplicated with small variations, increasing coupling and cognitive load.

**Current responsibilities (catalogue)**
- _BackendIRBuilder (`ir_builders/backend_refactored.py`)_: orchestrates AST ingestion and glues together `extract_node_specs`, `extract_enums_all`, `extract_domain_models`, `extract_integrations`, `extract_conversions`, and `extract_typescript_indexes` from `backend_extractors.py`, then feeds results into `build_factory_data` / `build_conversions_data` from `backend_builders.py` before emitting a single IR payload with inline metadata. Maintains its own `TypeConverter` instance and touches environment (`DIPEO_BASE_DIR`) for filesystem lookups.
- _FrontendIRBuilder (`ir_builders/frontend.py`)_: keeps bespoke extract/transform helpers in the same file (`extract_node_configs`, `generate_field_configs`, `extract_graphql_queries`, `build_registry_data`, `generate_typescript_models`); writes a snapshot JSON to `projects/codegen/ir/frontend_ir.json`. Relies on shared `TypeConverter` utilities but otherwise duplicates node-spec parsing and GraphQL query handling.
- _StrawberryIRBuilder (`ir_builders/strawberry_refactored.py`)_: composes configuration loading, `extract_operations_from_ast` (`strawberry_extractors.py`), `extract_interfaces_from_ast` / `extract_enums_from_ast` / `extract_graphql_input_types_from_ast` (`utils.py`), and reuses backend `extract_node_specs`. Transforms data via `strawberry_transformers.py`, then assembles/validates IR through `strawberry_builders.py`. Also instantiates `StrawberryConfig` objects for disk-backed overrides.
- _Shared utilities (`ir_builders/utils.py`, `base.py`)_: house global type converters, case helpers, config loading, and minimal validation but offer no structured abstraction for step composition, so each builder curates its own mini-pipeline.

**Goals**
- Reorganize the IR build pipeline around shared stages (ingest -> extract -> transform -> assemble -> validate) instead of per-domain files.
- Make cross-cutting data producers (node specs, domain models, GraphQL operations, UI configs) reusable modules with clear contracts.
- Reduce the size and responsibility of the final builder classes so that adding a new output surface is mostly composition, not bespoke logic.

**Refactor plan**

_Phase 1 – Foundation_ ✅ COMPLETED
- ✅ Introduced `ir_builders/core/` package with:
  - `context.py` for build context/config + cached helpers (TypeConverter)
  - `steps.py` with BuildStep interface, PipelineOrchestrator, and StepRegistry
  - `base.py` with refactored BaseIRBuilder using the new step system
- ✅ Created reusable step modules under `ir_builders/modules/`:
  - `node_specs.py` (ExtractNodeSpecsStep, BuildNodeFactoryStep, BuildCategoryMetadataStep)
  - `domain_models.py` (ExtractDomainModelsStep, ExtractEnumsStep, ExtractIntegrationsStep, ExtractConversionsStep)
  - `graphql_operations.py` (ExtractGraphQLOperationsStep, BuildOperationStringsStep, GroupOperationsByEntityStep)
  - `ui_configs.py` (ExtractNodeConfigsStep, BuildNodeRegistryStep, GenerateFieldConfigsStep, GenerateTypeScriptModelsStep)

_Phase 2 – Adoption_ ✅ CORE COMPLETED, COMPATIBILITY ISSUES REMAIN
1. ✅ Re-implemented builder entry points in `ir_builders/builders/`:
   - Backend builder = node specs + domain models + conversions/integrations assembler + backend validator.
   - Strawberry builder = operations step + domain models step + node specs feed + GraphQL config assembler.
   - Frontend builder = node specs step + UI config/registry step + GraphQL operations step.
2. ✅ Provided targeted validators under `ir_builders/validators/`:
   - Base validator framework with ValidationResult and ValidationError
   - Domain-specific validators: BackendValidator, FrontendValidator, StrawberryValidator
   - Composite validator for combining multiple validators
3. ✅ Updated codegen workflow to use new builders:
   - ✅ Updated ir_registry.py to import new builders
   - ✅ Fixed async/await compatibility with IRBuilderPort interface
   - ✅ Basic code generation runs successfully
4. ⏳ After full parity is verified, deprecate legacy modules and update documentation

_Phase 3 – Fix Compatibility Issues_ ⏳ IN PROGRESS
**Issues found during `make codegen` (from server.log):**
1. **Strawberry builder validation errors:**
   - All GraphQL operations missing `query_string` field
   - BuildOperationStringsStep may not be generating query strings correctly
   - Need to ensure operations data includes query_string for each operation

2. **Template compatibility errors:**
   - `integrations.j2`: Expects dict with `.get()` method but receives list
     - Backend assembler may be passing wrong data structure for integrations
   - `generated_nodes.j2`: Expects object with `.imports` attribute
     - Node factory structure differs from template expectations

3. **Data structure mismatches:**
   - New builders produce different IR structure than templates expect
   - Need to either:
     a. Update templates to match new IR structure, OR
     b. Adjust builders to produce backward-compatible structure

**Action items:**
- [ ] Fix BuildOperationStringsStep to generate query_string for operations
- [ ] Ensure backend assembler provides integrations as expected structure
- [ ] Fix node_factory data structure to include imports attribute
- [ ] Run comprehensive test comparing old vs new IR outputs
- [ ] Update validators to be less strict during migration period
- [ ] Add integration tests that verify template rendering works

**Open questions / risks**
- Need to confirm there are no hidden runtime imports that expect current module paths; plan to provide deprecation shims during migration.
- Strawberry builder currently reads config from disk—decide whether that remains a direct dependency or becomes a configurable step.
- Ensure the pipeline remains async-friendly if future builders need async extraction work (e.g. loading additional metadata).

**Next validation steps**
- Add unit coverage for the new step modules (mock AST inputs) and integration tests that compare generated IR JSON to current snapshots for each builder.
- Test the refactored pipeline end-to-end by running `make codegen` and verifying no diff in generated artifacts before deleting legacy code.
