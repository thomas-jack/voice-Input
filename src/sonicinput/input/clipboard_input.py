"""剪贴板输入方法"""

import pyperclip
import time
import win32api
import win32con
from typing import Optional
from ..utils import TextInputError, app_logger


class ClipboardInput:
    """基于剪贴板的文本输入"""
    
    def __init__(self):
        self.original_clipboard = ""
        self.restore_delay = 0.1  # 恢复剪贴板内容的延迟
        
        app_logger.log_audio_event("Clipboard input initialized", {})
    
    def backup_clipboard(self) -> str:
        """备份当前剪贴板内容"""
        try:
            content = pyperclip.paste()
            self.original_clipboard = content
            
            app_logger.log_audio_event("Clipboard backed up", {
                "content_length": len(content),
                "has_content": bool(content)
            })
            
            return content
            
        except Exception as e:
            app_logger.log_error(e, "backup_clipboard")
            self.original_clipboard = ""
            return ""
    
    def restore_clipboard(self, content: str) -> None:
        """恢复剪贴板内容"""
        try:
            pyperclip.copy(content)
            
            app_logger.log_audio_event("Clipboard restored", {
                "content_length": len(content)
            })
            
        except Exception as e:
            app_logger.log_error(e, "restore_clipboard")
    
    def send_ctrl_v(self) -> None:
        """发送Ctrl+V组合键"""
        try:
            # 按下Ctrl键
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            time.sleep(0.01)
            
            # 按下V键
            win32api.keybd_event(ord('V'), 0, 0, 0)
            time.sleep(0.01)
            
            # 释放V键
            win32api.keybd_event(ord('V'), 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.01)
            
            # 释放Ctrl键
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            
            app_logger.log_audio_event("Ctrl+V sent", {})
            
        except Exception as e:
            raise TextInputError(f"Failed to send Ctrl+V: {e}")
    
    def input_via_clipboard(self, text: str, restore_delay: Optional[float] = None) -> bool:
        """通过剪贴板输入文本"""
        if not text:
            return True
        
        restore_delay = restore_delay or self.restore_delay
        
        try:
            # 备份原始剪贴板内容
            original_content = self.backup_clipboard()
            
            # 将文本复制到剪贴板
            pyperclip.copy(text)
            time.sleep(0.05)  # 短暂延迟确保复制完成
            
            # 发送Ctrl+V
            self.send_ctrl_v()
            
            # 延迟后恢复原始剪贴板内容
            if restore_delay > 0:
                time.sleep(restore_delay)
                self.restore_clipboard(original_content)
            
            app_logger.log_audio_event("Text input via clipboard successful", {
                "text_length": len(text),
                "restore_delay": restore_delay
            })
            
            return True
            
        except Exception as e:
            app_logger.log_error(e, "input_via_clipboard")
            
            # 尝试恢复剪贴板
            try:
                self.restore_clipboard(original_content)
            except (OSError, RuntimeError):
                pass  # 剪贴板访问失败或已被其他程序占用
            
            return False
    
    def test_clipboard_access(self) -> bool:
        """测试剪贴板访问权限"""
        try:
            # 测试读取
            original = pyperclip.paste()
            
            # 测试写入
            test_text = "voice_input_test_" + str(time.time())
            pyperclip.copy(test_text)
            
            # 验证写入
            result = pyperclip.paste()
            success = result == test_text
            
            # 恢复原始内容
            pyperclip.copy(original)
            
            app_logger.log_audio_event("Clipboard access test", {
                "success": success
            })
            
            return success
            
        except Exception as e:
            app_logger.log_error(e, "test_clipboard_access")
            return False
    
    def set_restore_delay(self, delay: float) -> None:
        """设置剪贴板恢复延迟"""
        self.restore_delay = max(0.0, delay)
        
        app_logger.log_audio_event("Clipboard restore delay set", {
            "delay": self.restore_delay
        })
    
    def clear_clipboard(self) -> None:
        """清空剪贴板"""
        try:
            pyperclip.copy("")
            app_logger.log_audio_event("Clipboard cleared", {})
        except Exception as e:
            app_logger.log_error(e, "clear_clipboard")
    
    def get_clipboard_content(self) -> str:
        """获取当前剪贴板内容"""
        try:
            return pyperclip.paste()
        except Exception as e:
            app_logger.log_error(e, "get_clipboard_content")
            return ""