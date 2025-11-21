# Capability: Declarative Service Registry

## ADDED Requirements

### Requirement: Python-Based Service Definitions
Service registration SHALL use Python-based declarative definitions for type safety and IDE support.

#### Scenario: Service defined declaratively
- **GIVEN** a new service needs to be registered
- **WHEN** the service is added to service definitions file
- **THEN** the definition SHALL include interface type, implementation class, and lifetime (singleton/transient)

#### Scenario: Type checking enforced
- **GIVEN** service definitions use Python type hints
- **WHEN** mypy type checker runs
- **THEN** interface/implementation type mismatches SHALL be caught

### Requirement: Simplified DI Container
DI container SHALL focus solely on dependency injection and service location, delegating lifecycle to LifecycleComponent.

#### Scenario: Container registers singleton service
- **GIVEN** a service definition with "singleton" lifetime
- **WHEN** the service is registered in DI container
- **THEN** the container SHALL return the same instance on every `get()` call

#### Scenario: Container registers transient service
- **GIVEN** a service definition with "transient" lifetime
- **WHEN** the service is registered in DI container
- **THEN** the container SHALL create a new instance on every `get()` call

#### Scenario: Container resolves dependencies
- **GIVEN** a service with constructor dependencies
- **WHEN** `container.get(IMyService)` is called
- **THEN** the container SHALL automatically resolve and inject dependencies

### Requirement: Factory Functions for Complex Services
Complex service instantiation logic SHALL use factory functions while still being registered declaratively.

#### Scenario: Factory function registered
- **GIVEN** a service requiring complex initialization (e.g., SpeechService with provider detection)
- **WHEN** the service is defined with "factory:function_name" format
- **THEN** the factory function SHALL be called to create the service instance

#### Scenario: Factory receives container
- **GIVEN** a factory function for service creation
- **WHEN** the factory is invoked
- **THEN** the factory SHALL receive the DI container as parameter to resolve dependencies

### Requirement: Unified ServiceRegistry
There SHALL be only one ServiceRegistry implementation used by both DI container and hot-reload system.

#### Scenario: Single source of truth
- **GIVEN** a service registered in ServiceRegistry
- **WHEN** the service is queried by DI container or hot-reload manager
- **THEN** both SHALL return the same service instance

### Requirement: Service Cleanup Priority
Services SHALL declare cleanup priority to ensure proper shutdown order (dependencies cleaned up last).

#### Scenario: Cleanup priority respected
- **GIVEN** services with different cleanup priorities (UI=5, Business=50, Core=100)
- **WHEN** application shutdown occurs
- **THEN** services SHALL be cleaned up in descending priority order (Core last)

#### Scenario: EventBus cleaned up last
- **GIVEN** EventBus is a core dependency with priority 100
- **WHEN** shutdown occurs
- **THEN** EventBus SHALL be cleaned up after all other services

## REMOVED Requirements

### Requirement: Hardcoded Service Registration
**Reason**: Replaced by declarative definitions
**Migration**: 400-line `create_container()` function SHALL be replaced with service definitions file

#### Previous Pattern (REMOVED):
```python
def create_container() -> EnhancedDIContainer:
    container = EnhancedDIContainer()
    # 400 lines of hardcoded registration...
    container.register_singleton(IConfigService, ConfigService)
    # ...
```

### Requirement: DI Container Lifecycle Management
**Reason**: Lifecycle delegated to LifecycleComponent
**Migration**: Remove lifecycle-related methods from DI container

The DI container SHALL NOT manage service lifecycle states (init/start/stop), only creation and cleanup.

### Requirement: DI Container Hot-Reload Integration
**Reason**: Hot-reload delegated to HotReloadManager
**Migration**: Remove service replacement logic from DI container

The DI container SHALL NOT handle service replacement during hot-reload.

### Requirement: Service Decorators (Performance, ErrorHandling)
**Reason**: Unused and complex (dynamic method replacement)
**Migration**: Remove PerformanceDecorator and ErrorHandlingDecorator

Service decorators SHALL be removed from DI container to simplify implementation.

### Requirement: Duplicate ServiceRegistry Implementations
**Reason**: Consolidate into single implementation
**Migration**: Merge DI container's ServiceRegistry and hot-reload's ServiceRegistry

Only one ServiceRegistry SHALL exist in the codebase.

### Requirement: ConfigurableContainerFactory
**Reason**: Unused code (178 lines, zero usage)
**Migration**: None needed (no dependencies)

The `ConfigurableContainerFactory` and `ConfigurableServiceRegistry` classes SHALL be deleted.

## ADDED Requirements

### Requirement: Service Definition Format
Service definitions SHALL follow a consistent tuple format: `(Interface, Implementation, Lifetime)`.

#### Scenario: Service definition structure
- **GIVEN** a service definition
- **WHEN** the definition is created
- **THEN** it SHALL be a tuple of (interface type, implementation class or factory name, lifetime string)

#### Scenario: Lifetime values
- **GIVEN** a service definition
- **WHEN** specifying lifetime
- **THEN** valid values SHALL be "singleton", "transient", or "scoped"

### Requirement: Service Definition Categories
Service definitions SHALL be organized into logical categories (core, business, ui, infrastructure).

#### Scenario: Core services defined first
- **GIVEN** service definitions file
- **WHEN** definitions are listed
- **THEN** core services (EventBus, ConfigService, StateManager) SHALL be listed first

#### Scenario: Dependency order implicit
- **GIVEN** service definitions in order
- **WHEN** services are registered
- **THEN** services with fewer dependencies SHALL be registered before dependents
