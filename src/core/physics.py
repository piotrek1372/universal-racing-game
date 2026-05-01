"""
Physics world management for Bullet-based simulation.

This module provides a fixed-step `BulletWorld` wrapper to keep
simulation deterministic and decoupled from variable render frame time.
"""

from __future__ import annotations

from dataclasses import dataclass

from panda3d.bullet import BulletRigidBodyNode, BulletVehicle, BulletWorld
from panda3d.core import LVector3


@dataclass(frozen=True)
class PhysicsWorldConfig:
    """
    Configuration values for the physics simulation world.

    Attributes:
        gravity: Gravity acceleration vector in world space.
        fixed_time_step: Fixed simulation tick duration in seconds.
        max_substeps: Maximum number of fixed ticks processed per frame.
    """

    gravity: LVector3 = LVector3(0.0, 0.0, -9.81)
    fixed_time_step: float = 1.0 / 60.0
    max_substeps: int = 5


class PhysicsWorld:
    """
    Manages a Bullet physics world with fixed-step simulation.

    This class isolates physics stepping from rendering. Call `step(dt)`
    once per frame with render delta time, and the class internally
    advances the Bullet world in fixed increments.
    """

    def __init__(self, config: PhysicsWorldConfig | None = None) -> None:
        """
        Initialize the Bullet world and fixed-step accumulator.

        Args:
            config: Optional world configuration. Defaults to 60 Hz setup.
        """

        self.config: PhysicsWorldConfig = config or PhysicsWorldConfig()
        self.world: BulletWorld = BulletWorld()
        self.world.setGravity(self.config.gravity)
        self._accumulator: float = 0.0

    def step(self, dt: float) -> None:
        """
        Advance simulation using a fixed time step.

        Args:
            dt: Render frame delta time in seconds.
        """

        if dt <= 0.0:
            return

        self._accumulator += dt
        max_time: float = self.config.fixed_time_step * self.config.max_substeps
        if self._accumulator > max_time:
            self._accumulator = max_time

        while self._accumulator >= self.config.fixed_time_step:
            self.world.doPhysics(self.config.fixed_time_step, 0, self.config.fixed_time_step)
            self._accumulator -= self.config.fixed_time_step

    def attach_rigid_body(self, body: BulletRigidBodyNode) -> None:
        """
        Add a rigid body to the Bullet world.

        Args:
            body: Body node to attach.
        """

        self.world.attachRigidBody(body)

    def remove_rigid_body(self, body: BulletRigidBodyNode) -> None:
        """
        Remove a rigid body from the Bullet world.

        Args:
            body: Body node to remove.
        """

        self.world.removeRigidBody(body)

    def attach_vehicle(self, vehicle: BulletVehicle) -> None:
        """
        Add a Bullet vehicle to the physics world.

        Args:
            vehicle: Vehicle instance to attach.
        """

        self.world.attachVehicle(vehicle)

    def remove_vehicle(self, vehicle: BulletVehicle) -> None:
        """
        Remove a Bullet vehicle from the physics world.

        Args:
            vehicle: Vehicle instance to remove.
        """

        self.world.removeVehicle(vehicle)

    def cleanup(self) -> None:
        """
        Reset internal stepping state.

        World-owned bodies and vehicles should be removed by their owners
        before this method is called.
        """

        self._accumulator = 0.0
