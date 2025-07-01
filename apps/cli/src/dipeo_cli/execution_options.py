from dataclasses import dataclass
from enum import Enum


class ExecutionMode(Enum):
    STANDARD = "standard"
    MONITOR = "monitor"
    HEADLESS = "headless"
    CHECK = "check"


@dataclass
class ExecutionOptions:
    mode: ExecutionMode = ExecutionMode.STANDARD
    debug: bool = False
    keep_server: bool = False
    timeout: int = 300  # 5 minutes
    output_file: str | None = None
    diagram_file: str | None = None
    local: bool = False  # Use local execution without server
    format: str | None = None  # Diagram format: native, light, readable


def parse_run_options(args: list[str]) -> ExecutionOptions:
    """Parse command line options for run command"""
    options = ExecutionOptions()

    for arg in args:
        if arg == "--monitor":
            options.mode = ExecutionMode.MONITOR
        elif arg == "--mode=headless":
            options.mode = ExecutionMode.HEADLESS
        elif arg == "--mode=check":
            options.mode = ExecutionMode.CHECK
        elif arg == "--debug":
            options.debug = True
        elif arg == "--keep-server":
            options.keep_server = True
        elif arg == "--local":
            options.local = True
        elif arg.startswith("--format="):
            format_value = arg.split("=")[1].lower()
            if format_value in ["native", "light", "readable"]:
                options.format = format_value
            else:
                print(f"Error: Invalid format '{format_value}'. Supported formats: native, light, readable")
        elif arg.startswith("--timeout="):
            try:
                options.timeout = int(arg.split("=")[1])
            except ValueError:
                print("Error: Invalid timeout value. Using default.")
        elif not arg.startswith("--"):
            options.output_file = arg

    return options
