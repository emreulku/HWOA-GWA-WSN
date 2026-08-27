"""
WSN Environment: Defines the network area, sensor nodes,
target points, and coverage calculations.
"""

import numpy as np


class WSNEnvironment:
    """
    100m x 100m wireless sensor network environment.
    All sensors share the same sensing radius r.
    Coverage is computed using Boolean disk model.
    """

    def __init__(self, n_sensors: int, n_targets: int,
                 area_size: float = 100.0,
                 sensing_radius: float = 5.0,
                 seed: int = 42):
        self.n_sensors      = n_sensors
        self.n_targets      = n_targets
        self.area_size      = area_size
        self.sensing_radius = sensing_radius
        self.seed           = seed

        rng = np.random.default_rng(seed)
        # Target positions — fixed for all algorithms in a scenario
        self.targets = rng.uniform(0, area_size, (n_targets, 2))
        # Initial sensor positions — randomly scattered
        self.initial_sensors = rng.uniform(0, area_size, (n_sensors, 2))

    # ------------------------------------------------------------------
    # Core coverage calculations
    # ------------------------------------------------------------------

    def coverage_rate(self, sensor_positions: np.ndarray) -> float:
        """
        Boolean disk coverage: a target is covered if at least one
        sensor is within sensing_radius of it.
        Returns fraction of targets covered in [0, 1].
        """
        covered = 0
        for t in self.targets:
            dists = np.linalg.norm(sensor_positions - t, axis=1)
            if np.any(dists <= self.sensing_radius):
                covered += 1
        return covered / self.n_targets

    def coverage_rate_vectorized(self, sensor_positions: np.ndarray) -> float:
        """Vectorized version of coverage_rate — faster for large N."""
        # (n_targets, n_sensors)
        diff = self.targets[:, np.newaxis, :] - sensor_positions[np.newaxis, :, :]
        dists = np.linalg.norm(diff, axis=2)
        covered = np.any(dists <= self.sensing_radius, axis=1).sum()
        return covered / self.n_targets

    def total_displacement(self, final_positions: np.ndarray) -> float:
        """Total Euclidean displacement of all sensors from initial positions."""
        return float(np.sum(
            np.linalg.norm(final_positions - self.initial_sensors, axis=1)
        ))

    def clip(self, positions: np.ndarray) -> np.ndarray:
        """Keep sensor positions inside the deployment area."""
        return np.clip(positions, 0, self.area_size)
