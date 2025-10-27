"""Startup diagnostic utilities for comprehensive application health checking"""

import os
import sys
import platform
import importlib
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from sonicinput.utils.logger import app_logger
from .environment_validator import environment_validator


class StartupDiagnostics:
    """Comprehensive startup diagnostic system"""
    
    def __init__(self):
        self.diagnostic_start_time = datetime.now()
        self.test_results = {}
        self.import_results = {}
        self.system_info = {}
    
    def generate_environment_report(self) -> Dict[str, Any]:
        """Generate comprehensive environment diagnostic report"""
        app_logger.log_audio_event("Generating environment report", {})
        
        report = {
            'timestamp': self.diagnostic_start_time.isoformat(),
            'system_info': self._collect_system_info(),
            'python_info': self._collect_python_info(),
            'environment_validation': {},
            'import_tests': {},
            'dependency_check': {},
            'file_system_check': {},
            'process_info': self._collect_process_info(),
            'summary': {
                'overall_status': 'unknown',
                'critical_issues': [],
                'warnings': [],
                'recommendations': []
            }
        }
        
        try:
            # Run environment validation
            env_success, env_results = environment_validator.comprehensive_validation()
            report['environment_validation'] = env_results
            
            # Run import tests
            report['import_tests'] = self.test_all_imports()
            
            # Check dependencies
            report['dependency_check'] = self.check_dependency_versions()
            
            # File system checks
            report['file_system_check'] = self._check_file_system()
            
            # Generate summary
            report['summary'] = self._generate_summary(report)
            
            app_logger.log_audio_event("Environment report generated", {
                "overall_status": report['summary']['overall_status'],
                "critical_issues": len(report['summary']['critical_issues']),
                "warnings": len(report['summary']['warnings'])
            })
            
        except Exception as e:
            app_logger.log_error(e, "environment_report_generation")
            report['summary']['critical_issues'].append(f"Report generation error: {e}")
            report['summary']['overall_status'] = 'error'
        
        return report
    
    def test_all_imports(self) -> Dict[str, bool]:
        """Test all critical imports for the application"""
        app_logger.log_audio_event("Testing all critical imports", {})
        
        import_tests = {}
        
        # Core PyQt6 imports
        qt_imports = [
            'PyQt6',
            'PyQt6.QtCore',
            'PyQt6.QtGui', 
            'PyQt6.QtWidgets'
        ]
        
        # Application imports
        app_imports = [
            'sonicinput.core.voice_input_app',
            'sonicinput.core.di_container',
            'sonicinput.core.hotkey_manager',
            'sonicinput.ui.main_window',
            'sonicinput.ui.recording_overlay',
            'sonicinput.audio.recorder',
            'sonicinput.speech.gpu_manager'
        ]
        
        # External dependencies
        external_imports = [
            'pynput',
            'loguru',
            'requests',
            'numpy',
            'scipy'
        ]
        
        all_imports = qt_imports + app_imports + external_imports
        
        for module_name in all_imports:
            try:
                importlib.import_module(module_name)
                import_tests[module_name] = True
                app_logger.log_audio_event(f"Import successful: {module_name}", {})
            except ImportError as e:
                import_tests[module_name] = False
                app_logger.log_error(e, f"import_test_{module_name}")
            except Exception as e:
                import_tests[module_name] = False
                app_logger.log_error(e, f"import_test_error_{module_name}")
        
        success_count = sum(import_tests.values())
        total_count = len(import_tests)
        
        app_logger.log_audio_event("Import testing completed", {
            "success_count": success_count,
            "total_count": total_count,
            "success_rate": success_count / total_count if total_count > 0 else 0
        })
        
        return import_tests
    
    def check_dependency_versions(self) -> Dict[str, str]:
        """Check versions of all dependencies with detailed info"""
        app_logger.log_audio_event("Checking dependency versions", {})
        
        versions = {}
        
        # Critical dependencies with expected version info
        dependencies = [
            'PyQt6', 'pynput', 'loguru', 'requests',
            'numpy', 'scipy', 'faster_whisper'
        ]
        
        for dep in dependencies:
            try:
                module = importlib.import_module(dep)
                
                # Try different ways to get version
                version = None
                for attr in ['__version__', 'VERSION', 'version']:
                    if hasattr(module, attr):
                        version = getattr(module, attr)
                        break
                
                if version is None:
                    # Try package metadata
                    try:
                        import pkg_resources
                        version = pkg_resources.get_distribution(dep).version
                    except Exception:
                        version = 'Version unknown'
                
                versions[dep] = str(version)
                
            except ImportError:
                versions[dep] = 'Not installed'
            except Exception as e:
                versions[dep] = f'Error: {e}'
        
        # System info
        versions['Python'] = sys.version.split()[0]
        versions['Platform'] = platform.platform()
        versions['Architecture'] = platform.architecture()[0]
        
        app_logger.log_audio_event("Dependency version check completed", {
            "dependencies_checked": len(dependencies),
            "python_version": versions['Python']
        })
        
        return versions
    
    def validate_file_permissions(self) -> bool:
        """Validate file system permissions and access"""
        try:
            # Application data directory
            app_data_dir = Path(os.getenv('APPDATA', '.')) / 'SonicInput'
            app_data_dir.mkdir(parents=True, exist_ok=True)
            
            # Test write access
            test_file = app_data_dir / 'permission_test.tmp'
            with open(test_file, 'w') as f:
                f.write('permission test')

            # Test read access
            with open(test_file, 'r'):
                pass

            # Cleanup
            test_file.unlink()
            
            app_logger.log_audio_event("File permissions validated", {
                "app_data_dir": str(app_data_dir)
            })
            return True
            
        except Exception as e:
            app_logger.log_error(e, "file_permission_validation")
            return False
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect comprehensive system information"""
        system_info = {
            'platform': platform.platform(),
            'system': platform.system(),
            'version': platform.version(),
            'release': platform.release(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'architecture': platform.architecture(),
            'python_version': sys.version,
            'python_executable': sys.executable,
            'environment_variables': {}
        }
        
        # Important environment variables
        env_vars_of_interest = [
            'PATH', 'PYTHONPATH', 'QT_API', 'QT_PLUGIN_PATH', 
            'DISPLAY', 'HOME', 'APPDATA', 'USERPROFILE'
        ]
        
        for var in env_vars_of_interest:
            system_info['environment_variables'][var] = os.environ.get(var, 'Not set')
        
        return system_info
    
    def _collect_python_info(self) -> Dict[str, Any]:
        """Collect Python-specific information"""
        python_info = {
            'version': sys.version,
            'version_info': sys.version_info,
            'executable': sys.executable,
            'prefix': sys.prefix,
            'path': sys.path[:5],  # First 5 entries to avoid too much data
            'modules': list(sys.modules.keys())[:20]  # First 20 loaded modules
        }
        
        return python_info
    
    def _collect_process_info(self) -> Dict[str, Any]:
        """Collect current process information"""
        process_info = {
            'pid': os.getpid(),
            'cwd': os.getcwd(),
            'command_line': ' '.join(sys.argv)
        }
        
        try:
            import psutil
            process = psutil.Process()
            process_info.update({
                'memory_info': process.memory_info()._asdict(),
                'cpu_percent': process.cpu_percent(),
                'num_threads': process.num_threads()
            })
        except ImportError:
            process_info['psutil'] = 'Not available'
        except Exception as e:
            process_info['psutil_error'] = str(e)
        
        return process_info
    
    def _check_file_system(self) -> Dict[str, Any]:
        """Check file system related issues"""
        fs_check = {
            'current_directory_writable': False,
            'app_data_directory_writable': False,
            'temp_directory_writable': False,
            'disk_space_available': 'unknown'
        }
        
        try:
            # Current directory write test
            test_file = Path.cwd() / 'temp_write_test.tmp'
            with open(test_file, 'w') as f:
                f.write('test')
            test_file.unlink()
            fs_check['current_directory_writable'] = True
        except Exception:
            fs_check['current_directory_writable'] = False

        try:
            # App data directory write test
            app_data_dir = Path(os.getenv('APPDATA', '.')) / 'SonicInput'
            app_data_dir.mkdir(parents=True, exist_ok=True)
            test_file = app_data_dir / 'temp_write_test.tmp'
            with open(test_file, 'w') as f:
                f.write('test')
            test_file.unlink()
            fs_check['app_data_directory_writable'] = True
        except Exception:
            fs_check['app_data_directory_writable'] = False

        try:
            # Temp directory write test
            import tempfile
            with tempfile.NamedTemporaryFile(delete=True) as f:
                f.write(b'test')
            fs_check['temp_directory_writable'] = True
        except Exception:
            fs_check['temp_directory_writable'] = False

        try:
            # Disk space check
            import shutil
            total, used, free = shutil.disk_usage(Path.cwd())
            fs_check['disk_space_available'] = {
                'total_gb': total // (1024**3),
                'used_gb': used // (1024**3),
                'free_gb': free // (1024**3)
            }
        except Exception:
            fs_check['disk_space_available'] = 'Cannot determine'
        
        return fs_check
    
    def _generate_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary with status and recommendations"""
        summary = {
            'overall_status': 'healthy',
            'critical_issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Check environment validation
        env_validation = report.get('environment_validation', {})
        if not env_validation.get('overall_success', False):
            summary['overall_status'] = 'critical'
            summary['critical_issues'].append('Environment validation failed')
            
            if env_validation.get('errors'):
                summary['critical_issues'].extend(env_validation['errors'])
                
            if env_validation.get('warnings'):
                summary['warnings'].extend(env_validation['warnings'])
        
        # Check import tests
        import_tests = report.get('import_tests', {})
        failed_imports = [name for name, success in import_tests.items() if not success]
        
        critical_imports = ['PyQt6', 'PyQt6.QtWidgets', 'sonicinput.core.voice_input_app']
        critical_failures = [imp for imp in failed_imports if imp in critical_imports]
        
        if critical_failures:
            summary['overall_status'] = 'critical'
            summary['critical_issues'].append(f'Critical imports failed: {critical_failures}')
        
        optional_failures = [imp for imp in failed_imports if imp not in critical_imports]
        if optional_failures:
            summary['warnings'].append(f'Optional imports failed: {optional_failures}')
        
        # Check file system
        fs_check = report.get('file_system_check', {})
        if not fs_check.get('app_data_directory_writable', False):
            summary['critical_issues'].append('Cannot write to application data directory')
            summary['overall_status'] = 'critical'
        
        # Generate recommendations
        if summary['critical_issues']:
            summary['recommendations'].append('Fix critical issues before running the application')
            
        if 'PyQt6' in failed_imports:
            summary['recommendations'].append('Install PyQt6: pip install PyQt6')
            
        if env_validation.get('import_conflicts'):
            summary['recommendations'].append('Resolve package conflicts - consider using virtual environment')
        
        # Final status determination
        if len(summary['critical_issues']) > 0:
            summary['overall_status'] = 'critical'
        elif len(summary['warnings']) > 2:
            summary['overall_status'] = 'warning'
        else:
            summary['overall_status'] = 'healthy'
        
        return summary
    
    def print_diagnostic_summary(self, report: Dict[str, Any]) -> None:
        """Print a human-readable diagnostic summary"""
        print("\n" + "="*60)
        print("VOICE INPUT SOFTWARE - STARTUP DIAGNOSTICS")
        print("="*60)
        
        summary = report['summary']
        status = summary['overall_status']
        
        status_symbols = {
            'healthy': '[PASS]',
            'warning': '[WARN] ',
            'critical': '[FAIL]',
            'error': '[ERROR]'
        }
        
        print(f"\nOverall Status: {status_symbols.get(status, '?')} {status.upper()}")
        
        if summary['critical_issues']:
            print(f"\n[FAIL] CRITICAL ISSUES ({len(summary['critical_issues'])}):")
            for issue in summary['critical_issues']:
                print(f"  • {issue}")
        
        if summary['warnings']:
            print(f"\n[WARN]  WARNINGS ({len(summary['warnings'])}):")
            for warning in summary['warnings']:
                print(f"  • {warning}")
        
        if summary['recommendations']:
            print("\n[INFO] RECOMMENDATIONS:")
            for rec in summary['recommendations']:
                print(f"  • {rec}")
        
        # Import status summary
        import_tests = report.get('import_tests', {})
        if import_tests:
            success_count = sum(import_tests.values())
            total_count = len(import_tests)
            print(f"\n[INFO] IMPORTS: {success_count}/{total_count} successful")
            
            failed = [name for name, success in import_tests.items() if not success]
            if failed:
                print(f"   Failed: {', '.join(failed[:3])}{'...' if len(failed) > 3 else ''}")
        
        # Environment summary
        env_validation = report.get('environment_validation', {})
        if env_validation:
            print("\n[INFO]  ENVIRONMENT:")
            print(f"   PyQt6: {'[PASS]' if env_validation.get('pyqt6_validation', {}).get('pyqt6_available') else '[FAIL]'}")
            print(f"   Display: {'[PASS]' if env_validation.get('display_available') else '[FAIL]'}")
            print(f"   System Tray: {'[PASS]' if env_validation.get('system_tray_support') else '[FAIL]'}")
        
        print("\n" + "="*60 + "\n")


# Create global instance
startup_diagnostics = StartupDiagnostics()