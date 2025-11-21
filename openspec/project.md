# Project Context

## Purpose
SonicInput is an enterprise-grade voice input system for Windows that provides real-time speech recognition with AI text optimization. The project aims to deliver ultra-lightweight, CPU-efficient speech-to-text functionality with intelligent input capabilities.

**Core Goals:**
- Ultra-lightweight installation (<250MB vs traditional 2-3GB solutions)
- Real-time speech recognition with dual streaming modes
- CPU-optimized inference (no GPU dependency)
- AI-powered text enhancement and formatting
- Seamless Windows integration with global hotkeys
- Production-ready stability with enterprise-grade architecture

## Tech Stack

### Core Runtime
- **Python**: >=3.10
- **Package Manager**: uv (modern Python dependency management)
- **GUI Framework**: PySide6 6.10.0 (LGPL)

### Speech Recognition
- **Engine**: sherpa-onnx (lightweight CPU inference)
- **Models**:
  - Paraformer (226MB, Chinese/English)
  - Zipformer (112MB, multilingual)
- **Audio Processing**: sounddevice, numpy, librosa

### Cloud Transcription Providers
- **Groq Whisper API**: Cloud-based speech recognition
- **SiliconFlow**: Chinese ASR specialist
- **Qwen ASR**: Fast cloud ASR service

### LLM Providers (AI Text Processing)
- **OpenRouter**: Multi-provider LLM gateway
- **Groq**: LLM text optimization
- **NVIDIA NIM**: Enterprise AI inference
- **Client Pattern**: OpenAI-compatible API abstraction
- **Optimization**: Text formatting, punctuation, grammar correction

### System Integration
- **Hotkeys**: pynput (global keyboard hooks)
- **Input Methods**: Windows SendInput API, clipboard-based injection
- **Audio Capture**: DirectSound (sounddevice backend)

### Development Tools
- **Linting**: ruff (fast Python linter)
- **Type Checking**: mypy (static type analysis)
- **Security**: bandit (vulnerability scanning)
- **CI/CD**: GitHub Actions

## Project Conventions

### Code Style
- **No emojis** in any console output or logs
- **PEP 8** compliance enforced by ruff
- **Type hints** required for all public APIs
- **Docstrings** for classes and complex methods
- **Line length**: 100 characters (PySide6 standard)
- **Import order**: stdlib → third-party → local
- **Naming conventions**:
  - Classes: `PascalCase`
  - Functions/methods: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
  - Private members: `_leading_underscore`

### Architecture Patterns

**Layered Architecture (Enterprise Pattern with Bimodal Services)**

实际架构分为五层，采用双模式服务设计：

```
Controllers → Stateful Services ├─ Stateless Services
                      │          │
                      └─ Interfaces Layer
                            │
                      Base Layer (LifecycleComponent)
```

1. **Controller Layer**: User interaction and business orchestration
   - `RecordingController`, `TranscriptionController`, `AIProcessingController`, `InputController`
   - Coordinates between UI and services
   - Most inherit `BaseController`, implement interface protocols

2. **Service Layer** (Bimodal Design):

   a. **Stateful Services** (inherit LifecycleComponent):
   - `AIService`, `HotkeyService`, `HistoryStorageService`, `LifecycleManager`
   - Require lifecycle management (init/start/stop/cleanup)
   - Manage external resources (audio devices, network connections)

   b. **Stateless Utility Services** (no inheritance):
   - `StateManager`, `StreamingCoordinator`, `TranscriptionCore`
   - Pure function-like design, orchestration and coordination
   - Examples: `EventBus`, `ConfigService`, `ServiceRegistry`

3. **Interface Layer**: Protocol definitions **(v0.4.0: Simplified to 3 core interfaces)**
   - **Only multi-implementation interfaces**: `ISpeechService`, `IAIClient`, `IInputService`
   - Removed 15 single-implementation interfaces (YAGNI principle)
   - Protocol-based for duck typing flexibility

4. **Base Layer**: Lifecycle management infrastructure **(v0.4.0: Simplified)**
   - `LifecycleComponent`: Base class for stateful services only (~80 lines)
   - **3 states**: STOPPED → RUNNING → ERROR (simplified from 8 states)
   - **2 abstract methods**: `_do_start()` and `_do_stop()` (simplified from 4 methods)
   - Thread-safe state transitions
   - **Note**: Not all services use this - only stateful ones

**Key Design Principles**
- **Bimodal Architecture**: Separates stateful (lifecycle-managed) from stateless (utility) services
- **Protocol-based interfaces**: Duck typing for flexibility
- **Dependency injection**: Constructor-based DI
- **Factory pattern**: Service factories for instantiation
- **Command pattern**: Encapsulated operations
- **Observer pattern**: Event-driven state updates via EventBus
- **Lifecycle management**: Unified lifecycle for stateful components only

**Architecture Rationale**:
- **Stateful Services**: Need proper initialization and cleanup for external resources
- **Stateless Services**: Pure computation and coordination, no resource management overhead
- **EventBus Pattern**: Central nervous system for loose coupling between components

### Service Dependency Rules

**Dependency Center Architecture**

The system follows a strict hierarchical dependency model to prevent circular dependencies:

```
Level 0 (Foundation):
  EventBus/DynamicEventSystem (NO dependencies)
    │
    ├─────────────────┬─────────────────┐
    │                 │                 │
Level 1 (Core Infrastructure):
  ConfigService    StateManager    (EventBus only)
    │                 │
    └────────┬────────┘
             │
Level 2 (Business Services):
  AIService, HotkeyService, HistoryStorageService
  (ConfigService + EventService + StateManager)
    │
Level 3 (Controllers):
  RecordingController, TranscriptionController, etc.
  (All Level 0-2 services)
    │
Level 4 (UI Layer):
  SettingsWindow, RecordingOverlay, SystemTray
  (All services via dependency injection)
```

**Dependency Rules**:

1. **EventBus is the Dependency Center**
   - EventBus/DynamicEventSystem has ZERO constructor dependencies
   - Must remain completely standalone
   - Only lazy-loads logger to avoid circular imports
   - All other services can depend on EventBus

2. **Core Infrastructure Services**
   - ConfigService: Depends ONLY on EventService (optional)
   - StateManager: Depends ONLY on EventService (optional)
   - These two services provide foundation for all other services

3. **Business Services**
   - Can depend on: ConfigService, EventService, StateManager
   - Cannot depend on: Controllers, UI components
   - Examples:
     - AIService: IConfigService
     - HotkeyService: (lifecycle-managed)
     - HistoryStorageService: IConfigService

4. **Controllers**
   - Must depend on: ConfigService, EventService, StateManager
   - Can depend on: Business services (via constructor injection)
   - BaseController enforces this pattern

5. **UI Layer**
   - Receives all dependencies via constructor injection
   - Never creates services directly
   - Uses facade pattern for complex operations

**Why EventBus is the Dependency Center**:

1. **Zero Dependencies**: EventBus is completely self-contained
2. **Universal Requirement**: All services need event communication
3. **Decoupling**: Enables loose coupling between components
4. **Initialization Order**: EventBus can be created first, others depend on it
5. **No Circular Risk**: Since EventBus depends on nothing, no circular dependencies possible

**Correct vs Incorrect Dependencies**:

```python
# CORRECT: EventBus with no dependencies
class DynamicEventSystem(IEventService):
    def __init__(self):
        self._listeners = defaultdict(list)
        self._lock = threading.RLock()
        # No constructor parameters

# CORRECT: ConfigService depends on EventService only
class RefactoredConfigService(IConfigService):
    def __init__(
        self,
        config_path: Optional[str] = None,
        event_service: Optional[IEventService] = None,
    ):
        self._event_service = event_service
        # Initialize config subsystems

# CORRECT: StateManager depends on EventService only
class StateManager(IStateManager):
    def __init__(
        self,
        event_service: Optional[IEventService] = None,
        max_history: int = 100,
    ):
        self._event_service = event_service
        # Initialize state tracking

# CORRECT: Business service depends on core services
class AIService(LifecycleComponent):
    def __init__(self, config_service: IConfigService):
        super().__init__("AIService", config_service)
        # AIService needs config but not state/events directly

# CORRECT: Controller depends on all core services
class BaseController:
    def __init__(
        self,
        config_service: IConfigService,
        event_service: IEventService,
        state_manager: IStateManager,
    ):
        self.config = config_service
        self.events = event_service
        self.state = state_manager

# INCORRECT: EventBus depending on other services
class WrongEventBus:
    def __init__(self, config_service: IConfigService):  # WRONG!
        self._config = config_service
        # This creates circular dependency

# INCORRECT: ConfigService depending on StateManager
class WrongConfigService:
    def __init__(
        self,
        event_service: IEventService,
        state_manager: IStateManager,  # WRONG!
    ):
        # Creates complex dependency graph

# INCORRECT: Business service depending on controllers
class WrongAIService:
    def __init__(
        self,
        config_service: IConfigService,
        recording_controller: RecordingController,  # WRONG!
    ):
        # Controllers should depend on services, not vice versa
```

**Verification Checklist**:

- [ ] EventBus has zero constructor parameters
- [ ] ConfigService only depends on EventService (optional)
- [ ] StateManager only depends on EventService (optional)
- [ ] Business services depend on Level 0-1 services only
- [ ] Controllers depend on Level 0-2 services
- [ ] UI components receive dependencies via injection
- [ ] No service creates its own dependencies (uses DI container)
- [ ] No circular imports detected (run `python -m compileall src/`)

**Maintenance Guidelines**:

1. **Adding New Services**: Always start at the correct dependency level
2. **Refactoring**: Never introduce dependencies that violate the hierarchy
3. **Testing**: Verify initialization order works (EventBus → Config/State → Services → Controllers → UI)
4. **Code Review**: Check all `__init__` signatures follow dependency rules

### Service Classification Pattern (Stateful vs Stateless)

**Architecture Principle**: Not all services need lifecycle management. The codebase uses a **bimodal service design** to minimize complexity and overhead.

**Service Classification**:

```
Total Services: 58 classes across 46 files
├── Stateful Services (24): Inherit LifecycleComponent
│   └── Require resource management (init/start/stop/cleanup)
└── Stateless Services (34): Pure utilities/factories
    └── No lifecycle overhead (function-like design)
```

**Stateful Service Criteria** (need LifecycleComponent):
1. Manages external resources (files, network connections, threads, sessions)
2. Maintains runtime state that requires cleanup
3. Has start/stop semantics (e.g., audio recording, hotkey listening)
4. Needs ordered initialization/shutdown

**Examples of Stateful Services**:
- `DynamicEventSystem` (EventBus): Manages event listeners, thread locks, cache
- `RefactoredConfigService`: Manages file watchers, config cache, file I/O
- `StateManager`: Manages state history, subscriber callbacks, thread locks
- `AudioRecorder`: Manages PyAudio instances, audio streams, recording threads
- `RefactoredTranscriptionService`: Coordinates model loading, streaming sessions, task queues
- `AIService`: Manages AI client instances, HTTP connections
- `HotkeyService`: Manages hotkey manager (Win32/pynput), system hooks
- `Win32HotkeyManager`, `PynputHotkeyManager`: Manage platform-specific message loops
- `SherpaEngine`: Manages sherpa-onnx recognizer instances, model loading
- Controllers: `RecordingController`, `TranscriptionController`, `AIProcessingController`, `InputController`
- UI Components: `TrayController`, `RecordingOverlay`, `TimerManager`, `AnimationController`

**Examples of Stateless Services**:
- Factories: `SpeechServiceFactory`, `AIClientFactory` (pure factory methods)
- Utilities: `ConfigValidator`, `ConfigReader`, `ConfigBackup`, `AudioProcessor`
- Cloud Providers: `GroqSpeechService`, `SiliconFlowEngine`, `QwenEngine` (stateless HTTP clients)
- AI Clients: `GroqClient`, `NvidiaClient`, `OpenAICompatibleClient`, `OpenRouterClient`
- UI Utilities: `PositionManager`, `AnimationEngine`, `TextDiffHelper`
- Service Infrastructure: `ServiceRegistry`, `DIContainer`, `HotReloadManager`

**Migration Tier System** (for LifecycleComponent migration):

```
Tier 0: Core Infrastructure (No Dependencies)
  └── DynamicEventSystem (EventBus)

Tier 1: Core Services (Depend on EventBus)
  ├── RefactoredConfigService
  └── StateManager

Tier 2: Business Services (Depend on Core)
  ├── AudioRecorder, SmartTextInput
  ├── AIService, HotkeyService, HistoryStorageService
  ├── StreamingCoordinator, TaskQueueManager, ModelManager
  ├── ErrorRecoveryService, RefactoredTranscriptionService
  ├── SherpaEngine
  └── Win32HotkeyManager, PynputHotkeyManager

Tier 3: Controllers (Depend on Services)
  ├── RecordingController
  ├── TranscriptionController
  ├── AIProcessingController
  └── InputController

Tier 4: UI Components (Depend on Controllers)
  ├── TrayController
  ├── RecordingOverlay
  ├── TimerManager
  └── AnimationController
```

**LifecycleComponent API Evolution**:

Old API (4 methods):
```python
class MyService(LifecycleComponent):
    def _do_initialize(self, config: Dict[str, Any]) -> bool: ...
    def _do_start(self) -> bool: ...
    def _do_stop(self) -> bool: ...
    def _do_cleanup(self) -> None: ...
```

New API (2 methods):
```python
class MyService(LifecycleComponent):
    def _do_start(self) -> bool:
        # Merge initialize + start logic here
        return True

    def _do_stop(self) -> bool:
        # Merge stop + cleanup logic here
        return True
```

**Migration Pattern**:
1. For services using old API (AIService, HotkeyService, HistoryStorageService, TrayController):
   - Move `_do_initialize()` logic to `_do_start()`
   - Move `_do_cleanup()` logic to `_do_stop()`
   - Remove config parameter from `_do_start()` (use `self._config_service` instead)

2. For services with manual lifecycle (TranscriptionService, TaskQueueManager, ModelManager):
   - Replace `start()` method with `_do_start()`
   - Replace `stop()` and `cleanup()` methods with `_do_stop()`
   - Add LifecycleComponent inheritance

3. For services with only cleanup (EventBus, ConfigService, AudioRecorder):
   - Add `_do_start()` method (initialize resources)
   - Move `cleanup()` logic to `_do_stop()`
   - Add LifecycleComponent inheritance

**Service Pattern Guidelines**:

1. **When to use LifecycleComponent**:
   - Service manages external resources (files, network, threads)
   - Service requires ordered initialization/shutdown
   - Service has start/stop semantics
   - Service needs resource cleanup guarantees

2. **When NOT to use LifecycleComponent**:
   - Pure factories (just create instances, no state)
   - Pure utilities (stateless helper functions)
   - Stateless HTTP clients (create sessions per request)
   - UI utilities managed by Qt parent-child hierarchy
   - Service infrastructure (registry, container, coordinator)

3. **Design Trade-offs**:
   - Stateful services: More robust, guaranteed cleanup, but higher complexity
   - Stateless services: Simpler, faster, but requires careful resource handling
   - Choose based on resource management needs, not arbitrary "everything needs lifecycle"

**Verification Checklist**:
- [ ] Stateful services inherit from LifecycleComponent
- [ ] Stateless services do NOT inherit from LifecycleComponent
- [ ] All stateful services implement `_do_start()` and `_do_stop()`
- [ ] No services use old `_do_initialize()` or `_do_cleanup()` methods
- [ ] Manual lifecycle methods (`start()`, `stop()`, `cleanup()`) are replaced
- [ ] Dependency order follows tier system (Tier 0 → Tier 1 → ... → Tier 4)

### Configuration Hot-Reload Pattern (v0.4.0)

**Architecture Philosophy**: Simple callback-based system (~50 lines) replaces complex topological sorting and two-phase commit (~594 lines).

**HotReloadManager Design**:

```python
class HotReloadManager:
    """Lightweight configuration hot-reload manager

    Replaces ConfigReloadCoordinator with simple callback pattern:
    - No topological sorting (Kahn's algorithm removed)
    - No two-phase commit (distributed transaction concept removed)
    - Hardcoded service reload order (5 lines)
    - Failure handling: Prompt user to restart app (2s startup time)
    """

    def register_callback(
        self,
        service_name: str,
        callback: Callable[[Dict[str, Any]], bool],
        description: str = "",
    ) -> None:
        """Register a service reload callback"""
        self._callbacks[service_name] = ReloadCallback(
            service_name=service_name,
            callback=callback,
            description=description,
        )

    def reload_config(self, new_config: Dict[str, Any]) -> bool:
        """Reload configuration with hardcoded service order"""
        reload_order = [
            "hotkey_service",
            "transcription_service",
            "ai_service",
            "audio_settings",
            "ui_preferences",
        ]

        for service_name in reload_order:
            callback = self._callbacks.get(service_name)
            if callback:
                success = callback.callback(new_config)
                if not success:
                    # Show error dialog: "Reload failed, please restart app"
                    return False

        return True
```

**Registration Pattern**:

```python
# In service initialization:
hot_reload_manager.register_callback(
    service_name="transcription_service",
    callback=lambda config: self._reload_transcription_config(config),
    description="Reload transcription provider and model settings",
)

# Reload implementation:
def _reload_transcription_config(self, config: Dict[str, Any]) -> bool:
    """Handle transcription config changes"""
    try:
        new_provider = config["transcription"]["provider"]
        if new_provider != self._current_provider:
            self._switch_provider(new_provider)
        return True
    except Exception as e:
        logger.error(f"Failed to reload transcription config: {e}")
        return False
```

**Configuration Validation** (v0.4.0 addition):

```python
class ConfigService:
    def validate_before_save(
        self,
        new_config: Dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """Validate config before saving to prevent invalid hot-reload

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        # Validate audio device ID
        device_id = new_config.get("audio", {}).get("device_id")
        if device_id and not self._is_valid_device(device_id):
            errors.append(f"Invalid audio device ID: {device_id}")

        # Validate hotkey format
        hotkeys = new_config.get("hotkeys", [])
        for hotkey in hotkeys:
            if not self._is_valid_hotkey(hotkey):
                errors.append(f"Invalid hotkey format: {hotkey}")

        return (len(errors) == 0, errors)
```

**Model Download Progress** (v0.4.0 addition):

When switching transcription provider to local sherpa-onnx, if model not cached:

```python
# Synchronous download with progress dialog (QProgressDialog)
progress_dialog = QProgressDialog(
    "Downloading model: paraformer\nSize: 226 MB",
    None,  # No cancel button
    0, 100,
    parent_window
)
progress_dialog.setWindowModality(Qt.WindowModal)

# Download with progress updates
for chunk in download_stream:
    bytes_downloaded += len(chunk)
    percent = int(bytes_downloaded * 100 / total_size)
    progress_dialog.setValue(percent)
    progress_dialog.setLabelText(
        f"Downloading model: {model_name}\n"
        f"Progress: {bytes_downloaded/1024/1024:.1f} MB / "
        f"{total_size/1024/1024:.1f} MB ({percent}%)"
    )
    QApplication.processEvents()  # Keep UI responsive

progress_dialog.setValue(95)
progress_dialog.setLabelText(f"Extracting model: {model_name}\nPlease wait...")

# User accepts 3-10 second wait (simple implementation, no background threads)
```

**Design Trade-offs**:

**Old System (ConfigReloadCoordinator, 594 lines)**:
- Topological sorting for dependency graph
- Two-phase commit (prepare → validate → commit → rollback)
- Complex state machine with transaction IDs
- Dynamic dependency resolution

**New System (HotReloadManager, 50 lines)**:
- Hardcoded reload order (5 lines): hotkey → transcription → AI → audio → UI
- Simple callback pattern
- Fail fast: Show error, prompt restart
- Justification: 2-second cold start, single-machine app, no distributed transactions

**Benefits of Simplification**:
- 92% code reduction (594 → 50 lines)
- No Kahn's algorithm complexity
- No transaction overhead
- Easier to understand and maintain
- Acceptable failure mode: "Please restart app (2s startup time)"

**Usage Example**:

```python
# Settings window applies config changes:
def _apply_config(self):
    # 1. Validate before saving
    is_valid, errors = self.config_service.validate_before_save(new_config)
    if not is_valid:
        show_error_dialog("\n".join(errors))
        return

    # 2. Save to disk
    self.config_service.save_config(new_config)

    # 3. Hot-reload services
    success = self.hot_reload_manager.reload_config(new_config)
    if not success:
        show_error_dialog(
            "Configuration reload failed.\n"
            "Please restart the application (2-second startup)."
        )
```

**Verification Checklist**:
- [ ] Services register reload callbacks with `HotReloadManager`
- [ ] Reload callbacks return bool (success/failure)
- [ ] Config validation happens before save
- [ ] Model download shows progress dialog
- [ ] Reload failures prompt user to restart app

### Testing Strategy

**Current Approach** (pragmatic, production-focused):
- **pytest**: Unit and integration test framework
- **Smoke testing**: `--test` flag for automated core functionality validation
- **Manual GUI testing**: `--gui` flag for user interaction verification
- **Diagnostics**: `--diagnostics` flag for configuration validation
- **CI/CD**: GitHub Actions runs code quality checks (ruff, mypy, bandit)
- **Functional testing**: Local Windows environment only

**Testing Workflow**:
1. After code changes: `uv run python app.py --test`
2. Validate UI: `uv run python app.py --gui`
3. Fix issues immediately (no technical debt accumulation)

**Test Coverage**:
- Unit tests for service layer (pytest)
- Integration tests for speech recognition pipeline
- Mock-based testing for external API clients

### Git Workflow

**Branching Strategy**:
- **Main branch**: `master` (production-ready code)
- **Direct commits**: Small fixes and features
- **Feature branches**: For larger changes (optional)

**Commit Conventions**:
- Prefix format: `type: description`
  - `feat:` New features
  - `fix:` Bug fixes
  - `chore:` Maintenance tasks
  - `refactor:` Code restructuring
  - `docs:` Documentation updates

**Example Commits** (from recent history):
- `fix: Ensure config hot-reload triggers immediately on Apply`
- `chore: Update uv.lock for v0.3.3`
- `chore: Remove redundant RELEASE_NOTES.md`

## Domain Context

### Speech Recognition Domain
- **Real-time Factor (RTF)**: Performance metric (sherpa-onnx achieves 0.06-0.21)
  - RTF < 1.0 = faster than real-time
  - RTF = 0.1 = 10x faster than real-time
- **Streaming modes**:
  - **chunked**: 30-second blocks, supports AI optimization
  - **realtime**: Edge-to-edge streaming, minimum latency
- **Audio specs**: 16kHz sample rate, mono channel (industry standard for ASR)

### Windows Integration Patterns
- **Global hotkeys**: System-wide keyboard hooks (requires admin on some systems)
- **SendInput API**: Native Windows input injection
- **System tray**: Persistent background application pattern
- **AppData storage**: User-scoped configuration and logs
  - Config: `%APPDATA%\SonicInput\config.json`
  - Logs: `%APPDATA%\SonicInput\logs\app.log`

### AI Text Optimization
- **Use case**: Fix transcription errors, add punctuation, format text
- **Pattern**: Post-processing step after speech recognition
- **Provider flexibility**: Supports multiple LLM backends (Groq, OpenRouter, etc.)

## Important Constraints

### Platform Constraints
- **Windows 11 only**: Project targets Windows 11 environment
- **No Linux/macOS commands**: Avoid cross-platform assumptions
- **Process management**: Cannot kill node.exe (Claude Code runs on Node.js)

### Technical Constraints
- **CPU-only inference**: No GPU/CUDA dependencies
- **Lightweight requirement**: Total installation <250MB
- **Real-time performance**: Transcription must be faster than real-time (RTF < 0.3)
- **Thread safety**: Multi-threaded audio recording and processing
- **Resource cleanup**: Strict lifecycle management to prevent memory leaks

### User Experience Constraints
- **Hotkey responsiveness**: <100ms reaction time
- **Recording control**: Manual stop via hotkey or UI button
- **Recording duration**: Unlimited (user manually stops recording)
- **Model auto-download**: First-run experience must be smooth

## External Dependencies

### Speech Recognition APIs
- **Groq Whisper API**: `whisper-large-v3-turbo` model
  - Requires API key
  - Cloud-based transcription fallback

- **SiliconFlow**: `FunAudioLLM/SenseVoiceSmall` model
  - Chinese ASR specialist
  - Requires API key

- **Qwen ASR**: `qwen3-asr-flash` model
  - Fast cloud ASR service
  - Requires API key

### AI Text Processing APIs
- **OpenRouter**: Multi-provider LLM gateway
  - Requires API key
  - Supports multiple models

- **Groq LLM**: Alternative text processing backend
- **NVIDIA NIM**: Enterprise AI inference platform

### Model Distribution
- **GitHub Releases**: Automatic model download from project releases
  - Paraformer: 226MB archive
  - Zipformer: 112MB archive
- **Fallback**: Manual download instructions if auto-download fails

### System Services
- **Windows Audio**: DirectSound API via sounddevice
- **Windows Input**: SendInput API for text injection
- **Windows Registry**: Potential future use for auto-start configuration
