"""Profile container initialization command."""

import asyncio
import click
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(project_root))

from dipeo.container import Container
from dipeo.container.utilities import init_resources, shutdown_resources
from dipeo.container.profiling import enable_profiling


@click.command()
@click.option('--profile', type=click.Choice(['full', 'edit', 'execution', 'analysis', 'cli']), 
              default='full', help='Container profile to use')
@click.option('--repeat', type=int, default=1, help='Number of times to repeat the profiling')
def profile_container(profile: str, repeat: int):
    """Profile container initialization performance."""
    async def run_profiling():
        times = []
        
        for i in range(repeat):
            with enable_profiling() as profiler:
                # Set profile before creating container
                Container.set_profile(profile)
                container = Container()
                
                # Initialize resources with profiling
                async with profiler.profile_async("Container.init_resources", profile=profile):
                    await init_resources(container)
                
                # Get results
                results = profiler.get_results()
                if results:
                    if i == 0:  # Print detailed results only for first run
                        profiler.print_results()
                    times.append(results.total_duration_ms())
                
                # Cleanup
                await shutdown_resources(container)
        
        if repeat > 1:
            avg_time = sum(times) / len(times)
            min_time = min(times)
            max_time = max(times)
            print(f"\n=== Summary (n={repeat}) ===")
            print(f"Average: {avg_time:.2f}ms")
            print(f"Min: {min_time:.2f}ms")
            print(f"Max: {max_time:.2f}ms")
    
    # Run the async function
    asyncio.run(run_profiling())


if __name__ == '__main__':
    profile_container()
