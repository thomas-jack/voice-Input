"""Win32 RegisterHotKey implementation - no admin privileges required

This implementation uses Windows RegisterHotKey API instead of low-level keyboard hooks.

Advantages:
- No administrator privileges required
- Works across privilege boundaries (not blocked by UIPI)
- Better performance (no hook overhead)
- Official Windows API for global hotkeys

Trade-offs:
- Cannot suppress hotkey events (they still reach active window)
- Can conflict with other applications' hotkeys
"""

import win32gui
import win32con
import win32api
from typing import Callable, Dict, Optional
import threading
import queue
from ..utils import HotkeyRegistrationError, app_logger
from .interfaces import IHotkeyService


class HotkeyConflictError(Exception):
    """Hotkey already registered by another application"""

    def __init__(self, hotkey: str, error_code: int = None):
        self.hotkey = hotkey
        self.error_code = error_code

        message = f"Hotkey '{hotkey}' is already in use by another application"
        if error_code:
            message += f" (error code: {error_code})"

        super().__init__(message)

        # Suggest alternative hotkeys
        self.suggestions = self._generate_suggestions(hotkey)

    @staticmethod
    def _generate_suggestions(conflicting_hotkey: str) -> list:
        """Generate alternative hotkey suggestions

        Args:
            conflicting_hotkey: The hotkey that conflicts

        Returns:
            List of suggested alternative hotkeys
        """
        # Common alternative hotkeys that are less likely to conflict
        common_alternatives = [
            "alt+h",
            "ctrl+shift+v",
            "ctrl+alt+v",
            "f11",
            "f10",
            "alt+shift+v",
            "ctrl+shift+h",
        ]

        # Filter out the conflicting one
        normalized = conflicting_hotkey.lower().strip()
        suggestions = [h for h in common_alternatives if h != normalized]

        # Limit to top 3
        return suggestions[:3]


class Win32HotkeyManager(IHotkeyService):
    """Windows RegisterHotKey based hotkey manager

    Uses Windows RegisterHotKey API for global hotkey detection.
    Does not require administrator privileges.
    """

    # Modifier key mapping
    MOD_ALT = win32con.MOD_ALT
    MOD_CONTROL = win32con.MOD_CONTROL
    MOD_SHIFT = win32con.MOD_SHIFT
    MOD_WIN = win32con.MOD_WIN

    # Virtual key code mapping
    VK_MAP = {
        'f1': win32con.VK_F1,
        'f2': win32con.VK_F2,
        'f3': win32con.VK_F3,
        'f4': win32con.VK_F4,
        'f5': win32con.VK_F5,
        'f6': win32con.VK_F6,
        'f7': win32con.VK_F7,
        'f8': win32con.VK_F8,
        'f9': win32con.VK_F9,
        'f10': win32con.VK_F10,
        'f11': win32con.VK_F11,
        'f12': win32con.VK_F12,
        'a': ord('A'),
        'b': ord('B'),
        'c': ord('C'),
        'd': ord('D'),
        'e': ord('E'),
        'f': ord('F'),
        'g': ord('G'),
        'h': ord('H'),
        'i': ord('I'),
        'j': ord('J'),
        'k': ord('K'),
        'l': ord('L'),
        'm': ord('M'),
        'n': ord('N'),
        'o': ord('O'),
        'p': ord('P'),
        'q': ord('Q'),
        'r': ord('R'),
        's': ord('S'),
        't': ord('T'),
        'u': ord('U'),
        'v': ord('V'),
        'w': ord('W'),
        'x': ord('X'),
        'y': ord('Y'),
        'z': ord('Z'),
        '0': ord('0'),
        '1': ord('1'),
        '2': ord('2'),
        '3': ord('3'),
        '4': ord('4'),
        '5': ord('5'),
        '6': ord('6'),
        '7': ord('7'),
        '8': ord('8'),
        '9': ord('9'),
        'space': win32con.VK_SPACE,
        'enter': win32con.VK_RETURN,
        'esc': win32con.VK_ESCAPE,
        'tab': win32con.VK_TAB,
        'backspace': win32con.VK_BACK,
        'delete': win32con.VK_DELETE,
        'insert': win32con.VK_INSERT,
        'home': win32con.VK_HOME,
        'end': win32con.VK_END,
        'pageup': win32con.VK_PRIOR,
        'pagedown': win32con.VK_NEXT,
        'up': win32con.VK_UP,
        'down': win32con.VK_DOWN,
        'left': win32con.VK_LEFT,
        'right': win32con.VK_RIGHT,
    }

    def __init__(self, callback: Callable[[str], None]):
        """Initialize Win32 hotkey manager

        Args:
            callback: Callback function called when hotkey is triggered
        """
        self.callback = callback
        self.registered_hotkeys: Dict[str, Dict] = {}  # hotkey_str -> {id, action, modifiers, vk}
        self._hwnd: Optional[int] = None
        self._is_listening_flag = False
        self._message_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._next_hotkey_id = 1
        self._command_queue = queue.Queue()

        app_logger.log_audio_event(
            "Win32 hotkey manager initialized (RegisterHotKey)", {}
        )

    @property
    def is_listening(self) -> bool:
        """Whether hotkey listening is active"""
        return self._is_listening_flag

    def _parse_hotkey(self, hotkey_str: str) -> tuple[int, int]:
        """Parse hotkey string to modifiers and virtual key code

        Args:
            hotkey_str: Hotkey string like "ctrl+shift+v" or "f12"

        Returns:
            (modifiers, virtual_key) tuple

        Raises:
            HotkeyRegistrationError: Invalid hotkey format
        """
        parts = [part.strip().lower() for part in hotkey_str.split('+')]

        modifiers = 0
        vk = 0

        for part in parts:
            if part in ('ctrl', 'control'):
                modifiers |= self.MOD_CONTROL
            elif part in ('alt', 'menu'):
                modifiers |= self.MOD_ALT
            elif part == 'shift':
                modifiers |= self.MOD_SHIFT
            elif part in ('win', 'windows', 'super'):
                modifiers |= self.MOD_WIN
            elif part in self.VK_MAP:
                if vk != 0:
                    raise HotkeyRegistrationError(
                        f"Invalid hotkey '{hotkey_str}': multiple keys specified"
                    )
                vk = self.VK_MAP[part]
            else:
                raise HotkeyRegistrationError(
                    f"Invalid hotkey '{hotkey_str}': unknown key '{part}'"
                )

        if vk == 0:
            raise HotkeyRegistrationError(
                f"Invalid hotkey '{hotkey_str}': no key specified"
            )

        return modifiers, vk

    def _normalize_hotkey(self, hotkey_str: str) -> str:
        """Normalize hotkey string format

        Args:
            hotkey_str: Raw hotkey string

        Returns:
            Normalized hotkey string
        """
        parts = [part.strip().lower() for part in hotkey_str.split('+')]

        # Order: ctrl, alt, shift, win, key
        modifiers = []
        key = None

        for part in parts:
            if part in ('ctrl', 'control'):
                if 'ctrl' not in modifiers:
                    modifiers.append('ctrl')
            elif part in ('alt', 'menu'):
                if 'alt' not in modifiers:
                    modifiers.append('alt')
            elif part == 'shift':
                if 'shift' not in modifiers:
                    modifiers.append('shift')
            elif part in ('win', 'windows', 'super'):
                if 'win' not in modifiers:
                    modifiers.append('win')
            else:
                key = part

        # Build normalized string
        result = '+'.join(modifiers)
        if key:
            if result:
                result += '+' + key
            else:
                result = key

        return result

    def _wndproc(self, hwnd, msg, wparam, lparam):
        """Window procedure for message-only window

        Handles WM_HOTKEY messages from RegisterHotKey
        """
        if msg == win32con.WM_HOTKEY:
            hotkey_id = wparam

            # Find hotkey by ID
            for hotkey_str, info in self.registered_hotkeys.items():
                if info['id'] == hotkey_id:
                    action = info['action']

                    app_logger.log_audio_event(
                        "Win32 hotkey triggered",
                        {
                            "hotkey": hotkey_str,
                            "action": action,
                            "id": hotkey_id
                        },
                    )

                    app_logger.log_hotkey_event(hotkey_str, action)

                    # Execute callback in separate thread to avoid blocking message loop
                    threading.Thread(
                        target=self._execute_callback,
                        args=(action,),
                        daemon=True
                    ).start()

                    break

        elif msg == win32con.WM_CLOSE:
            win32gui.DestroyWindow(hwnd)
        elif msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)

        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _execute_callback(self, action: str):
        """Execute hotkey callback

        Args:
            action: Action name to pass to callback
        """
        try:
            if self.callback:
                self.callback(action)
                app_logger.log_audio_event(
                    "Win32 hotkey callback completed", {"action": action}
                )
        except Exception as e:
            app_logger.log_error(e, f"win32_hotkey_callback_{action}")

    def _message_loop(self):
        """Message loop thread for receiving WM_HOTKEY messages"""
        try:
            # Register window class
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self._wndproc
            wc.lpszClassName = "SonicInputHotkeyWindow"
            wc.hInstance = win32api.GetModuleHandle(None)

            try:
                class_atom = win32gui.RegisterClass(wc)
            except Exception as e:
                # Class might already be registered
                class_atom = win32gui.WNDCLASS()
                app_logger.log_audio_event(
                    "Window class already registered (expected)", {}
                )

            # Create message-only window
            self._hwnd = win32gui.CreateWindow(
                wc.lpszClassName,
                "SonicInput Hotkey Window",
                0, 0, 0, 0, 0,
                win32con.HWND_MESSAGE,  # Message-only window
                0,
                wc.hInstance,
                None
            )

            app_logger.log_audio_event(
                "Win32 message window created",
                {"hwnd": self._hwnd}
            )

            # Signal that window is ready
            self._is_listening_flag = True

            # Process queued registration commands
            while not self._command_queue.empty():
                try:
                    cmd = self._command_queue.get_nowait()
                    cmd()
                except queue.Empty:
                    break
                except Exception as e:
                    # Log errors from command execution but continue processing
                    app_logger.log_error(e, "command_queue_execution")
                    # Don't break - continue processing other commands

            # Message loop
            while not self._stop_event.is_set():
                try:
                    # Process Windows messages with timeout
                    msg = win32gui.GetMessage(self._hwnd, 0, 0)
                    if msg[1][1] == win32con.WM_QUIT:
                        break
                    win32gui.TranslateMessage(msg[1])
                    win32gui.DispatchMessage(msg[1])
                except Exception as e:
                    if not self._stop_event.is_set():
                        app_logger.log_error(e, "win32_message_loop")
                    break

        except Exception as e:
            app_logger.log_error(e, "win32_message_loop_init")
        finally:
            self._is_listening_flag = False
            if self._hwnd:
                try:
                    win32gui.DestroyWindow(self._hwnd)
                except:
                    pass
                self._hwnd = None

    def register_hotkey(self, hotkey: str, action: str = "toggle_recording") -> bool:
        """Register global hotkey using RegisterHotKey API

        Args:
            hotkey: Hotkey string (e.g., "ctrl+shift+v", "f12")
            action: Action name to pass to callback

        Returns:
            True if registration successful

        Raises:
            HotkeyRegistrationError: Invalid hotkey format
            HotkeyConflictError: Hotkey already in use by another application
        """
        if not hotkey:
            raise HotkeyRegistrationError("Hotkey string cannot be empty")

        # Normalize hotkey string
        normalized_hotkey = self._normalize_hotkey(hotkey)

        # Unregister if already exists
        if normalized_hotkey in self.registered_hotkeys:
            self.unregister_hotkey(normalized_hotkey)

        try:
            # Parse hotkey
            modifiers, vk = self._parse_hotkey(normalized_hotkey)

            # Assign ID
            hotkey_id = self._next_hotkey_id
            self._next_hotkey_id += 1

            # Variables to capture result/error from register_command
            registration_error = None
            registration_complete = threading.Event()

            # Register hotkey (must be done in message loop thread)
            def register_command():
                nonlocal registration_error
                try:
                    success = win32gui.RegisterHotKey(
                        self._hwnd,
                        hotkey_id,
                        modifiers,
                        vk
                    )

                    if not success:
                        error_code = win32api.GetLastError()
                        registration_error = HotkeyConflictError(normalized_hotkey, error_code)
                        return

                    # Store registration info
                    self.registered_hotkeys[normalized_hotkey] = {
                        'id': hotkey_id,
                        'action': action,
                        'modifiers': modifiers,
                        'vk': vk
                    }

                    app_logger.log_audio_event(
                        "Win32 hotkey registered",
                        {
                            "hotkey": normalized_hotkey,
                            "action": action,
                            "id": hotkey_id,
                            "modifiers": modifiers,
                            "vk": vk
                        },
                    )

                except Exception as e:
                    app_logger.log_error(e, "register_hotkey_win32")
                    registration_error = e
                finally:
                    registration_complete.set()

            if self._hwnd:
                # Window already exists, register immediately
                register_command()
                # Check if there was an error
                if registration_error:
                    raise registration_error
            else:
                # Queue command for when window is created
                self._command_queue.put(register_command)
                # Wait for completion (with timeout)
                if registration_complete.wait(timeout=1.0):
                    if registration_error:
                        raise registration_error
                else:
                    # Timeout - will be registered when message loop starts
                    pass

            return True

        except Exception as e:
            app_logger.log_error(e, f"register_hotkey_{normalized_hotkey}")
            raise

    def unregister_hotkey(self, hotkey: str) -> bool:
        """Unregister hotkey

        Args:
            hotkey: Hotkey string

        Returns:
            True if unregistration successful
        """
        normalized_hotkey = self._normalize_hotkey(hotkey)

        if normalized_hotkey not in self.registered_hotkeys:
            return False

        info = self.registered_hotkeys[normalized_hotkey]
        hotkey_id = info['id']

        try:
            if self._hwnd:
                win32gui.UnregisterHotKey(self._hwnd, hotkey_id)

            del self.registered_hotkeys[normalized_hotkey]

            app_logger.log_audio_event(
                "Win32 hotkey unregistered",
                {"hotkey": normalized_hotkey, "id": hotkey_id},
            )

            return True

        except Exception as e:
            app_logger.log_error(e, f"unregister_hotkey_{normalized_hotkey}")
            return False

    def unregister_all_hotkeys(self) -> None:
        """Unregister all hotkeys"""
        hotkeys = list(self.registered_hotkeys.keys())
        for hotkey in hotkeys:
            self.unregister_hotkey(hotkey)

    def start_listening(self) -> bool:
        """Start hotkey listening

        Creates message window and starts message loop thread

        Returns:
            True if listening started successfully
        """
        if self._is_listening_flag:
            app_logger.log_audio_event("Win32 hotkey already listening", {})
            return True

        try:
            self._stop_event.clear()

            # Start message loop thread
            self._message_thread = threading.Thread(
                target=self._message_loop,
                daemon=True,
                name="Win32HotkeyMessageLoop"
            )
            self._message_thread.start()

            # Wait for window creation
            import time
            for _ in range(50):  # Wait up to 5 seconds
                if self._is_listening_flag:
                    break
                time.sleep(0.1)

            if not self._is_listening_flag:
                raise RuntimeError("Failed to start message loop")

            app_logger.log_audio_event("Win32 hotkey listening started", {})
            return True

        except Exception as e:
            app_logger.log_error(e, "start_listening_win32")
            return False

    def stop_listening(self) -> None:
        """Stop hotkey listening"""
        if not self._is_listening_flag:
            return

        try:
            # Unregister all hotkeys
            self.unregister_all_hotkeys()

            # Signal stop
            self._stop_event.set()

            # Post quit message
            if self._hwnd:
                try:
                    win32gui.PostMessage(self._hwnd, win32con.WM_QUIT, 0, 0)
                except:
                    pass

            # Wait for thread
            if self._message_thread and self._message_thread.is_alive():
                self._message_thread.join(timeout=2.0)

            self._is_listening_flag = False
            self._message_thread = None

            app_logger.log_audio_event("Win32 hotkey listening stopped", {})

        except Exception as e:
            app_logger.log_error(e, "stop_listening_win32")

    def get_registered_hotkeys(self) -> Dict[str, str]:
        """Get registered hotkeys

        Returns:
            Dict mapping hotkey string to action name
        """
        return {
            hotkey: info['action']
            for hotkey, info in self.registered_hotkeys.items()
        }

    def reload(self) -> None:
        """Reload hotkey configuration

        Re-registers all hotkeys (compatibility method)
        """
        # Store current hotkeys
        current_hotkeys = list(self.registered_hotkeys.items())

        # Unregister all
        self.unregister_all_hotkeys()

        # Re-register
        for hotkey, info in current_hotkeys:
            try:
                self.register_hotkey(hotkey, info['action'])
            except Exception as e:
                app_logger.log_error(e, f"reload_hotkey_{hotkey}")
