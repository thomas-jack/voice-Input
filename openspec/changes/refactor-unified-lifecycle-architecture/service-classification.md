# Service Classification for LifecycleComponent Migration

## Executive Summary

**Total Services Analyzed**: 58 classes across 46 files
- **Stateful Services** (Need LifecycleComponent): 24 services
- **Stateless Services** (No Lifecycle): 34 services (factories, utilities, helpers)

**Current LifecycleComponent Users**: 4 services
- AIService (uses old _do_initialize, _do_cleanup API)
- HotkeyService (uses old _do_initialize, _do_cleanup API)
- HistoryStorageService (uses old _do_initialize, _do_cleanup API)
- TrayController (uses old _do_initialize, _do_cleanup API)

**Migration Strategy**: Tier-based migration (Tier 0 → Tier 4)
**Estimated Effort**: 6-10 days for Phase 3.2

---

## Stateful Services (Need LifecycleComponent)

### Tier 0: Core Infrastructure (No Dependencies)

#### 1. DynamicEventSystem (EventBus)
- **File**: `src/sonicinput/core/services/dynamic_event_system.py`
- **Current State**: Standalone class, no lifecycle (has `cleanup()` method)
- **Resources Managed**: Event listeners, thread locks, listener cache
- **Lifecycle Methods Needed**:
  - `_do_start()`: Initialize builtin events, reset stats
  - `_do_stop()`: Clear listener cache, prepare for cleanup
  - Migrate `cleanup()` to `_do_stop()` cleanup logic
- **Dependencies**: NONE (Tier 0)
- **Breaking Changes**: Must add lifecycle state management
- **Priority**: CRITICAL (all services depend on this)
- **Estimated Effort**: 2 hours

**Current API**:
```python
def __init__(self): ...
def cleanup(self) -> None: ...  # Has cleanup, needs migration
```

**Target API**:
```python
class DynamicEventSystem(LifecycleComponent):
    def _do_start(self) -> bool: ...
    def _do_stop(self) -> bool: ...  # Move cleanup logic here
```

---

### Tier 1: Core Services (Depend on EventBus)

#### 2. RefactoredConfigService (ConfigService)
- **File**: `src/sonicinput/core/services/config/config_service_refactored.py`
- **Current State**: Standalone class with lifecycle-like methods
- **Resources Managed**: File watchers, config cache, file I/O
- **Lifecycle Methods Needed**:
  - `_do_start()`: Start file watcher, load config
  - `_do_stop()`: Stop file watcher, save pending changes
  - Migrate `cleanup()` to `_do_stop()` cleanup logic
- **Dependencies**: EventBus (optional)
- **Current Lifecycle Methods**: `cleanup()` (line 328)
- **Breaking Changes**: Add lifecycle state tracking
- **Priority**: HIGH (many services depend on this)
- **Estimated Effort**: 3 hours

**Current API**:
```python
def __init__(self, config_path=None, event_service=None): ...
def cleanup(self) -> None: ...  # Has cleanup
```

**Target API**:
```python
class RefactoredConfigService(LifecycleComponent):
    def _do_start(self) -> bool: ...
    def _do_stop(self) -> bool: ...
```

#### 3. StateManager
- **File**: `src/sonicinput/core/services/state_manager.py`
- **Current State**: Standalone class, no explicit lifecycle
- **Resources Managed**: State history, subscriber callbacks, thread locks
- **Lifecycle Methods Needed**:
  - `_do_start()`: Initialize default states
  - `_do_stop()`: Clear subscribers, notify shutdown
- **Dependencies**: EventBus (optional)
- **Current Lifecycle Methods**: None (only `__init__`)
- **Breaking Changes**: Add lifecycle state management
- **Priority**: HIGH
- **Estimated Effort**: 2 hours

---

### Tier 2: Business Services (Depend on Tier 0-1)

#### 4. AudioRecorder (AudioService)
- **File**: `src/sonicinput/audio/recorder.py`
- **Current State**: Implements IAudioService, has `cleanup()` method
- **Resources Managed**: PyAudio instances, audio streams, recording threads
- **Lifecycle Methods Needed**:
  - `_do_start()`: Initialize PyAudio, validate device
  - `_do_stop()`: Stop recording if active, close streams
  - Migrate `cleanup()` (line 720) to `_do_stop()` cleanup logic
- **Dependencies**: ConfigService (for device validation)
- **Current Lifecycle Methods**: `cleanup()` (line 720)
- **Breaking Changes**: Add lifecycle state management
- **Priority**: HIGH (recording is core feature)
- **Estimated Effort**: 3 hours

**Current API**:
```python
def __init__(self, sample_rate, channels, chunk_size, config_service): ...
def cleanup(self) -> None: ...  # Has cleanup
def start_recording(self, device_id): ...
def stop_recording(self) -> np.ndarray: ...
```

**Target API**:
```python
class AudioRecorder(LifecycleComponent, IAudioService):
    def _do_start(self) -> bool: ...  # Initialize PyAudio
    def _do_stop(self) -> bool: ...   # Cleanup resources
    # Keep existing methods
```

#### 5. RefactoredTranscriptionService (TranscriptionService)
- **File**: `src/sonicinput/core/services/transcription_service_refactored.py`
- **Current State**: Has `start()`, `stop()`, `cleanup()` methods (coordinator pattern)
- **Resources Managed**: ModelManager, StreamingCoordinator, TaskQueueManager, ErrorRecoveryService
- **Lifecycle Methods Needed**:
  - Migrate `start()` (line 103) to `_do_start()`
  - Migrate `stop()` (line 172) to `_do_stop()`
  - Migrate `cleanup()` (line 834) to `_do_stop()` cleanup logic
- **Dependencies**: ConfigService, EventBus
- **Current Lifecycle Methods**: `start()`, `stop()`, `cleanup()` (manual lifecycle)
- **Breaking Changes**: Replace manual lifecycle with LifecycleComponent
- **Priority**: CRITICAL (core feature)
- **Estimated Effort**: 4 hours

**Current API**:
```python
def start(self) -> None: ...      # Line 103
def stop(self, timeout) -> None: ...  # Line 172
def cleanup(self) -> None: ...    # Line 834
```

**Target API**:
```python
class RefactoredTranscriptionService(LifecycleComponent, ISpeechService):
    def _do_start(self) -> bool: ...
    def _do_stop(self) -> bool: ...
```

#### 6. AIService ✅ Already Using LifecycleComponent (OLD API)
- **File**: `src/sonicinput/core/services/ai_service.py`
- **Current State**: Inherits from old LifecycleComponent
- **Resources Managed**: AI client instances, HTTP connections
- **Lifecycle Methods Used**: `_do_initialize()`, `_do_start()`, `_do_stop()`, `_do_cleanup()`
- **Migration Needed**: Remove `_do_initialize()` and `_do_cleanup()`, consolidate into `_do_start()` and `_do_stop()`
- **Dependencies**: ConfigService
- **Priority**: HIGH
- **Estimated Effort**: 2 hours

**Current API** (old):
```python
def _do_initialize(self, config) -> bool: ...  # Line 63
def _do_start(self) -> bool: ...                # Line 103
def _do_stop(self) -> bool: ...                 # Line 112
def _do_cleanup(self) -> None: ...              # Line 121
```

**Target API** (new):
```python
def _do_start(self) -> bool: ...  # Merge initialize + start
def _do_stop(self) -> bool: ...   # Merge stop + cleanup
```

#### 7. HotkeyService ✅ Already Using LifecycleComponent (OLD API)
- **File**: `src/sonicinput/core/services/hotkey_service.py`
- **Current State**: Inherits from old LifecycleComponent
- **Resources Managed**: Hotkey manager (Win32HotkeyManager or PynputHotkeyManager)
- **Lifecycle Methods Used**: `_do_initialize()`, `_do_start()`, `_do_stop()`, `_do_cleanup()`
- **Migration Needed**: Remove `_do_initialize()` and `_do_cleanup()`, consolidate
- **Dependencies**: ConfigService, EventBus
- **Priority**: HIGH (system-wide hotkeys)
- **Estimated Effort**: 2 hours

#### 8. HistoryStorageService ✅ Already Using LifecycleComponent (OLD API)
- **File**: `src/sonicinput/core/services/storage/history_storage_service.py`
- **Current State**: Inherits from old LifecycleComponent
- **Resources Managed**: SQLite database connections, file storage
- **Lifecycle Methods Used**: `_do_initialize()`, `_do_start()`, `_do_stop()`, `_do_cleanup()`
- **Migration Needed**: Remove `_do_initialize()` and `_do_cleanup()`, consolidate
- **Dependencies**: ConfigService
- **Priority**: MEDIUM
- **Estimated Effort**: 2 hours

#### 9. StreamingCoordinator
- **File**: `src/sonicinput/core/services/streaming_coordinator.py`
- **Current State**: Has `start_streaming()`, `stop_streaming()`, `cleanup()` methods
- **Resources Managed**: Streaming chunks, realtime sessions (sherpa-onnx), streaming stats
- **Lifecycle Methods Needed**:
  - `_do_start()`: Initialize streaming infrastructure (if needed)
  - `_do_stop()`: Call `cleanup()` (line 627)
- **Dependencies**: EventBus (optional)
- **Current Lifecycle Methods**: `cleanup()` (line 627)
- **Breaking Changes**: Add lifecycle state management
- **Priority**: MEDIUM (used by TranscriptionService)
- **Estimated Effort**: 2 hours

**Note**: Already implements context manager (`__enter__`, `__exit__`) for resource safety.

#### 10. TaskQueueManager
- **File**: `src/sonicinput/core/services/task_queue_manager.py`
- **Current State**: Has `start()`, `stop()`, `cleanup()` methods (manual lifecycle)
- **Resources Managed**: Task queue, worker threads, task handlers
- **Lifecycle Methods Needed**:
  - Migrate `start()` (line 118) to `_do_start()`
  - Migrate `stop()` (line 143) and `cleanup()` (line 562) to `_do_stop()`
- **Dependencies**: EventBus (optional)
- **Current Lifecycle Methods**: `start()`, `stop()`, `cleanup()` (manual lifecycle)
- **Breaking Changes**: Replace manual lifecycle
- **Priority**: MEDIUM
- **Estimated Effort**: 2 hours

#### 11. ModelManager
- **File**: `src/sonicinput/core/services/model_manager.py`
- **Current State**: Has `start()`, `stop()` methods (manual lifecycle)
- **Resources Managed**: Whisper engine instances, model loading/unloading
- **Lifecycle Methods Needed**:
  - Migrate `start()` (line 49) to `_do_start()`
  - Migrate `stop()` (line 63) to `_do_stop()`
- **Dependencies**: EventBus (optional)
- **Current Lifecycle Methods**: `start()`, `stop()` (manual lifecycle)
- **Priority**: MEDIUM
- **Estimated Effort**: 2 hours

#### 12. ErrorRecoveryService
- **File**: `src/sonicinput/core/services/error_recovery_service.py`
- **Current State**: Has `cleanup()` method
- **Resources Managed**: Error recovery strategies, retry logic, cleanup callbacks
- **Lifecycle Methods Needed**:
  - `_do_start()`: Initialize recovery strategies
  - `_do_stop()`: Call `cleanup()` (line 641)
- **Dependencies**: EventBus (optional)
- **Current Lifecycle Methods**: `cleanup()` (line 641)
- **Priority**: LOW (error handling utility)
- **Estimated Effort**: 1 hour

#### 13. SmartTextInput (InputService)
- **File**: `src/sonicinput/input/smart_input.py`
- **Current State**: Implements IInputService, has mode switching
- **Resources Managed**: Input mode state, keyboard context
- **Lifecycle Methods Needed**:
  - `_do_start()`: Initialize input subsystem
  - `_do_stop()`: Cleanup mode state
- **Dependencies**: None
- **Current Lifecycle Methods**: `start_recording_mode()`, `stop_recording_mode()` (domain methods, not lifecycle)
- **Priority**: MEDIUM
- **Estimated Effort**: 1 hour

---

### Tier 3: Controllers (Depend on All Services)

#### 14. RecordingController
- **File**: `src/sonicinput/core/controllers/recording_controller.py`
- **Current State**: No lifecycle (just methods)
- **Resources Managed**: Recording state, audio recorder, streaming coordinator
- **Lifecycle Methods Needed**:
  - `_do_start()`: Setup controller (if needed)
  - `_do_stop()`: Ensure recording stopped, cleanup coordinator
- **Dependencies**: ConfigService, EventBus, StateManager, AudioRecorder, TranscriptionService
- **Current Lifecycle Methods**: None (has `start_recording()`, `stop_recording()` which are domain methods)
- **Breaking Changes**: Add lifecycle state management
- **Priority**: HIGH (core controller)
- **Estimated Effort**: 3 hours

**Note**: Uses StreamingCoordinator as context manager (already has resource safety).

#### 15. TranscriptionController
- **File**: `src/sonicinput/core/controllers/transcription_controller.py`
- **Current State**: Inherits from BaseController, no lifecycle
- **Resources Managed**: Transcription state, result tracking
- **Lifecycle Methods Needed**:
  - `_do_start()`: Setup controller
  - `_do_stop()`: Cleanup pending transcriptions
- **Dependencies**: ConfigService, EventBus, StateManager, TranscriptionService
- **Priority**: HIGH
- **Estimated Effort**: 2 hours

#### 16. AIProcessingController
- **File**: `src/sonicinput/core/controllers/ai_processing_controller.py`
- **Current State**: Inherits from BaseController, no lifecycle
- **Resources Managed**: AI processing state, request tracking
- **Lifecycle Methods Needed**:
  - `_do_start()`: Setup controller
  - `_do_stop()`: Cancel pending requests
- **Dependencies**: ConfigService, EventBus, StateManager, AIService
- **Priority**: HIGH
- **Estimated Effort**: 2 hours

#### 17. InputController
- **File**: `src/sonicinput/core/controllers/input_controller.py`
- **Current State**: Inherits from BaseController, no lifecycle
- **Resources Managed**: Input method state
- **Lifecycle Methods Needed**:
  - `_do_start()`: Setup controller
  - `_do_stop()`: Cleanup input state
- **Dependencies**: ConfigService, EventBus, StateManager, InputService
- **Priority**: MEDIUM
- **Estimated Effort**: 1 hour

---

### Tier 4: UI Components (Depend on Controllers)

#### 18. TrayController ✅ Already Using LifecycleComponent (OLD API)
- **File**: `src/sonicinput/ui/components/system_tray/tray_controller.py`
- **Current State**: Inherits from old LifecycleComponent
- **Resources Managed**: System tray widget, menu actions, Qt resources
- **Lifecycle Methods Used**: `_do_initialize()`, `_do_start()`, `_do_stop()`, `_do_cleanup()`
- **Migration Needed**: Remove `_do_initialize()` and `_do_cleanup()`, consolidate
- **Dependencies**: ConfigService, EventBus (via LifecycleComponent)
- **Priority**: MEDIUM (UI component)
- **Estimated Effort**: 2 hours

#### 19. TimerManager
- **File**: `src/sonicinput/ui/overlay_components/timer_manager.py`
- **Current State**: Standalone class with `cleanup()` method
- **Resources Managed**: QTimer instances, timer callbacks
- **Lifecycle Methods Needed**:
  - `_do_start()`: Initialize timer system
  - `_do_stop()`: Call `cleanup()` (line 179) - stop all timers
- **Dependencies**: None (Qt-based)
- **Priority**: LOW (UI utility)
- **Estimated Effort**: 1 hour

#### 20. AnimationController
- **File**: `src/sonicinput/ui/overlay_components/animation_controller.py`
- **Current State**: Standalone class with `cleanup()` method
- **Resources Managed**: QPropertyAnimation instances, animation state
- **Lifecycle Methods Needed**:
  - `_do_start()`: Initialize animation system
  - `_do_stop()`: Call `cleanup()` (line 162) - stop all animations
- **Dependencies**: None (Qt-based)
- **Priority**: LOW (UI utility)
- **Estimated Effort**: 1 hour

#### 21. RecordingOverlay
- **File**: `src/sonicinput/ui/recording_overlay.py`
- **Current State**: QWidget with `cleanup()` method
- **Resources Managed**: Qt widgets, timers, animations, audio visualizer
- **Lifecycle Methods Needed**:
  - `_do_start()`: Show overlay, start animations
  - `_do_stop()`: Call `cleanup()` (line 1085) - stop animations, hide overlay
- **Dependencies**: EventBus, StateManager (via signals)
- **Priority**: MEDIUM (main UI component)
- **Estimated Effort**: 2 hours

---

### Tier 5: Hotkey Managers (Platform-Specific)

#### 22. Win32HotkeyManager
- **File**: `src/sonicinput/core/hotkey_manager_win32.py`
- **Current State**: Implements IHotkeyService, has `start_listening()`, `stop_listening()` methods
- **Resources Managed**: Win32 message loop thread, hotkey registrations
- **Lifecycle Methods Needed**:
  - Migrate `start_listening()` (line 569) to `_do_start()`
  - Migrate `stop_listening()` (line 608) to `_do_stop()`
- **Dependencies**: None (platform API)
- **Priority**: HIGH (system hotkeys)
- **Estimated Effort**: 2 hours

#### 23. PynputHotkeyManager
- **File**: `src/sonicinput/core/hotkey_manager_pynput.py`
- **Current State**: Implements IHotkeyService, has `start_listening()`, `stop_listening()` methods
- **Resources Managed**: pynput listener thread, hotkey state
- **Lifecycle Methods Needed**:
  - Migrate `start_listening()` (line 708) to `_do_start()`
  - Migrate `stop_listening()` (line 739) to `_do_stop()`
- **Dependencies**: None (pynput library)
- **Priority**: HIGH (system hotkeys)
- **Estimated Effort**: 2 hours

---

### Tier 6: Speech Engines (Provider-Specific)

#### 24. SherpaEngine
- **File**: `src/sonicinput/speech/sherpa_engine.py`
- **Current State**: Implements ISpeechService, manages sherpa-onnx models
- **Resources Managed**: Sherpa-ONNX recognizer instances, model files
- **Lifecycle Methods Needed**:
  - `_do_start()`: Load model if auto_load enabled
  - `_do_stop()`: Unload model, cleanup recognizer
- **Dependencies**: ConfigService (for model path)
- **Priority**: HIGH (local transcription)
- **Estimated Effort**: 2 hours

**Note**: Cloud engines (GroqSpeechService, SiliconFlowEngine, QwenEngine) are stateless - they create HTTP clients per request.

---

## Stateless Services (No Lifecycle Needed)

### Factories (Pure Functions)

1. **SpeechServiceFactory** (`src/sonicinput/speech/speech_service_factory.py`)
   - Pure factory methods: `create_service()`, `create_from_config()`
   - No state, no resources

2. **AIClientFactory** (`src/sonicinput/ai/factory.py`)
   - Pure factory methods: `create_client()`, `create_from_config()`
   - No state, no resources

### Utilities (Helpers)

3. **ConfigValidator** (`src/sonicinput/core/services/config/config_validator.py`)
   - Pure validation functions
   - No state, no resources

4. **ConfigReader** (`src/sonicinput/core/services/config/config_reader.py`)
   - File I/O utility
   - No persistent state (stateless)

5. **ConfigWriter** (`src/sonicinput/core/services/config/config_writer.py`)
   - File I/O utility with `cleanup()` for temp file cleanup
   - Could use context manager instead of lifecycle

6. **ConfigBackup** (`src/sonicinput/core/services/config/config_backup.py`)
   - File backup utility
   - No persistent state

7. **ConfigMigrator** (`src/sonicinput/core/services/config/config_migrator.py`)
   - Pure migration functions
   - No state

8. **ConfigKeys** (`src/sonicinput/core/services/config/config_keys.py`)
   - Constants class
   - No state, no methods

9. **AudioProcessor** (`src/sonicinput/audio/processor.py`)
   - Pure audio processing functions
   - No state (stateless processing)

10. **AudioVisualizer** (`src/sonicinput/audio/visualizer.py`)
    - Qt widget with `cleanup()` method
    - Could use Qt parent-child cleanup instead

11. **SherpaModelManager** (`src/sonicinput/speech/sherpa_models.py`)
    - Model download utility
    - No persistent state (one-time operations)

12. **HTTPClientManager** (`src/sonicinput/ai/http_client_manager.py`)
    - HTTP client pool manager
    - Could benefit from lifecycle for connection pooling (FUTURE)

13. **PerformanceMonitor** (`src/sonicinput/ai/performance_monitor.py`)
    - Metrics collection utility
    - No persistent state

14. **BaseAIClient** (`src/sonicinput/ai/base_client.py`)
    - Abstract base class for AI clients
    - Implementations are stateless (HTTP requests)

### Cloud Providers (Stateless HTTP Clients)

15. **GroqSpeechService** (`src/sonicinput/speech/groq_speech_service.py`)
    - HTTP client, creates sessions per request
    - `initialize()` is config setup, not lifecycle

16. **SiliconFlowEngine** (`src/sonicinput/speech/siliconflow_engine.py`)
    - HTTP client, creates sessions per request
    - `initialize()` is config setup

17. **QwenEngine** (`src/sonicinput/speech/qwen_engine.py`)
    - HTTP client, creates sessions per request
    - `initialize()` is config setup

18. **GroqClient** (`src/sonicinput/ai/groq.py`)
    - HTTP client wrapper
    - No persistent state

19. **NvidiaClient** (`src/sonicinput/ai/nvidia.py`)
    - HTTP client wrapper
    - No persistent state

20. **OpenAICompatibleClient** (`src/sonicinput/ai/openai_compatible.py`)
    - HTTP client wrapper
    - No persistent state

21. **OpenRouterClient** (`src/sonicinput/ai/openrouter.py`)
    - HTTP client wrapper
    - No persistent state

### UI Utilities (Qt-Managed)

22. **PositionManager** (`src/sonicinput/ui/overlay_components/position_manager.py`)
    - Position calculation utility
    - No persistent state

23. **PositionManager** (`src/sonicinput/ui/controllers/position_manager.py`)
    - Duplicate position manager
    - No persistent state

24. **AnimationEngine** (`src/sonicinput/ui/controllers/animation_engine.py`)
    - Qt animation wrapper
    - No persistent state (animations are stateless)

25. **TextDiffHelper** (`src/sonicinput/core/controllers/text_diff_helper.py`)
    - Text diff utility
    - No state

26. **ControllerLogging** (`src/sonicinput/core/controllers/logging_helper.py`)
    - Logging helper
    - No state

### Service Infrastructure (Registry/Container)

27. **ServiceRegistry** (`src/sonicinput/core/services/service_registry.py`)
    - Service registration utility
    - No lifecycle (registry is just a dict)

28. **ServiceRegistryConfig** (`src/sonicinput/core/services/service_registry_config.py`)
    - Configuration for service registry
    - No state

29. **DIContainer** (`src/sonicinput/core/di_container.py`)
    - Dependency injection container
    - Manages singleton instances but doesn't need lifecycle itself

30. **EnhancedDIContainer** (`src/sonicinput/core/di_container_enhanced.py`)
    - Legacy DI container with `cleanup()` method
    - Will be replaced by new DIContainer

### Other Services

31. **HotReloadManager** (`src/sonicinput/core/services/hot_reload_manager.py`)
    - Config reload coordinator
    - No persistent state (just callback registry)

32. **PluginManager** (`src/sonicinput/core/services/plugin_manager.py`)
    - Plugin loading utility
    - No persistent state

33. **UIServices** (`src/sonicinput/core/services/ui_services.py`)
    - UI service facades (UIMainService, UISettingsService, UIModelService, UIAudioService, UIGPUService)
    - Adapters, no persistent state

34. **UIServiceAdapter** (`src/sonicinput/core/services/ui_service_adapter.py`)
    - UI service adapters
    - No persistent state

---

## Migration Order (Dependency-Based)

### Wave 1: Foundation (No Dependencies) - Day 1
1. **DynamicEventSystem** (EventBus) - 2 hours

### Wave 2: Core Services (Depend on EventBus) - Day 2
2. **RefactoredConfigService** - 3 hours
3. **StateManager** - 2 hours

### Wave 3: Business Services (Depend on Core) - Day 3-5
4. **AudioRecorder** - 3 hours
5. **SmartTextInput** - 1 hour
6. **AIService** (migrate from old API) - 2 hours
7. **HotkeyService** (migrate from old API) - 2 hours
8. **HistoryStorageService** (migrate from old API) - 2 hours
9. **StreamingCoordinator** - 2 hours
10. **TaskQueueManager** - 2 hours
11. **ModelManager** - 2 hours
12. **ErrorRecoveryService** - 1 hour
13. **RefactoredTranscriptionService** - 4 hours
14. **SherpaEngine** - 2 hours
15. **Win32HotkeyManager** - 2 hours
16. **PynputHotkeyManager** - 2 hours

### Wave 4: Controllers (Depend on Services) - Day 6-7
17. **RecordingController** - 3 hours
18. **TranscriptionController** - 2 hours
19. **AIProcessingController** - 2 hours
20. **InputController** - 1 hour

### Wave 5: UI Components (Depend on Controllers) - Day 8
21. **TrayController** (migrate from old API) - 2 hours
22. **RecordingOverlay** - 2 hours
23. **TimerManager** - 1 hour
24. **AnimationController** - 1 hour

---

## Breaking Changes Summary

### Old LifecycleComponent API (4 methods)
```python
def _do_initialize(self, config: Dict[str, Any]) -> bool: ...
def _do_start(self) -> bool: ...
def _do_stop(self) -> bool: ...
def _do_cleanup(self) -> None: ...
```

### New LifecycleComponent API (2 methods)
```python
def _do_start(self) -> bool: ...
def _do_stop(self) -> bool: ...
```

### Migration Pattern
**For services using old API** (AIService, HotkeyService, HistoryStorageService, TrayController):
1. Move `_do_initialize()` logic to `_do_start()`
2. Move `_do_cleanup()` logic to `_do_stop()`
3. Keep `_do_start()` and `_do_stop()` as-is (but adjust cleanup)
4. Remove config parameter from `_do_start()` (use `self._config_service` instead)

**For services with manual lifecycle** (TranscriptionService, TaskQueueManager, ModelManager):
1. Replace `start()` method with `_do_start()`
2. Replace `stop()` and `cleanup()` methods with `_do_stop()`
3. Add LifecycleComponent inheritance

**For services with only cleanup** (EventBus, ConfigService, AudioRecorder, StreamingCoordinator, ErrorRecoveryService):
1. Add `_do_start()` method (initialize resources)
2. Move `cleanup()` logic to `_do_stop()`
3. Add LifecycleComponent inheritance

---

## Estimated Effort Breakdown

**Total Effort**: 51 hours (6.4 days at 8 hours/day)

### By Wave
- **Wave 1**: 2 hours (0.25 days)
- **Wave 2**: 5 hours (0.6 days)
- **Wave 3**: 23 hours (2.9 days)
- **Wave 4**: 8 hours (1 day)
- **Wave 5**: 6 hours (0.75 days)
- **Testing & Fixes**: 7 hours (0.9 days)

### By Priority
- **Critical**: 10 hours (EventBus, TranscriptionService)
- **High**: 27 hours (ConfigService, AudioRecorder, AIService, HotkeyService, Controllers, Hotkey Managers, SherpaEngine)
- **Medium**: 10 hours (StateManager, HistoryStorageService, StreamingCoordinator, TaskQueueManager, ModelManager, InputController, TrayController, RecordingOverlay)
- **Low**: 4 hours (ErrorRecoveryService, TimerManager, AnimationController)

---

## Verification Checklist

After migration, verify:
- [ ] All 24 stateful services inherit from new LifecycleComponent
- [ ] All services implement only `_do_start()` and `_do_stop()`
- [ ] No services use old `_do_initialize()` or `_do_cleanup()` methods
- [ ] All `cleanup()` methods are removed or migrated to `_do_stop()`
- [ ] All manual lifecycle methods (`start()`, `stop()`) are replaced
- [ ] Dependency order is correct (Tier 0 → Tier 1 → ... → Tier 5)
- [ ] Application starts successfully (all services initialize)
- [ ] Application stops cleanly (all services cleanup)
- [ ] No resource leaks (memory, file handles, threads)
- [ ] All smoke tests pass (`--test`, `--gui`, `--diagnostics`)

---

## Notes

1. **ConfigWriter** has a `cleanup()` method but is used as a context manager - consider removing lifecycle and relying on `__exit__` instead.

2. **HTTPClientManager** could benefit from lifecycle for connection pooling optimization, but currently operates statelessly. Mark as FUTURE enhancement.

3. **Cloud speech engines** (Groq, SiliconFlow, Qwen) have `initialize()` methods but these are config setup, not lifecycle - they remain stateless.

4. **UI components** (AudioVisualizer, TimerManager, AnimationController, RecordingOverlay) have `cleanup()` methods - these could use Qt parent-child cleanup, but adding lifecycle is safer for explicit resource management.

5. **Hotkey managers** (Win32, Pynput) have `start_listening()` and `stop_listening()` - these are lifecycle methods and should be migrated.

6. **SherpaEngine** manages model loading/unloading - this is definitely stateful and needs lifecycle.

7. **BaseController** is abstract and doesn't need lifecycle itself, but all concrete controllers should have it.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-21
**Status**: Complete - Ready for Phase 3.2
