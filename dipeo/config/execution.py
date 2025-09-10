"""Execution and diagram processing configuration for DiPeO."""

# Batch execution settings
BATCH_MAX_CONCURRENT = 10  # Maximum concurrent executions for batch processing
BATCH_SIZE = 100  # Maximum items to process in one batch

# Diagram validation constraints
DIAGRAM_MAX_PARALLEL_NODES = 10  # Maximum number of parallel nodes in a diagram
DIAGRAM_MAX_RECURSION_DEPTH = 50  # Maximum recursion depth for diagram execution
DIAGRAM_MAX_TOTAL_NODES = 1000  # Maximum total nodes allowed in a diagram

# Sub-diagram execution settings
SUB_DIAGRAM_MAX_CONCURRENT = 10  # Maximum concurrent sub-diagram executions
SUB_DIAGRAM_BATCH_SIZE = 100  # Maximum sub-diagrams to process in one batch
