"""
Vehicle system built on top of Panda3D BulletVehicle.

The implementation uses composition: physics state is maintained by
Bullet objects while visuals are synchronized through NodePaths.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

from panda3d.bullet import BulletBoxShape, BulletRigidBodyNode, BulletVehicle, ZUp
from panda3d.core import LPoint3, LVector3, NodePath

from src.core.physics import PhysicsWorld


@dataclass(frozen=True)
class VehiclePhysicsConfig:
    """
    Physical parameters for a vehicle chassis and wheels.

    Attributes:
        mass: Chassis mass in kilograms.
        suspension_stiffness: Suspension spring stiffness.
        suspension_damping: Suspension damping value.
        suspension_compression: Suspension compression damping.
        friction_slip: Tire friction coefficient used by Bullet wheels.
        roll_influence: Roll reduction factor for wheel stability.
        max_suspension_force: Maximum force each suspension can apply.
        suspension_rest_length: Suspension rest length in meters.
        wheel_radius: Wheel radius in meters.
        chassis_half_extents: Half extents for box chassis collision shape.
    """

    mass: float = 1200.0
    suspension_stiffness: float = 40.0
    suspension_damping: float = 2.3
    suspension_compression: float = 4.4
    friction_slip: float = 100.0
    roll_influence: float = 0.1
    max_suspension_force: float = 6000.0
    suspension_rest_length: float = 0.3
    wheel_radius: float = 0.35
    chassis_half_extents: LVector3 = LVector3(0.9, 2.0, 0.45)


@dataclass(frozen=True)
class WheelConfig:
    """
    Per-wheel placement and steering role.

    Attributes:
        connection_point: Wheel mount point in chassis local space.
        is_front_wheel: True for steerable front wheel, False for rear.
    """

    connection_point: LPoint3
    is_front_wheel: bool


@dataclass(frozen=True)
class VehicleConfig:
    """
    Aggregate configuration for constructing a 4-wheel vehicle.

    Attributes:
        physics: Physical tuning values for chassis and wheels.
        wheel_setups: Sequence defining wheel layout and front/rear flags.
    """

    physics: VehiclePhysicsConfig = field(default_factory=VehiclePhysicsConfig)
    wheel_setups: Sequence[WheelConfig] = field(
        default_factory=lambda: (
            WheelConfig(LPoint3(-0.8, 1.5, -0.25), True),
            WheelConfig(LPoint3(0.8, 1.5, -0.25), True),
            WheelConfig(LPoint3(-0.8, -1.5, -0.25), False),
            WheelConfig(LPoint3(0.8, -1.5, -0.25), False),
        )
    )


class Vehicle:
    """
    Compositional wrapper around `BulletVehicle`.

    Physics simulation is fully handled by Bullet, while this class exposes
    clear methods for visual synchronization and lifecycle management.
    """

    def __init__(
        self,
        physics_world: PhysicsWorld,
        parent: NodePath,
        config: VehicleConfig | None = None,
    ) -> None:
        """
        Create a vehicle chassis, BulletVehicle, and 4 wheel setup.

        Args:
            physics_world: Target simulation world wrapper.
            parent: Scene graph parent for visual and physics NodePaths.
            config: Optional custom vehicle tuning and wheel layout.
        """

        self.physics_world: PhysicsWorld = physics_world
        self.parent: NodePath = parent
        self.config: VehicleConfig = config or VehicleConfig()

        self.chassis_node: BulletRigidBodyNode = BulletRigidBodyNode("vehicle_chassis")
        self.chassis_node.setMass(self.config.physics.mass)
        self.chassis_node.addShape(BulletBoxShape(self.config.physics.chassis_half_extents))
        self.chassis_np: NodePath = self.parent.attachNewNode(self.chassis_node)
        self.chassis_np.setPos(LPoint3(0.0, 0.0, 2.0))

        self.vehicle: BulletVehicle = BulletVehicle(self.physics_world.world, self.chassis_node)
        self.vehicle.setCoordinateSystem(ZUp)

        self.physics_world.attach_rigid_body(self.chassis_node)
        self.physics_world.attach_vehicle(self.vehicle)

        self.chassis_visual_np: NodePath = self.parent.attachNewNode("vehicle_chassis_visual")
        self.wheel_physics_nodes: List[NodePath] = []
        self.wheel_visual_nodes: List[NodePath] = []

        self._configure_wheels()

    def _configure_wheels(self) -> None:
        """
        Configure all wheels using `BulletVehicle.addWheel()`.

        The setup uses a standard 4-wheel passenger car layout and applies
        shared suspension/friction values from `VehiclePhysicsConfig`.
        """

        wheel_direction_cs: LVector3 = LVector3(0.0, 0.0, -1.0)
        wheel_axle_cs: LVector3 = LVector3(1.0, 0.0, 0.0)
        physics: VehiclePhysicsConfig = self.config.physics

        for index, wheel_setup in enumerate(self.config.wheel_setups):
            wheel = self.vehicle.addWheel(
                wheel_setup.connection_point,
                wheel_direction_cs,
                wheel_axle_cs,
                physics.suspension_rest_length,
                physics.wheel_radius,
                wheel_setup.is_front_wheel,
            )
            wheel.setSuspensionStiffness(physics.suspension_stiffness)
            wheel.setWheelsDampingRelaxation(physics.suspension_damping)
            wheel.setWheelsDampingCompression(physics.suspension_compression)
            wheel.setFrictionSlip(physics.friction_slip)
            wheel.setRollInfluence(physics.roll_influence)
            wheel.setMaxSuspensionForce(physics.max_suspension_force)

            wheel_physics_np: NodePath = self.parent.attachNewNode(f"wheel_physics_{index}")
            wheel_visual_np: NodePath = self.parent.attachNewNode(f"wheel_visual_{index}")
            wheel.setNode(wheel_physics_np)

            self.wheel_physics_nodes.append(wheel_physics_np)
            self.wheel_visual_nodes.append(wheel_visual_np)

    def sync_visuals(self) -> None:
        """
        Synchronize visual NodePaths with Bullet simulation every frame.
        """

        self.chassis_visual_np.setTransform(self.chassis_np.getTransform(self.parent))

        for wheel_physics_np, wheel_visual_np in zip(
            self.wheel_physics_nodes, self.wheel_visual_nodes
        ):
            wheel_visual_np.setTransform(wheel_physics_np.getTransform(self.parent))

    def cleanup(self) -> None:
        """
        Remove the vehicle from the Bullet world and scene graph.
        """

        self.physics_world.remove_vehicle(self.vehicle)
        self.physics_world.remove_rigid_body(self.chassis_node)

        for wheel_physics_np in self.wheel_physics_nodes:
            wheel_physics_np.removeNode()
        self.wheel_physics_nodes.clear()

        for wheel_visual_np in self.wheel_visual_nodes:
            wheel_visual_np.removeNode()
        self.wheel_visual_nodes.clear()

        self.chassis_visual_np.removeNode()
        self.chassis_np.removeNode()
