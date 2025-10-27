"""Environment validation and diagnostic utilities for GUI startup"""

import os
import sys
import platform
import importlib
from typing import Dict, Any, Tuple, List
from pathlib import Path
from ..utils.logger import app_logger


class EnvironmentValidator:
    """Comprehensive environment validation for GUI application startup"""
    
    def __init__(self):
        self.validation_results = {}
        self.errors = []
        self.warnings = []
    
    def validate_pyqt6_installation(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate PyQt6 installation and compatibility"""
        validation_results = {
            'pyqt6_available': False,
            'qt_version': None,
            'display_available': False,
            'widgets_available': False,
            'core_available': False,
            'gui_available': False,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Test PyQt6 core availability
            import PyQt6  # noqa: F401
            validation_results['pyqt6_available'] = True
            app_logger.log_audio_event("PyQt6 import successful", {})

            # Test QtCore
            from PyQt6.QtCore import qVersion  # noqa: F401
            validation_results['qt_version'] = qVersion()
            validation_results['core_available'] = True
            app_logger.log_audio_event("PyQt6.QtCore import successful", {"version": qVersion()})

            # Test QtGui
            from PyQt6.QtGui import QGuiApplication  # noqa: F401
            validation_results['gui_available'] = True
            app_logger.log_audio_event("PyQt6.QtGui import successful", {})

            # Test QtWidgets
            from PyQt6.QtWidgets import QApplication
            validation_results['widgets_available'] = True
            app_logger.log_audio_event("PyQt6.QtWidgets import successful", {})
            
            # Test display availability (carefully)
            try:
                # Check if we're in a headless environment
                if os.environ.get('DISPLAY') == '' and platform.system() == 'Linux':
                    validation_results['warnings'].append("No DISPLAY environment variable set (headless environment)")
                
                # Try to create a minimal QApplication to test display
                existing_app = QApplication.instance()
                if existing_app is None:
                    QApplication([])
                    validation_results['display_available'] = True
                    app_logger.log_audio_event("QApplication creation successful", {})
                else:
                    validation_results['display_available'] = True
                    app_logger.log_audio_event("QApplication instance already exists", {})
                    
            except Exception as display_error:
                validation_results['errors'].append(f"Display system error: {display_error}")
                validation_results['display_available'] = False
                app_logger.log_error(display_error, "display_validation")
            
        except ImportError as e:
            validation_results['errors'].append(f"PyQt6 import error: {e}")
            app_logger.log_error(e, "pyqt6_import_validation")
        except Exception as e:
            validation_results['errors'].append(f"PyQt6 validation error: {e}")
            app_logger.log_error(e, "pyqt6_validation")
        
        # Overall success if core components are available
        success = (validation_results['pyqt6_available'] and 
                  validation_results['core_available'] and 
                  validation_results['widgets_available'])
        
        return success, validation_results
    
    def check_display_availability(self) -> bool:
        """Check if display system is available for GUI applications"""
        try:
            system = platform.system()
            
            if system == "Windows":
                # On Windows, check if we have desktop access
                import ctypes
                user32 = ctypes.windll.user32
                return user32.GetDesktopWindow() != 0
                
            elif system == "Linux":
                # Check DISPLAY environment variable
                display = os.environ.get('DISPLAY')
                if not display:
                    return False
                
                # Try to connect to X server
                try:
                    import subprocess
                    result = subprocess.run(['xset', 'q'], capture_output=True, timeout=2)
                    return result.returncode == 0
                except Exception:
                    return False
                    
            elif system == "Darwin":  # macOS
                # On macOS, GUI is usually always available
                return True
                
            else:
                app_logger.log_audio_event("Unknown platform for display check", {"platform": system})
                return False
                
        except Exception as e:
            app_logger.log_error(e, "display_availability_check")
            return False
    
    def test_system_tray_support(self) -> bool:
        """Test if system tray functionality is available"""
        try:
            from PyQt6.QtWidgets import QApplication, QSystemTrayIcon
            
            # Need an application instance
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # Check if system tray is available
            if QSystemTrayIcon.isSystemTrayAvailable():
                app_logger.log_audio_event("System tray support confirmed", {})
                return True
            else:
                app_logger.log_audio_event("System tray not available", {})
                return False
                
        except Exception as e:
            app_logger.log_error(e, "system_tray_support_test")
            return False
    
    def validate_threading_environment(self) -> bool:
        """Validate threading environment compatibility"""
        try:
            # Test basic threading
            import threading
            
            test_result = []
            
            def test_thread():
                test_result.append("success")
            
            thread = threading.Thread(target=test_thread)
            thread.start()
            thread.join(timeout=1.0)
            
            if len(test_result) > 0:
                app_logger.log_audio_event("Threading environment validated", {})
                return True
            else:
                app_logger.log_audio_event("Threading test failed", {})
                return False
                
        except Exception as e:
            app_logger.log_error(e, "threading_environment_validation")
            return False
    
    def diagnose_import_conflicts(self) -> List[str]:
        """Detect potential import conflicts that could affect GUI startup"""
        conflicts = []
        
        try:
            # Check for common conflicting packages
            conflicting_packages = [
                ('PySide6', 'PyQt6'),
                ('tkinter', 'PyQt6'),
                ('wx', 'PyQt6')
            ]
            
            for pkg1, pkg2 in conflicting_packages:
                try:
                    importlib.import_module(pkg1)
                    importlib.import_module(pkg2)
                    conflicts.append(f"Potential conflict: {pkg1} and {pkg2} both available")
                except ImportError:
                    # One or both not available, no conflict
                    pass
            
            # Check for Qt environment variables that might cause issues
            qt_env_vars = ['QT_API', 'QT_PLUGIN_PATH', 'QT_QPA_PLATFORM']
            for var in qt_env_vars:
                if var in os.environ:
                    value = os.environ[var]
                    if 'pyside' in value.lower() or 'qt5' in value.lower():
                        conflicts.append(f"Environment variable {var}={value} might conflict with PyQt6")
            
            app_logger.log_audio_event("Import conflict diagnosis completed", {
                "conflicts_found": len(conflicts)
            })
            
        except Exception as e:
            app_logger.log_error(e, "import_conflict_diagnosis")
            conflicts.append(f"Error during conflict detection: {e}")
        
        return conflicts
    
    def validate_file_permissions(self) -> bool:
        """Validate file system permissions for application operation"""
        try:
            # Check write permissions in user directory
            user_data_dir = Path(os.getenv('APPDATA', '.')) / 'SonicInput'
            user_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Test write access
            test_file = user_data_dir / 'permission_test.tmp'
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                test_file.unlink()
                
                app_logger.log_audio_event("File permissions validated", {
                    "data_dir": str(user_data_dir)
                })
                return True
                
            except Exception as perm_error:
                app_logger.log_error(perm_error, "file_permission_test")
                return False
                
        except Exception as e:
            app_logger.log_error(e, "file_permission_validation")
            return False
    
    def check_dependency_versions(self) -> Dict[str, str]:
        """Check versions of critical dependencies"""
        versions = {}
        
        critical_deps = [
            'PyQt6', 'pynput', 'loguru', 'requests', 'whisper'
        ]
        
        for dep in critical_deps:
            try:
                module = importlib.import_module(dep)
                version = getattr(module, '__version__', 'Unknown')
                versions[dep] = version
            except ImportError:
                versions[dep] = 'Not installed'
            except Exception as e:
                versions[dep] = f'Error: {e}'
        
        # Check Python version
        versions['Python'] = sys.version
        
        app_logger.log_audio_event("Dependency versions checked", versions)
        return versions
    
    def comprehensive_validation(self) -> Tuple[bool, Dict[str, Any]]:
        """Run comprehensive environment validation"""
        app_logger.log_audio_event("Starting comprehensive environment validation", {})
        
        results = {
            'overall_success': False,
            'pyqt6_validation': {},
            'display_available': False,
            'system_tray_support': False,
            'threading_valid': False,
            'file_permissions_ok': False,
            'import_conflicts': [],
            'dependency_versions': {},
            'platform_info': {
                'system': platform.system(),
                'version': platform.version(),
                'machine': platform.machine(),
                'python_version': sys.version
            },
            'errors': [],
            'warnings': []
        }
        
        try:
            # PyQt6 validation
            pyqt6_success, pyqt6_results = self.validate_pyqt6_installation()
            results['pyqt6_validation'] = pyqt6_results
            
            # Display system validation
            results['display_available'] = self.check_display_availability()
            
            # System tray support
            if pyqt6_success:
                results['system_tray_support'] = self.test_system_tray_support()
            
            # Threading environment
            results['threading_valid'] = self.validate_threading_environment()
            
            # File permissions
            results['file_permissions_ok'] = self.validate_file_permissions()
            
            # Import conflicts
            results['import_conflicts'] = self.diagnose_import_conflicts()
            
            # Dependency versions
            results['dependency_versions'] = self.check_dependency_versions()
            
            # Determine overall success
            critical_components = [
                pyqt6_success,
                results['display_available'],
                results['threading_valid'],
                results['file_permissions_ok']
            ]
            
            results['overall_success'] = all(critical_components)
            
            # Collect errors and warnings
            if pyqt6_results.get('errors'):
                results['errors'].extend(pyqt6_results['errors'])
            if pyqt6_results.get('warnings'):
                results['warnings'].extend(pyqt6_results['warnings'])
            
            if results['import_conflicts']:
                results['warnings'].extend(results['import_conflicts'])
            
            app_logger.log_audio_event("Environment validation completed", {
                "overall_success": results['overall_success'],
                "errors_count": len(results['errors']),
                "warnings_count": len(results['warnings'])
            })
            
        except Exception as e:
            app_logger.log_error(e, "comprehensive_validation")
            results['errors'].append(f"Validation process error: {e}")
            results['overall_success'] = False
        
        return results['overall_success'], results


# Create global instance
environment_validator = EnvironmentValidator()