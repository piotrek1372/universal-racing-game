"""
Entity-Component-System (ECS) Architecture

Lightweight ECS implementation for Universal Racing Game.
Provides a flexible and performant architecture for game entities,
components, and systems with focus on data-oriented design.

Author: URG Development Team
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any, Type, TypeVar, Generic
from abc import ABC, abstractmethod
import uuid


# Type variable for component type safety
T = TypeVar('T', bound='Component')


class Component(ABC):
    """
    Base class for all components.
    
    Components are pure data containers that describe aspects of an entity.
    They should not contain any logic - only data fields.
    
    Attributes:
        name: Component type name for identification
    """
    
    def __init__(self, name: str = "Component") -> None:
        """
        Initialize component with type name.
        
        Args:
            name: Component type identifier
        """
        self.name: str = name
    
    def __repr__(self) -> str:
        """String representation of component."""
        return f"{self.name}()"


class TransformComponent(Component):
    """
    Transform component storing position, rotation, and scale.
    
    Essential for rendering and physics calculations.
    """
    
    def __init__(self, 
                 x: float = 0.0, 
                 y: float = 0.0, 
                 z: float = 0.0,
                 rotation: float = 0.0,
                 scale_x: float = 1.0,
                 scale_y: float = 1.0,
                 scale_z: float = 1.0) -> None:
        """
        Initialize transform component.
        
        Args:
            x: X position
            y: Y position  
            z: Z position
            rotation: Rotation in degrees
            scale_x: X scale factor
            scale_y: Y scale factor
            scale_z: Z scale factor
        """
        super().__init__("TransformComponent")
        self.x: float = x
        self.y: float = y
        self.z: float = z
        self.rotation: float = rotation
        self.scale_x: float = scale_x
        self.scale_y: float = scale_y
        self.scale_z: float = scale_z
    
    def __repr__(self) -> str:
        """String representation with position data."""
        return f"TransformComponent(pos=({self.x}, {self.y}, {self.z}))"


class TextComponent(Component):
    """
    Text component for UI elements and labels.
    
    Stores text content and styling information. Designed to work
    with the LocaleSystem for automatic language updates.
    
    Attributes:
        text_key: Localization key for automatic translation
        text: Current text content
        font_size: Font size for rendering
        color: Text color as RGBA tuple
    """
    
    def __init__(self, 
                 text_key: str = "", 
                 text: str = "",
                 font_size: int = 12,
                 color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)) -> None:
        """
        Initialize text component.
        
        Args:
            text_key: Localization key for automatic translation updates
            text: Initial text content
            font_size: Font size for rendering
            color: Text color as RGBA tuple (r, g, b, a)
        """
        super().__init__("TextComponent")
        self.text_key: str = text_key
        self.text: str = text
        self.font_size: int = font_size
        self.color: tuple[float, float, float, float] = color
    
    def __repr__(self) -> str:
        """String representation with text preview."""
        preview: str = self.text[:30] + "..." if len(self.text) > 30 else self.text
        return f"TextComponent(key='{self.text_key}', text='{preview}')"


class VelocityComponent(Component):
    """
    Velocity component for movement and physics.
    
    Stores linear and angular velocity for physics calculations.
    """
    
    def __init__(self, 
                 vx: float = 0.0,
                 vy: float = 0.0,
                 vz: float = 0.0,
                 angular_velocity: float = 0.0) -> None:
        """
        Initialize velocity component.
        
        Args:
            vx: X velocity
            vy: Y velocity
            vz: Z velocity
            angular_velocity: Angular velocity in degrees per second
        """
        super().__init__("VelocityComponent")
        self.vx: float = vx
        self.vy: float = vy
        self.vz: float = vz
        self.angular_velocity: float = angular_velocity
    
    def __repr__(self) -> str:
        """String representation with velocity data."""
        return f"VelocityComponent(v=({self.vx}, {self.vy}, {self.vz}))"


class Entity:
    """
    Entity class representing a game object.
    
    Entities are unique identifiers that group components together.
    They have no logic of their own - all behavior comes from systems
    processing their components.
    
    Attributes:
        id: Unique entity identifier
        name: Human-readable name for debugging
        active: Whether the entity is active in the game world
        components: Dictionary of component type to component instance
    """
    
    def __init__(self, name: str = "Entity") -> None:
        """
        Initialize entity with unique ID.
        
        Args:
            name: Human-readable name for debugging
        """
        self.id: str = str(uuid.uuid4())
        self.name: str = name
        self.active: bool = True
        self.components: Dict[Type[Component], Component] = {}
    
    def add_component(self, component: Component) -> None:
        """
        Add a component to the entity.
        
        Args:
            component: Component instance to add
        
        Note:
            Replaces existing component of the same type.
        """
        component_type: Type[Component] = type(component)
        self.components[component_type] = component
    
    def get_component(self, component_type: Type[T]) -> Optional[T]:
        """
        Get a component of the specified type.
        
        Args:
            component_type: Component class type to retrieve
        
        Returns:
            Optional[T]: Component instance if found, None otherwise
        """
        return self.components.get(component_type)
    
    def has_component(self, component_type: Type[Component]) -> bool:
        """
        Check if entity has a component of the specified type.
        
        Args:
            component_type: Component class type to check
        
        Returns:
            bool: True if entity has the component
        """
        return component_type in self.components
    
    def remove_component(self, component_type: Type[Component]) -> bool:
        """
        Remove a component from the entity.
        
        Args:
            component_type: Component class type to remove
        
        Returns:
            bool: True if component was removed, False if not found
        """
        if component_type in self.components:
            del self.components[component_type]
            return True
        return False
    
    def __repr__(self) -> str:
        """String representation with component count."""
        return f"Entity(name='{self.name}', components={len(self.components)})"


class System(ABC):
    """
    Base class for all systems.
    
    Systems contain the logic that operates on entities with specific
    component combinations. They implement the game's behavior.
    
    Attributes:
        name: System identifier for debugging
        priority: Update order (lower = earlier)
    """
    
    def __init__(self, name: str = "System", priority: int = 0) -> None:
        """
        Initialize system with name and priority.
        
        Args:
            name: System identifier
            priority: Update order priority
        """
        self.name: str = name
        self.priority: int = priority
    
    @abstractmethod
    def update(self, entities: List[Entity], dt: float) -> None:
        """
        Update system logic.
        
        Args:
            entities: List of entities to process
            dt: Delta time since last update in seconds
        """
        pass
    
    def __repr__(self) -> str:
        """String representation with priority."""
        return f"{self.name}(priority={self.priority})"


class LocaleSystem(System):
    """
    System for managing localization updates across text components.
    
    This system automatically updates TextComponent instances when
    the application language changes. It bridges the i18n system with
    the ECS architecture, ensuring UI elements always display the
    correct language.
    
    Attributes:
        localization_manager: Reference to i18n system
        text_entities: Cache of entities with text components
    """
    
    def __init__(self, localization_manager: Any) -> None:
        """
        Initialize locale system.
        
        Args:
            localization_manager: LocalizationManager instance for translations
        """
        super().__init__("LocaleSystem", priority=100)  # High priority for UI updates
        self.localization_manager = localization_manager
        self.text_entities: List[Entity] = []
    
    def register_text_entity(self, entity: Entity) -> None:
        """
        Register an entity with a text component for automatic updates.
        
        Args:
            entity: Entity containing a TextComponent
        
        Note:
            Entities are automatically registered when processed in update().
            This method allows manual registration for immediate updates.
        """
        if entity not in self.text_entities and entity.has_component(TextComponent):
            self.text_entities.append(entity)
            self._update_entity_text(entity)
    
    def _update_entity_text(self, entity: Entity) -> None:
        """
        Update text component with current language translation.
        
        Args:
            entity: Entity with TextComponent to update
        
        Note:
            Uses the text_key field to look up translation in localization manager.
            Falls back to existing text if translation key is missing.
        """
        text_component: Optional[TextComponent] = entity.get_component(TextComponent)
        if text_component and text_component.text_key:
            # Get translated text from localization manager
            translated: str = self.localization_manager.get(
                text_component.text_key,
                text_component.text
            )
            text_component.text = translated
    
    def update(self, entities: List[Entity], dt: float) -> None:
        """
        Update all text components with current language.
        
        Processes entities with TextComponent and updates their text
        based on the current language setting. Maintains a cache of
        text entities for efficient updates when language changes.
        
        Args:
            entities: List of all entities in the game world
            dt: Delta time since last update (unused for locale updates)
        
        Note:
            This system runs with high priority to ensure UI text is
            updated before rendering. It only processes entities with
            TextComponent to optimize performance.
        """
        # Find entities with text components
        current_text_entities: List[Entity] = [
            entity for entity in entities 
            if entity.active and entity.has_component(TextComponent)
        ]
        
        # Update cache
        for entity in current_text_entities:
            if entity not in self.text_entities:
                self.text_entities.append(entity)
        
        # Update text for all registered entities
        for entity in self.text_entities:
            if entity.active:
                self._update_entity_text(entity)
    
    def force_update(self) -> None:
        """
        Force update all registered text entities.
        
        Call this method when language is changed externally to
        immediately refresh all UI text without waiting for next
        update cycle.
        """
        for entity in self.text_entities:
            if entity.active:
                self._update_entity_text(entity)


class MovementSystem(System):
    """
    System for updating entity positions based on velocity.
    
    Processes entities with both TransformComponent and VelocityComponent,
    updating positions based on velocity and elapsed time.
    """
    
    def __init__(self) -> None:
        """Initialize movement system."""
        super().__init__("MovementSystem", priority=50)
    
    def update(self, entities: List[Entity], dt: float) -> None:
        """
        Update entity positions based on velocity.
        
        Args:
            entities: List of all entities in the game world
            dt: Delta time since last update in seconds
        
        Note:
            Only processes entities with both TransformComponent and
            VelocityComponent. Uses simple Euler integration for movement.
        """
        for entity in entities:
            if not entity.active:
                continue
            
            transform: Optional[TransformComponent] = entity.get_component(TransformComponent)
            velocity: Optional[VelocityComponent] = entity.get_component(VelocityComponent)
            
            if transform and velocity:
                # Update position based on velocity
                transform.x += velocity.vx * dt
                transform.y += velocity.vy * dt
                transform.z += velocity.vz * dt
                
                # Update rotation based on angular velocity
                transform.rotation += velocity.angular_velocity * dt


class SystemManager:
    """
    Manages all systems and coordinates their execution.
    
    The SystemManager maintains a collection of systems and executes
    them in priority order. It provides methods for adding, removing,
    and updating systems, as well as managing the entity list.
    
    Attributes:
        systems: List of registered systems sorted by priority
        entities: List of all entities in the game world
    """
    
    def __init__(self) -> None:
        """Initialize system manager with empty collections."""
        self.systems: List[System] = []
        self.entities: List[Entity] = []
    
    def add_system(self, system: System) -> None:
        """
        Add a system to the manager.
        
        Args:
            system: System instance to add
        
        Note:
            Systems are automatically sorted by priority after addition.
            Lower priority values are updated first.
        """
        self.systems.append(system)
        self.systems.sort(key=lambda s: s.priority)
    
    def remove_system(self, system_type: Type[System]) -> bool:
        """
        Remove a system by type.
        
        Args:
            system_type: System class type to remove
        
        Returns:
            bool: True if system was removed, False if not found
        """
        for i, system in enumerate(self.systems):
            if type(system) == system_type:
                self.systems.pop(i)
                return True
        return False
    
    def get_system(self, system_type: Type[T]) -> Optional[T]:
        """
        Get a system by type.
        
        Args:
            system_type: System class type to retrieve
        
        Returns:
            Optional[T]: System instance if found, None otherwise
        """
        for system in self.systems:
            if type(system) == system_type:
                return system
        return None
    
    def add_entity(self, entity: Entity) -> None:
        """
        Add an entity to the manager.
        
        Args:
            entity: Entity instance to add
        
        Note:
            Automatically registers entity with LocaleSystem if it
            has a TextComponent.
        """
        self.entities.append(entity)
        
        # Auto-register with LocaleSystem if entity has text component
        locale_system: Optional[LocaleSystem] = self.get_system(LocaleSystem)
        if locale_system and entity.has_component(TextComponent):
            locale_system.register_text_entity(entity)
    
    def remove_entity(self, entity: Entity) -> bool:
        """
        Remove an entity from the manager.
        
        Args:
            entity: Entity instance to remove
        
        Returns:
            bool: True if entity was removed, False if not found
        """
        if entity in self.entities:
            self.entities.remove(entity)
            return True
        return False
    
    def get_entities_with_components(self, *component_types: Type[Component]) -> List[Entity]:
        """
        Get all entities that have all specified component types.
        
        Args:
            *component_types: Variable number of component types to match
        
        Returns:
            List[Entity]: Entities that have all specified components
        
        Example:
            >>> manager.get_entities_with_components(TransformComponent, VelocityComponent)
            [Entity(name='Car', ...), Entity(name='Player', ...)]
        """
        matching_entities: List[Entity] = []
        
        for entity in self.entities:
            if entity.active and all(
                entity.has_component(ct) for ct in component_types
            ):
                matching_entities.append(entity)
        
        return matching_entities
    
    def update(self, dt: float) -> None:
        """
        Update all systems in priority order.
        
        Args:
            dt: Delta time since last update in seconds
        
        Note:
            Systems are updated in priority order (lower priority first).
            This ensures dependencies are resolved correctly (e.g., movement
            before rendering).
        """
        for system in self.systems:
            system.update(self.entities, dt)
    
    def clear(self) -> None:
        """Remove all entities and systems from the manager."""
        self.entities.clear()
        self.systems.clear()
    
    def __repr__(self) -> str:
        """String representation with system and entity counts."""
        return f"SystemManager(systems={len(self.systems)}, entities={len(self.entities)})"


if __name__ == "__main__":
    # Test the ECS implementation
    print("=== ECS Architecture Test ===\n")
    
    # Create system manager
    manager: SystemManager = SystemManager()
    print(f"Created: {manager}\n")
    
    # Create entities
    player: Entity = Entity(name="Player")
    player.add_component(TransformComponent(x=0, y=0, z=0))
    player.add_component(VelocityComponent(vx=10, vy=0, vz=0))
    player.add_component(TextComponent(text_key="game.position", text="Position: 1st"))
    
    car: Entity = Entity(name="Race Car")
    car.add_component(TransformComponent(x=100, y=0, z=0))
    car.add_component(VelocityComponent(vx=50, vy=0, vz=0, angular_velocity=5))
    car.add_component(TextComponent(text_key="game.speed", text="Speed: 50 km/h"))
    
    # Add entities to manager
    manager.add_entity(player)
    manager.add_entity(car)
    print(f"Added entities: {player}, {car}\n")
    
    # Add systems
    from src.i18n import get_localization_manager
    locale_manager = get_localization_manager()
    
    locale_system: LocaleSystem = LocaleSystem(locale_manager)
    movement_system: MovementSystem = MovementSystem()
    
    manager.add_system(locale_system)
    manager.add_system(movement_system)
    print(f"Added systems: {locale_system}, {movement_system}\n")
    
    # Update systems
    print("=== Initial State ===")
    manager.update(dt=0.0)
    
    for entity in manager.entities:
        text_comp: Optional[TextComponent] = entity.get_component(TextComponent)
        if text_comp:
            print(f"{entity.name}: {text_comp.text}")
    
    # Simulate movement update
    print("\n=== After Movement Update (dt=1.0) ===")
    manager.update(dt=1.0)
    
    for entity in manager.entities:
        transform: Optional[TransformComponent] = entity.get_component(TransformComponent)
        if transform:
            print(f"{entity.name}: Position = ({transform.x:.1f}, {transform.y:.1f}, {transform.z:.1f})")
    
    print("\n=== ECS Test Complete ===")