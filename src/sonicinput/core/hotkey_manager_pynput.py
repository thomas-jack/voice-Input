"""全局快捷键管理器 - 使用pynput替代keyboard库

This implementation uses low-level keyboard hooks (SetWindowsHookEx with WH_KEYBOARD_LL).

Advantages:
- Can suppress hotkey events (prevent them from reaching active window)
- Full control over keyboard event processing

Trade-offs:
- May require administrator privileges for reliable operation across privilege boundaries
- Blocked by UIPI (User Interface Privilege Isolation) when monitoring elevated windows
- Higher performance overhead (hooks all keyboard events)

Recommended for users running the application in administrator mode.
"""

from pynput import keyboard
from pynput.keyboard import Key, KeyCode, HotKey
import time
from typing import Callable, Dict, Set, Optional, Any, Union
from ..utils import HotkeyRegistrationError, app_logger
from .interfaces import IHotkeyService

# Windows 虚拟键码常量
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104  # Alt 组合键
WM_SYSKEYUP = 0x0105

VK_LMENU = 0xA4  # Left Alt
VK_RMENU = 0xA5  # Right Alt
VK_LCONTROL = 0xA2  # Left Ctrl
VK_RCONTROL = 0xA3  # Right Ctrl
VK_LSHIFT = 0xA0  # Left Shift
VK_RSHIFT = 0xA1  # Right Shift
VK_LWIN = 0x5B  # Left Windows
VK_RWIN = 0x5C  # Right Windows


class PynputHotkeyManager(IHotkeyService):
    """全局快捷键管理 - 基于pynput实现 (需要管理员权限以获得最佳体验)"""

    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.registered_hotkeys: Dict[
            str, Dict[str, Any]
        ] = {}  # hotkey_string -> {hotkey_obj, action, keys}
        self._listener: Optional[keyboard.Listener] = None
        self._is_listening_flag = False

        app_logger.log_audio_event(
            "Pynput hotkey manager initialized (win32_event_filter)", {}
        )

    @property
    def is_listening(self) -> bool:
        """是否正在监听快捷键"""
        return self._is_listening_flag

    def register_hotkey(self, hotkey: str, action: str = "toggle_recording") -> bool:
        """注册全局快捷键 - pynput版本"""
        if not hotkey:
            raise HotkeyRegistrationError("Hotkey string cannot be empty")

        # 先注销已存在的快捷键
        if hotkey in self.registered_hotkeys:
            self.unregister_hotkey(hotkey)

        try:
            # 规范化快捷键字符串
            normalized_hotkey = self._normalize_hotkey(hotkey)

            # 测试快捷键可用性
            availability_test = self.test_hotkey_availability(hotkey)
            if not availability_test["available"]:
                app_logger.log_audio_event(
                    "Hotkey unavailable",
                    {"hotkey": hotkey, "reason": availability_test["message"]},
                )
                raise HotkeyRegistrationError(
                    f"Hotkey '{hotkey}' is not available: {availability_test['message']}"
                )

            # 解析热键为pynput格式
            pynput_keys = self._parse_hotkey_to_pynput(normalized_hotkey)

            # 创建回调函数
            def hotkey_callback():
                try:
                    app_logger.log_audio_event(
                        "Hotkey triggered",
                        {
                            "hotkey": normalized_hotkey,
                            "action": action,
                            "timestamp": time.time(),
                        },
                    )

                    app_logger.log_hotkey_event(normalized_hotkey, action)

                    if self.callback:
                        self.callback(action)
                        app_logger.log_audio_event(
                            "Hotkey callback completed", {"action": action}
                        )

                except Exception as e:
                    app_logger.log_error(e, f"hotkey_callback_{action}")

            # 创建 HotKey 对象
            hotkey_obj = HotKey(pynput_keys, hotkey_callback)

            # 保存热键信息
            self.registered_hotkeys[hotkey] = {
                "hotkey_obj": hotkey_obj,
                "action": action,
                "normalized": normalized_hotkey,
                "keys": pynput_keys,
            }

            # 重启listener以应用新热键
            self._restart_listener()

            app_logger.log_audio_event(
                "Hotkey registered (pynput)",
                {
                    "hotkey": hotkey,
                    "normalized": normalized_hotkey,
                    "action": action,
                    "availability_tested": True,
                },
            )

            return True

        except Exception as e:
            app_logger.log_error(e, f"register_hotkey_{hotkey}")
            raise HotkeyRegistrationError(f"Failed to register hotkey '{hotkey}': {e}")

    def _parse_hotkey_to_pynput(self, hotkey: str) -> Set:
        """转换热键字符串为pynput格式

        Args:
            hotkey: 标准格式如 "alt+h" 或 "ctrl+shift+a"

        Returns:
            pynput键集合，如 {Key.alt_l, KeyCode.from_char('h')}
        """
        keys = set()
        parts = hotkey.lower().split("+")

        for part in parts:
            part = part.strip()
            if part == "ctrl" or part == "control":
                keys.add(Key.ctrl_l)
            elif part == "alt":
                keys.add(Key.alt_l)
            elif part == "shift":
                keys.add(Key.shift_l)
            elif part == "cmd" or part == "windows" or part == "win":
                keys.add(Key.cmd)
            elif len(part) == 1:
                # 单个字符
                keys.add(KeyCode.from_char(part))
            else:
                # 特殊键
                try:
                    keys.add(getattr(Key, part))
                except AttributeError:
                    app_logger.log_audio_event(
                        "Unknown key in hotkey", {"key": part, "hotkey": hotkey}
                    )

        return keys

    def _normalize_key(self, key) -> Any:
        """规范化按键（将右侧修饰键转换为左侧）"""
        # 将右侧修饰键映射到左侧以便比较
        if key == Key.alt_r or key == Key.alt_gr:
            return Key.alt_l
        elif key == Key.ctrl_r:
            return Key.ctrl_l
        elif key == Key.shift_r:
            return Key.shift_l
        return key

    def _normalize_key_set(self, keys: Set) -> Set:
        """规范化按键集合"""
        return {self._normalize_key(k) for k in keys}

    def _vk_to_pynput_key(self, vk_code: int) -> Optional[Union[Key, KeyCode]]:
        """将 Windows VK 码转换为 pynput Key 对象

        Args:
            vk_code: Windows 虚拟键码

        Returns:
            对应的 pynput Key 或 KeyCode 对象，无法转换则返回 None
        """
        # 修饰键映射
        modifier_map = {
            VK_LMENU: Key.alt_l,
            VK_RMENU: Key.alt_r,
            VK_LCONTROL: Key.ctrl_l,
            VK_RCONTROL: Key.ctrl_r,
            VK_LSHIFT: Key.shift_l,
            VK_RSHIFT: Key.shift_r,
            VK_LWIN: Key.cmd,
            VK_RWIN: Key.cmd,
        }

        # 特殊键映射
        special_key_map = {
            0x20: Key.space,
            0x1B: Key.esc,
            0x0D: Key.enter,
            0x09: Key.tab,
            0x08: Key.backspace,
            0x2E: Key.delete,
            0x2D: Key.insert,
            0x24: Key.home,
            0x23: Key.end,
            0x21: Key.page_up,
            0x22: Key.page_down,
            0x26: Key.up,
            0x28: Key.down,
            0x25: Key.left,
            0x27: Key.right,
            0x13: Key.pause,
            0x2C: Key.print_screen,
            0x91: Key.scroll_lock,
        }

        # 功能键 F1-F12 (0x70-0x7B)
        function_keys = {
            0x70: Key.f1,
            0x71: Key.f2,
            0x72: Key.f3,
            0x73: Key.f4,
            0x74: Key.f5,
            0x75: Key.f6,
            0x76: Key.f7,
            0x77: Key.f8,
            0x78: Key.f9,
            0x79: Key.f10,
            0x7A: Key.f11,
            0x7B: Key.f12,
        }

        # 检查修饰键
        if vk_code in modifier_map:
            return modifier_map[vk_code]

        # 检查特殊键
        if vk_code in special_key_map:
            return special_key_map[vk_code]

        # 检查功能键
        if vk_code in function_keys:
            return function_keys[vk_code]

        # 字符键 (A-Z: 0x41-0x5A)
        if 0x41 <= vk_code <= 0x5A:
            char = chr(vk_code).lower()
            return KeyCode.from_char(char)

        # 数字键 (0-9: 0x30-0x39)
        if 0x30 <= vk_code <= 0x39:
            char = chr(vk_code)
            return KeyCode.from_char(char)

        return None

    def _restart_listener(self) -> None:
        """重启键盘监听器以应用热键更改"""
        # 调试日志：记录重启（DEBUG级别）
        if app_logger.is_debug_enabled():
            import inspect

            caller_frame = inspect.currentframe().f_back
            caller_info = f"{caller_frame.f_code.co_filename}:{caller_frame.f_lineno}"

            app_logger.log_audio_event(
                "Hotkey listener restarting",
                {
                    "caller": caller_info,
                    "was_listening": self._is_listening_flag,
                    "registered_count": len(self.registered_hotkeys),
                },
            )

        # 停止旧listener
        if self._listener and self._is_listening_flag:
            self._listener.stop()

            # 等待 listener 线程完全退出，避免进程泄漏
            import time

            for _ in range(10):  # 最多等待 1 秒
                if not self._listener.is_alive():
                    break
                time.sleep(0.1)

            self._is_listening_flag = False

        # 清空所有 HotKey 对象的内部状态（防止状态残留）
        for hotkey_info in self.registered_hotkeys.values():
            hotkey_obj = hotkey_info["hotkey_obj"]
            if hotkey_obj._state:
                if app_logger.is_debug_enabled():
                    app_logger.log_audio_event(
                        "Resetting hotkey state on listener restart",
                        {
                            "hotkey": hotkey_info.get("normalized", "unknown"),
                            "stale_state": str(hotkey_obj._state),
                        },
                    )
                hotkey_obj._state.clear()

        # 跟踪当前按下的键 (VK 码 -> 按下时间戳)
        # 修复 Alt+H 误触发：添加时间窗口检查，确保组合键在 500ms 内按下
        current_vk_keys: Dict[int, float] = {}
        # 跟踪被抑制的键（确保press和release成对抑制）
        suppressed_vk_keys: Set[int] = set()

        # win32 事件过滤器 - 在 Windows 消息循环中最早执行
        def win32_event_filter(msg, data):
            """在 Windows 消息级别拦截按键事件

            修复 Alt+H 误触发：添加 500ms 时间窗口检查
            - 只有所有按键在 500ms 内按下才触发快捷键
            - 自动清理超过 2 秒未释放的按键
            """
            try:
                if msg in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    # 按键按下
                    vk_code = data.vkCode
                    current_time = time.time()

                    # 清理超时的按键（超过 2 秒未释放）
                    timeout_keys = [
                        vk
                        for vk, ts in current_vk_keys.items()
                        if current_time - ts > 2.0
                    ]
                    for vk in timeout_keys:
                        del current_vk_keys[vk]
                        if app_logger.is_debug_enabled():
                            app_logger.log_audio_event(
                                f"Timeout key cleaned (VK={hex(vk)})",
                                {
                                    "vk_code": vk,
                                    "age_seconds": current_time
                                    - current_vk_keys.get(vk, current_time),
                                },
                            )

                    # 调试日志：记录按键事件（DEBUG级别）
                    if app_logger.is_debug_enabled() and vk_code in [
                        0x7B,
                        0xA4,
                        0xA5,
                        0x48,
                    ]:  # F12, Left Alt, Right Alt, H
                        app_logger.log_audio_event(
                            f"KeyDown detected (VK={hex(vk_code)})",
                            {
                                "vk_code": vk_code,
                                "current_vk_keys": {
                                    hex(k): current_time - v
                                    for k, v in current_vk_keys.items()
                                },
                                "suppressed_vk_keys": [
                                    hex(k) for k in suppressed_vk_keys
                                ],
                                "registered_hotkeys_count": len(
                                    self.registered_hotkeys
                                ),
                            },
                        )

                    current_vk_keys[vk_code] = current_time

                    # 转换为 pynput Key
                    pynput_key = self._vk_to_pynput_key(vk_code)
                    if pynput_key is None:
                        return True  # 无法转换，允许传播

                    # 检查当前按键组合是否匹配快捷键
                    current_pynput_keys = set()
                    for vk in current_vk_keys:
                        pk = self._vk_to_pynput_key(vk)
                        if pk:
                            current_pynput_keys.add(pk)

                    normalized_current = self._normalize_key_set(current_pynput_keys)

                    # 调试日志：显示所有已注册快捷键的比较（DEBUG级别）
                    if app_logger.is_debug_enabled() and vk_code in [
                        0x7B,
                        0xA4,
                        0xA5,
                        0x48,
                    ]:  # F12, Alt, H
                        app_logger.log_audio_event(
                            f"Checking hotkey match (VK={hex(vk_code)})",
                            {
                                "normalized_current": str(normalized_current),
                                "registered_hotkeys": {
                                    k: str(v["keys"])
                                    for k, v in self.registered_hotkeys.items()
                                },
                            },
                        )

                    # 检查是否匹配任何已注册的快捷键
                    for hotkey_info in self.registered_hotkeys.values():
                        hotkey_keys = hotkey_info["keys"]
                        if normalized_current == hotkey_keys:
                            # 时间窗口检查：所有按键必须在 500ms 内按下
                            timestamps = [
                                current_vk_keys[vk] for vk in current_vk_keys.keys()
                            ]
                            time_span = max(timestamps) - min(timestamps)

                            if time_span > 0.5:  # 超过 500ms
                                # 不触发快捷键
                                if app_logger.is_debug_enabled():
                                    app_logger.log_audio_event(
                                        "Hotkey REJECTED (time window)",
                                        {
                                            "hotkey": hotkey_info.get(
                                                "normalized", "unknown"
                                            ),
                                            "time_span_ms": time_span * 1000,
                                            "threshold_ms": 500,
                                            "vk_codes": [
                                                hex(vk) for vk in current_vk_keys.keys()
                                            ],
                                            "timestamps_age": {
                                                hex(vk): current_time - ts
                                                for vk, ts in current_vk_keys.items()
                                            },
                                        },
                                    )

                                # ⭐ 修复误触发：拒绝快捷键时，清理超时的修饰键（Alt/Ctrl/Shift）
                                # 防止它们与后续打字组合成误触发
                                modifier_vks = {
                                    VK_LMENU,
                                    VK_RMENU,
                                    VK_LCONTROL,
                                    VK_RCONTROL,
                                    VK_LSHIFT,
                                    VK_RSHIFT,
                                }
                                cleaned_modifiers = []
                                for vk in list(current_vk_keys.keys()):
                                    if (
                                        vk in modifier_vks
                                        and (current_time - current_vk_keys[vk]) > 0.5
                                    ):
                                        del current_vk_keys[vk]
                                        cleaned_modifiers.append(hex(vk))

                                if cleaned_modifiers and app_logger.is_debug_enabled():
                                    app_logger.log_audio_event(
                                        "Modifier keys cleaned (time window reject)",
                                        {"cleaned_vk_codes": cleaned_modifiers},
                                    )

                                continue  # 跳过此快捷键，不触发
                            # 匹配！抑制此事件并手动通知 HotKey
                            suppressed_vk_keys.add(vk_code)

                            hotkey_obj = hotkey_info["hotkey_obj"]

                            # 调试日志：热键匹配成功（DEBUG级别）
                            if app_logger.is_debug_enabled():
                                app_logger.log_audio_event(
                                    f"Hotkey MATCHED (VK={hex(vk_code)})",
                                    {
                                        "hotkey": hotkey_info.get(
                                            "normalized", "unknown"
                                        ),
                                        "normalized_current": str(normalized_current),
                                        "hotkey_keys": str(hotkey_keys),
                                        "hotkey_state_before": str(hotkey_obj._state),
                                        "action": hotkey_info.get("action", "unknown"),
                                    },
                                )

                            # 重建完整的按键状态（修复组合键触发问题）
                            # 清空旧状态并重新添加所有当前按下的键
                            if app_logger.is_debug_enabled():
                                app_logger.log_audio_event(
                                    "Rebuilding hotkey state",
                                    {
                                        "old_state": str(hotkey_obj._state),
                                        "current_keys": str(normalized_current),
                                        "vk_code": vk_code,
                                    },
                                )
                            hotkey_obj._state.clear()

                            # 逐个添加当前所有按下的键到 _state
                            for pk in current_pynput_keys:
                                hotkey_obj.press(pk)

                            # 调试日志：press 后的状态（DEBUG级别）
                            if app_logger.is_debug_enabled() and vk_code == 0x7B:  # F12
                                app_logger.log_audio_event(
                                    "F12 after press()",
                                    {"hotkey_state_after": str(hotkey_obj._state)},
                                )

                            # ⭐ 修复误触发：快捷键触发后立即清空所有跟踪状态
                            # 防止修饰键（Alt/Ctrl/Shift）状态残留导致后续打字误触发
                            if app_logger.is_debug_enabled():
                                app_logger.log_audio_event(
                                    "Clearing all key states after hotkey trigger",
                                    {
                                        "hotkey": hotkey_info.get(
                                            "normalized", "unknown"
                                        ),
                                        "cleared_vk_keys": [
                                            hex(vk) for vk in current_vk_keys.keys()
                                        ],
                                        "cleared_suppressed_keys": [
                                            hex(vk) for vk in suppressed_vk_keys
                                        ],
                                    },
                                )

                            current_vk_keys.clear()
                            suppressed_vk_keys.clear()

                            # 同时清空所有 HotKey 对象的状态，确保完全归零
                            for info in self.registered_hotkeys.values():
                                info["hotkey_obj"]._state.clear()

                            return False  # 抑制事件

                    # 不匹配，允许传播到 on_press
                    return True

                elif msg in (WM_KEYUP, WM_SYSKEYUP):
                    # 按键释放
                    vk_code = data.vkCode

                    # 调试日志：F12 释放（DEBUG级别）
                    if app_logger.is_debug_enabled() and vk_code == 0x7B:  # F12
                        app_logger.log_audio_event(
                            "F12 KeyUp detected",
                            {
                                "vk_code": vk_code,
                                "in_suppressed": vk_code in suppressed_vk_keys,
                                "current_vk_keys": list(current_vk_keys.keys()),
                            },
                        )

                    if vk_code in current_vk_keys:
                        del current_vk_keys[vk_code]

                    pynput_key = self._vk_to_pynput_key(vk_code)
                    if pynput_key is None:
                        return True

                    # 如果这个键的 press 被抑制了，release 也要抑制
                    if vk_code in suppressed_vk_keys:
                        suppressed_vk_keys.discard(vk_code)

                        # 手动通知 HotKey 对象
                        for info in self.registered_hotkeys.values():
                            hotkey_obj = info["hotkey_obj"]

                            # 调试日志：release 前的状态（DEBUG级别）
                            if app_logger.is_debug_enabled() and vk_code == 0x7B:  # F12
                                app_logger.log_audio_event(
                                    "F12 before release()",
                                    {"hotkey_state_before": str(hotkey_obj._state)},
                                )

                            hotkey_obj.release(pynput_key)

                            # 调试日志：release 后的状态（DEBUG级别）
                            if app_logger.is_debug_enabled() and vk_code == 0x7B:  # F12
                                app_logger.log_audio_event(
                                    "F12 after release()",
                                    {"hotkey_state_after": str(hotkey_obj._state)},
                                )

                        return False  # 抑制事件

                    # 否则允许传播到 on_release
                    return True

            except Exception as e:
                app_logger.log_error(e, "win32_event_filter")
                return True  # 出错时不抑制

            return True

        # on_press/on_release 只处理未被抑制的事件
        def on_press(key):
            # 通知所有 HotKey 对象（对于未被 win32_event_filter 抑制的键）
            for hotkey_info in self.registered_hotkeys.values():
                hotkey_info["hotkey_obj"].press(key)

        def on_release(key):
            # 通知所有 HotKey 对象（对于未被 win32_event_filter 抑制的键）
            for hotkey_info in self.registered_hotkeys.values():
                hotkey_info["hotkey_obj"].release(key)

        # 创建 listener，使用 win32_event_filter
        self._listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release,
            win32_event_filter=win32_event_filter,
        )

        self._listener.start()
        self._is_listening_flag = True

        app_logger.log_audio_event(
            "Hotkey listener started (win32_event_filter)",
            {"registered_count": len(self.registered_hotkeys)},
        )

    def unregister_hotkey(self, hotkey: str) -> None:
        """注销快捷键"""
        if hotkey not in self.registered_hotkeys:
            return

        try:
            del self.registered_hotkeys[hotkey]

            # 重启listener以移除热键
            if self.registered_hotkeys:
                self._restart_listener()
            else:
                # 没有热键了，停止listener
                if self._listener:
                    self._listener.stop()
                    self._is_listening_flag = False

            app_logger.log_audio_event("Hotkey unregistered", {"hotkey": hotkey})

        except Exception as e:
            app_logger.log_error(e, f"unregister_hotkey_{hotkey}")

    def unregister_all_hotkeys(self) -> None:
        """注销所有快捷键 - pynput版本不会阻塞"""
        hotkeys_to_remove = list(self.registered_hotkeys.keys())

        for hotkey in hotkeys_to_remove:
            # 从字典中删除，不调用unregister_hotkey避免重复restart
            if hotkey in self.registered_hotkeys:
                del self.registered_hotkeys[hotkey]

        # 停止listener - pynput的stop()不会阻塞键盘输入
        if self._listener and self._is_listening_flag:
            self._listener.stop()

            # 等待 listener 线程完全退出，避免进程泄漏
            import time

            for _ in range(10):  # 最多等待 1 秒
                if not self._listener.is_alive():
                    break
                time.sleep(0.1)

            self._listener = None
            self._is_listening_flag = False

        app_logger.log_audio_event(
            "All hotkeys unregistered (pynput)", {"count": len(hotkeys_to_remove)}
        )

    def is_hotkey_registered(self, hotkey: str) -> bool:
        """检查快捷键是否已注册"""
        return hotkey in self.registered_hotkeys

    def get_registered_hotkeys(self) -> Dict[str, str]:
        """获取所有已注册的快捷键"""
        return {
            hotkey: info["normalized"]
            for hotkey, info in self.registered_hotkeys.items()
        }

    def start_listening(self) -> bool:
        """开始监听快捷键"""
        if self._is_listening_flag:
            app_logger.log_audio_event("Hotkey listening already active", {})
            return True

        # 检查是否有已注册的快捷键
        if not self.registered_hotkeys:
            app_logger.log_audio_event(
                "No hotkeys registered, skipping listening start", {}
            )
            return False

        try:
            # 启动listener
            self._restart_listener()

            app_logger.log_audio_event(
                "Hotkey listening started (pynput)",
                {
                    "registered_count": len(self.registered_hotkeys),
                    "hotkeys": list(self.registered_hotkeys.keys()),
                },
            )
            return True

        except Exception as e:
            self._is_listening_flag = False
            app_logger.log_error(e, "start_listening")
            return False

    def stop_listening(self) -> None:
        """停止监听快捷键"""
        if not self._is_listening_flag:
            return

        if self._listener:
            self._listener.stop()
            self._listener = None

        self._is_listening_flag = False
        app_logger.log_audio_event("Hotkey listening stopped", {})

    def _normalize_hotkey(self, hotkey: str) -> str:
        """规范化快捷键字符串"""
        # 移除空格，转小写
        normalized = hotkey.strip().lower()

        # 标准化分隔符
        normalized = normalized.replace(" ", "").replace("_", "+")

        # 标准化键名
        normalized = normalized.replace("control", "ctrl")
        normalized = normalized.replace("command", "cmd")
        normalized = normalized.replace("windows", "win")

        return normalized

    def test_hotkey_availability(self, hotkey: str) -> Dict[str, Any]:
        """测试快捷键可用性"""
        try:
            # 基本检查
            if not hotkey or not hotkey.strip():
                return {"available": False, "message": "Hotkey cannot be empty"}

            # 规范化
            normalized = self._normalize_hotkey(hotkey)
            parts = normalized.split("+")

            # 检查是否为单键（除非是特殊键）
            allowed_single_keys = [
                "f1",
                "f2",
                "f3",
                "f4",
                "f5",
                "f6",
                "f7",
                "f8",
                "f9",
                "f10",
                "f11",
                "f12",
                "esc",
                "space",
                "pause",
                "print_screen",
                "scroll_lock",
            ]
            if len(parts) == 1 and parts[0] not in allowed_single_keys:
                return {
                    "available": False,
                    "message": "Single key hotkeys are not recommended (except function keys)",
                }

            # 检查是否有修饰键
            modifiers = ["ctrl", "alt", "shift", "cmd", "win"]
            has_modifier = any(part in modifiers for part in parts)

            if len(parts) > 1 and not has_modifier:
                return {
                    "available": False,
                    "message": "Multi-key hotkeys must include a modifier (ctrl, alt, shift)",
                }

            # 检查是否与系统热键冲突（基本检查）
            system_hotkeys = [
                "ctrl+alt+del",
                "ctrl+shift+esc",
                "win+l",
                "win+d",
                "alt+tab",
                "alt+f4",
            ]

            if normalized in system_hotkeys:
                return {
                    "available": False,
                    "message": f"Hotkey conflicts with system hotkey: {normalized}",
                }

            return {"available": True, "message": "Hotkey is available"}

        except Exception as e:
            app_logger.log_error(e, f"test_hotkey_availability_{hotkey}")
            return {"available": False, "message": f"Error testing hotkey: {str(e)}"}
