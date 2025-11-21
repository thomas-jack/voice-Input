# Capability: Typed Configuration Access

## ADDED Requirements

### Requirement: ConfigKeys Type-Safe Constants
All configuration key paths SHALL be defined as string constants in `ConfigKeys` class for type safety and IDE support.

#### Scenario: Config key defined as constant
- **GIVEN** a configuration key path "transcription.provider"
- **WHEN** defined in ConfigKeys class
- **THEN** it SHALL be accessible as `ConfigKeys.TRANSCRIPTION_PROVIDER` with IDE autocomplete

#### Scenario: Config key refactoring safe
- **GIVEN** a ConfigKeys constant is renamed (e.g., `AI_ENABLED` → `AI_PROCESSING_ENABLED`)
- **WHEN** IDE refactoring is triggered
- **THEN** all usages SHALL be automatically updated

#### Scenario: Config key validation
- **GIVEN** ConfigKeys class with 50+ constants
- **WHEN** a developer types `ConfigKeys.`
- **THEN** IDE SHALL show autocomplete list of all config keys

### Requirement: Unified Configuration Access Pattern
Configuration access SHALL use only the facade pattern via `IConfigService`, eliminating direct access and adapter patterns.

#### Scenario: Services access config via facade
- **GIVEN** a service requiring configuration
- **WHEN** the service accesses configuration
- **THEN** it SHALL call `config_service.get_setting(ConfigKeys.*, default)`

#### Scenario: UI accesses config via UISettingsService
- **GIVEN** a UI component requiring configuration
- **WHEN** the component accesses configuration
- **THEN** it SHALL call `ui_settings_service.get_setting(ConfigKeys.*)` (which delegates to facade)

#### Scenario: No direct ConfigService access from UI
- **GIVEN** a UI component
- **WHEN** the component is implemented
- **THEN** it SHALL NOT directly import or call ConfigService

### Requirement: Configuration Validation with ConfigKeys
Configuration validation SHALL reference ConfigKeys constants instead of string literals.

#### Scenario: Validator uses ConfigKeys
- **GIVEN** ConfigValidator validating configuration
- **WHEN** checking a specific key
- **THEN** it SHALL use `ConfigKeys.TRANSCRIPTION_PROVIDER` not `"transcription.provider"`

### Requirement: Updated Validation Rules
Configuration validation SHALL validate current technology stack (sherpa-onnx, not whisper).

#### Scenario: Sherpa-onnx validation
- **GIVEN** local transcription provider configured
- **WHEN** configuration is validated
- **THEN** validator SHALL check for valid sherpa-onnx models (paraformer, zipformer)

#### Scenario: Cloud provider validation
- **GIVEN** cloud transcription provider configured
- **WHEN** configuration is validated
- **THEN** validator SHALL check for valid providers (groq, siliconflow, qwen)

#### Scenario: AI provider validation
- **GIVEN** AI processing enabled
- **WHEN** configuration is validated
- **THEN** validator SHALL check for valid AI providers (openrouter, groq, nvidia, openai_compatible)

## REMOVED Requirements

### Requirement: String Literal Configuration Keys
**Reason**: Type-unsafe, typo-prone, no IDE support
**Migration**: Replace all `get_setting("key.path")` with `get_setting(ConfigKeys.KEY_PATH)`

#### Previous Pattern (REMOVED):
```python
# No autocomplete, typo-prone
value = config_service.get_setting("transcription.provider", "local")
value = config_service.get_setting("transcripton.provider", "local")  # Typo!
```

### Requirement: Multiple Configuration Access Patterns
**Reason**: Inconsistent, confusing
**Migration**: Standardize on facade pattern

#### Previous Patterns (REMOVED):
```python
# Pattern 1: Direct ConfigService access
value = self._config_service.get_setting("key")

# Pattern 2: Initialization config dict
config = config.get("section", {})
value = config.get("key")

# Pattern 3: UI adapter
value = self.ui_settings_service.get_setting("key")
```

### Requirement: Whisper Configuration Validation
**Reason**: Technology stack changed to sherpa-onnx in v0.3.0
**Migration**: Remove whisper validation, add sherpa-onnx validation

#### Previous Validation (REMOVED):
```python
whisper_model = config.get("whisper.model", "")
valid_models = ["tiny", "base", "small", "medium", "large-v3"]
if whisper_model not in valid_models:
    # ... error
```

## ADDED Requirements

### Requirement: ConfigKeys Comprehensive Coverage
ConfigKeys SHALL define constants for ALL configuration keys in the system (50+ keys).

#### Scenario: All keys covered
- **GIVEN** the configuration file structure
- **WHEN** ConfigKeys is complete
- **THEN** every leaf configuration key SHALL have a corresponding constant

#### Scenario: Nested configuration paths
- **GIVEN** nested configuration like `transcription.local.streaming_mode`
- **WHEN** defined in ConfigKeys
- **THEN** constant name SHALL be `TRANSCRIPTION_LOCAL_STREAMING_MODE`

### Requirement: ConfigKeys Documentation
Each ConfigKeys constant SHALL have a docstring explaining its purpose and valid values.

#### Scenario: Constant has docstring
- **GIVEN** a ConfigKeys constant
- **WHEN** developer hovers over constant in IDE
- **THEN** docstring SHALL explain purpose and show valid values

### Requirement: Immediate Parameter Default
Configuration `set_setting()` SHALL default to `immediate=True` to trigger hot-reload by default.

#### Scenario: Default immediate save
- **GIVEN** a call to `config_service.set_setting(key, value)`
- **WHEN** `immediate` parameter is not specified
- **THEN** configuration SHALL be saved immediately and hot-reload triggered

#### Scenario: Explicit deferred save
- **GIVEN** a call to `config_service.set_setting(key, value, immediate=False)`
- **WHEN** `immediate=False` is specified
- **THEN** configuration SHALL be saved on next flush or shutdown

### Requirement: Configuration Key Migration
Existing string literal config keys SHALL be migrated to ConfigKeys constants in all 145+ usage locations.

#### Scenario: All usages migrated
- **GIVEN** all files in the codebase
- **WHEN** searching for `get_setting("` or `set_setting("`
- **THEN** zero string literal keys SHALL be found (all use ConfigKeys)

### Requirement: IDE Integration
ConfigKeys SHALL be designed for optimal IDE experience (autocomplete, go-to-definition, find-usages).

#### Scenario: Go-to-definition works
- **GIVEN** a usage of `ConfigKeys.AI_ENABLED`
- **WHEN** developer uses "go to definition"
- **THEN** IDE SHALL jump to ConfigKeys class definition

#### Scenario: Find all usages works
- **GIVEN** ConfigKeys.TRANSCRIPTION_PROVIDER constant
- **WHEN** developer uses "find all usages"
- **THEN** IDE SHALL show all locations using this config key
