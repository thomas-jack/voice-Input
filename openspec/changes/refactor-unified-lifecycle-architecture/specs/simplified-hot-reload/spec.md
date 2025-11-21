# Capability: Simplified Hot-Reload

## ADDED Requirements

### Requirement: Callback-Based Hot-Reload Interface
Services SHALL implement a simple callback interface to handle configuration changes without complex two-phase commit.

#### Scenario: Service implements hot-reload callback
- **GIVEN** a service that depends on configuration
- **WHEN** the service implements IConfigReloadable
- **THEN** the service SHALL provide `get_config_dependencies()` and `on_config_changed(diff)` methods

#### Scenario: Config dependencies declared
- **GIVEN** a service implementing IConfigReloadable
- **WHEN** `get_config_dependencies()` is called
- **THEN** it SHALL return a list of config key paths the service depends on (e.g., ["ai.enabled", "ai.provider"])

### Requirement: HotReloadManager Coordination
HotReloadManager SHALL coordinate configuration changes across affected services without topological sorting.

#### Scenario: Config change triggers service reload
- **GIVEN** a configuration change event with changed keys
- **WHEN** HotReloadManager receives the event
- **THEN** it SHALL identify affected services by matching changed keys to declared dependencies

#### Scenario: Services reloaded in linear order
- **GIVEN** multiple services affected by config change
- **WHEN** HotReloadManager reloads services
- **THEN** core services (EventBus, ConfigService) SHALL reload first, then application services

#### Scenario: Reload failure handling
- **GIVEN** a service whose `on_config_changed()` returns False
- **WHEN** reload fails
- **THEN** HotReloadManager SHALL log error and notify user to restart application

### Requirement: Complete Hot-Reload Coverage
ALL configuration changes SHALL trigger hot-reload for affected services (100% coverage).

#### Scenario: Hotkey configuration hot-reloads
- **GIVEN** user changes hotkey configuration in settings
- **WHEN** configuration is saved
- **THEN** HotkeyService SHALL reload and re-register hotkeys without restart

#### Scenario: AI provider switch hot-reloads
- **GIVEN** user switches AI provider (e.g., OpenRouter → Groq)
- **WHEN** configuration is saved
- **THEN** AIService SHALL reload and create new AI client without restart

#### Scenario: Transcription provider switch hot-reloads
- **GIVEN** user switches transcription provider (e.g., local → groq)
- **WHEN** configuration is saved
- **THEN** TranscriptionService SHALL reload and switch provider without restart

#### Scenario: Audio configuration hot-reloads
- **GIVEN** user changes audio device or sample rate
- **WHEN** configuration is saved
- **THEN** AudioService SHALL reload and reconfigure audio capture without restart

#### Scenario: Input method hot-reloads
- **GIVEN** user changes input method (e.g., SendInput → Clipboard)
- **WHEN** configuration is saved
- **THEN** InputService SHALL reload and switch input method without restart

#### Scenario: UI theme hot-reloads
- **GIVEN** user changes UI theme or overlay position
- **WHEN** configuration is saved
- **THEN** UI components SHALL reload and apply new theme without restart

### Requirement: Simplified ConfigReloadable Interface
The IConfigReloadable interface SHALL have only 2 methods (down from 6).

#### Scenario: Minimal interface methods
- **GIVEN** IConfigReloadable protocol
- **WHEN** a service implements it
- **THEN** only `get_config_dependencies() -> List[str]` and `on_config_changed(diff: ConfigDiff) -> bool` SHALL be required

### Requirement: No Rollback Mechanism
Hot-reload failures SHALL result in fail-fast behavior with user notification, not automatic rollback.

#### Scenario: Reload failure notification
- **GIVEN** a service hot-reload fails
- **WHEN** the failure occurs
- **THEN** user SHALL see a notification suggesting application restart

#### Scenario: No automatic rollback
- **GIVEN** a service hot-reload fails
- **WHEN** the failure is detected
- **THEN** previous configuration SHALL NOT be automatically restored

**Rationale**: Rollback adds complexity without clear benefit for desktop applications. Users can manually revert config and restart.

## REMOVED Requirements

### Requirement: Two-Phase Commit Hot-Reload
**Reason**: Over-engineered for desktop application
**Migration**: Replace `prepare_reload() + commit_reload() + rollback_reload()` with single `on_config_changed()`

#### Previous Interface (REMOVED):
```python
class IConfigReloadable:
    def get_reload_strategy(diff) -> ReloadStrategy: ...
    def can_reload_now() -> bool: ...
    def prepare_reload(diff) -> ReloadResult: ...
    def commit_reload(diff) -> ReloadResult: ...
    def rollback_reload(rollback_data): ...
    def get_service_dependencies() -> List[str]: ...
```

### Requirement: Topological Sorting of Services
**Reason**: Overkill for simple service dependencies
**Migration**: Replace Kahn's algorithm with linear core-first ordering

The ConfigReloadCoordinator's topological sorting logic SHALL be removed.

### Requirement: ReloadStrategy Enum (PARAMETER_UPDATE, REINITIALIZE, RECREATE)
**Reason**: Unnecessary complexity, services handle their own reload strategy
**Migration**: Services decide internally how to reload

The `ReloadStrategy` enum SHALL be removed from the hot-reload system.

### Requirement: ConfigReloadCoordinator
**Reason**: 594 lines of over-engineered coordination
**Migration**: Replace with HotReloadManager (<200 lines)

The `ConfigReloadCoordinator` class SHALL be deleted and replaced with simpler `HotReloadManager`.

### Requirement: ServiceRegistry Atomic Replacement
**Reason**: Unused feature (RECREATE strategy not needed)
**Migration**: Services reload in-place, no instance replacement

The `ServiceRegistry.replace()` method for atomic service instance replacement SHALL be removed.

## ADDED Requirements

### Requirement: ConfigDiff Simplified Structure
ConfigDiff SHALL contain only changed keys and old/new config snapshots.

#### Scenario: ConfigDiff structure
- **GIVEN** a configuration change
- **WHEN** ConfigDiff is created
- **THEN** it SHALL contain `changed_keys: Set[str]`, `old_config: Dict`, `new_config: Dict`, `timestamp: float`

### Requirement: Hot-Reload Target (<200 Lines)
HotReloadManager implementation SHALL be less than 200 lines of code.

#### Scenario: Code size verification
- **GIVEN** HotReloadManager implementation complete
- **WHEN** line count is measured
- **THEN** total lines (excluding comments/blank lines) SHALL be <200

### Requirement: Immediate Configuration Save
Configuration changes via UI SHALL use `immediate=True` by default to trigger hot-reload.

#### Scenario: UI config change triggers immediate reload
- **GIVEN** user modifies configuration in settings window
- **WHEN** "Apply" button is clicked
- **THEN** config SHALL be saved with `immediate=True` and hot-reload triggered immediately

### Requirement: Hot-Reload Latency Target
Configuration hot-reload SHALL complete in <100ms for simple changes.

#### Scenario: Hot-reload latency measurement
- **GIVEN** a simple config change (e.g., boolean toggle)
- **WHEN** hot-reload is triggered
- **THEN** service SHALL be reloaded in <100ms

### Requirement: Hot-Reload Service Registration
Services SHALL register themselves with HotReloadManager during initialization.

#### Scenario: Service self-registration
- **GIVEN** a service implementing IConfigReloadable
- **WHEN** service `_do_initialize()` is called
- **THEN** service SHALL register itself with HotReloadManager via `register(name, self, dependencies)`

### Requirement: Config Validation Before Save (Architecture Validation Modification 2)
ConfigService SHALL provide validation method to prevent saving invalid configurations that would cause hot-reload failures.

#### Scenario: Audio device validation before save
- **GIVEN** user changes audio device ID in settings
- **WHEN** user clicks "Apply" button
- **THEN** ConfigService SHALL validate device ID exists using PyAudio before saving
- **AND** if invalid, SHALL show error message and prevent save

#### Scenario: Hotkey validation before save
- **GIVEN** user changes hotkey in settings
- **WHEN** user clicks "Apply" button
- **THEN** ConfigService SHALL validate hotkey format is parseable before saving
- **AND** if invalid, SHALL show error message and prevent save

#### Scenario: Pre-save validation API
- **GIVEN** ConfigService implementation
- **WHEN** code calls `validate_before_save(key, value)`
- **THEN** it SHALL return `(is_valid: bool, error_message: str)` tuple
- **AND** SHALL have validators for critical configs: audio.device_id, hotkeys.keys, transcription.provider

**Rationale**: Prevents critical service hot-reload failures by validating config before save, rather than discovering errors during hot-reload. Reduces risk of audio/hotkey functionality breaking from 15% to <2%.

### Requirement: Background Model Download for Provider Switch (Architecture Validation Modification 3)
TranscriptionService SHALL download sherpa-onnx models in background thread to prevent UI freezing during hot-reload.

#### Scenario: Non-blocking model download
- **GIVEN** user switches transcription provider from cloud to local
- **WHEN** config is saved and hot-reload triggered
- **THEN** TranscriptionService SHALL start background thread for model download (226MB)
- **AND** UI SHALL remain responsive

#### Scenario: Download progress indication
- **GIVEN** model download in progress
- **WHEN** download is 50% complete
- **THEN** EventBus SHALL emit `model_download_progress` event with percent: 50
- **AND** SettingsWindow SHALL display progress dialog

#### Scenario: Download completion
- **GIVEN** model download completes successfully
- **WHEN** download finishes
- **THEN** TranscriptionService SHALL switch to new local provider
- **AND** EventBus SHALL emit `model_download_completed` event
- **AND** SettingsWindow SHALL close progress dialog and show success message

#### Scenario: Download failure handling
- **GIVEN** model download fails (network error)
- **WHEN** download fails
- **THEN** TranscriptionService SHALL keep current provider
- **AND** EventBus SHALL emit `model_download_failed` event with error
- **AND** SettingsWindow SHALL show error dialog

**Rationale**: Improves user experience by avoiding 3-10 second UI freeze during model download. Non-blocking design allows user to continue using app while download completes in background.
