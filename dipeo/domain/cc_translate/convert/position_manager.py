"""Position management for nodes in DiPeO diagrams.

This module handles node positioning logic including layout algorithms
and position calculations for diagram visualization.
"""

from typing import Optional


class PositionManager:
    """Manages node positioning for DiPeO diagram layout."""

    def __init__(self, initial_x: int = 100, initial_y: int = 100):
        """Initialize the position manager.

        Args:
            initial_x: Starting X coordinate for nodes
            initial_y: Starting Y coordinate for nodes
        """
        self.initial_x = initial_x
        self.initial_y = initial_y
        self.node_counter = 0
        self.current_x = initial_x
        self.current_y = initial_y

    def reset(self):
        """Reset position manager to initial state."""
        self.node_counter = 0
        self.current_x = self.initial_x
        self.current_y = self.initial_y

    def get_next_position(self) -> dict[str, int]:
        """Calculate position for the next node.

        Returns:
            Dictionary with x and y coordinates
        """
        self.node_counter += 1

        # Calculate position with horizontal spread and vertical rows
        x = 300 + (self.node_counter * 50) % 800
        y = 100 + (self.node_counter // 10) * 150

        return {"x": x, "y": y}

    def get_start_position(self) -> dict[str, int]:
        """Get the position for the start node.

        Returns:
            Dictionary with x and y coordinates for start node
        """
        return {"x": self.initial_x, "y": self.initial_y}

    def get_position_for_index(self, index: int) -> dict[str, int]:
        """Calculate position for a specific node index.

        Args:
            index: The node index to calculate position for

        Returns:
            Dictionary with x and y coordinates
        """
        x = 300 + (index * 50) % 800
        y = 100 + (index // 10) * 150

        return {"x": x, "y": y}

    def set_custom_position(self, x: int, y: int):
        """Set a custom position for special nodes.

        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.current_x = x
        self.current_y = y

    @property
    def current_position(self) -> dict[str, int]:
        """Get the current position without incrementing counter.

        Returns:
            Dictionary with current x and y coordinates
        """
        return {"x": self.current_x, "y": self.current_y}

    def increment_counter(self) -> int:
        """Increment and return the node counter.

        Returns:
            The incremented node counter
        """
        self.node_counter += 1
        return self.node_counter


class GridPositionManager(PositionManager):
    """Alternative position manager using grid-based layout."""

    def __init__(
        self,
        initial_x: int = 100,
        initial_y: int = 100,
        grid_width: int = 5,
        cell_width: int = 200,
        cell_height: int = 150,
    ):
        """Initialize grid-based position manager.

        Args:
            initial_x: Starting X coordinate
            initial_y: Starting Y coordinate
            grid_width: Number of columns in grid
            cell_width: Width of each grid cell
            cell_height: Height of each grid cell
        """
        super().__init__(initial_x, initial_y)
        self.grid_width = grid_width
        self.cell_width = cell_width
        self.cell_height = cell_height

    def get_next_position(self) -> dict[str, int]:
        """Calculate position for the next node using grid layout.

        Returns:
            Dictionary with x and y coordinates
        """
        col = self.node_counter % self.grid_width
        row = self.node_counter // self.grid_width

        x = self.initial_x + (col * self.cell_width)
        y = self.initial_y + (row * self.cell_height)

        self.node_counter += 1

        return {"x": x, "y": y}
