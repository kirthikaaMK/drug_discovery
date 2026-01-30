#!/usr/bin/env python3
"""
Robust startup script for the Drug Discovery AI System
Handles all edge cases and ensures the system works in any environment
"""

import os
import sys
import time
import socket
import subprocess
import signal
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import config

class SystemHealthChecker:
    """Check system health and requirements"""

    def __init__(self):
        self.issues = []
        self.warnings = []

    def check_python_version(self):
        """Check Python version compatibility"""
        version = sys.version_info
        if version < (3, 8):
            self.issues.append(f"Python {version.major}.{version.minor} is too old. Requires Python 3.8+")
        elif version < (3, 10):
            self.warnings.append(f"Python {version.major}.{version.minor} detected. Consider upgrading to 3.10+ for better performance")

    def check_dependencies(self):
        """Check if required packages are installed"""
        required_packages = [
            'flask', 'pandas', 'numpy', 'matplotlib', 'plotly',
            'requests', 'sklearn', 'torch', 'transformers', 'sentence_transformers'
        ]

        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            self.issues.append(f"Missing required packages: {', '.join(missing_packages)}")
            self.issues.append("Run: pip install -r requirements.txt")

    def check_disk_space(self):
        """Check available disk space"""
        try:
            stat = os.statvfs(project_root)
            free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
            if free_gb < 1.0:
                self.issues.append(".1f")
            elif free_gb < 5.0:
                self.warnings.append(".1f")
        except:
            pass  # Skip on systems where this doesn't work

    def check_memory(self):
        """Check available memory"""
        try:
            import psutil
            memory_gb = psutil.virtual_memory().available / (1024**3)
            if memory_gb < 2.0:
                self.issues.append(".1f")
            elif memory_gb < 4.0:
                self.warnings.append(".1f")
        except ImportError:
            self.warnings.append("Could not check memory (psutil not installed)")
        except:
            pass

    def check_network(self):
        """Check network connectivity"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
        except:
            self.warnings.append("No internet connection detected - some features may not work")

    def check_port_availability(self, port):
        """Check if port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return True
        except:
            return False

    def run_all_checks(self):
        """Run all health checks"""
        print("🔍 Running system health checks...")

        self.check_python_version()
        self.check_dependencies()
        self.check_disk_space()
        self.check_memory()
        self.check_network()

        if self.issues:
            print("❌ Critical Issues Found:")
            for issue in self.issues:
                print(f"   - {issue}")
            return False

        if self.warnings:
            print("⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   - {warning}")

        print("✅ System health check passed!")
        return True

class RobustAppLauncher:
    """Launch the Flask app with maximum reliability"""

    def __init__(self):
        self.app_process = None
        self.port = config.get('app', 'port', 5000)
        self.host = config.get('app', 'host', '0.0.0.0')

    def find_available_port(self, start_port=5000, max_attempts=10):
        """Find an available port"""
        for port in range(start_port, start_port + max_attempts):
            if self.check_port_available(port):
                return port
        return None

    def check_port_available(self, port):
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((self.host, port))
                return True
        except:
            return False

    def kill_existing_processes(self):
        """Kill any existing Flask processes"""
        try:
            # Kill processes on our port
            result = subprocess.run(['lsof', '-ti', f':{self.port}'],
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        time.sleep(1)
                    except:
                        pass
        except:
            pass

        # Also try to kill by process name
        try:
            subprocess.run(['pkill', '-f', 'python.*app.py'],
                         capture_output=True)
            time.sleep(2)
        except:
            pass

    def start_app(self):
        """Start the Flask application"""
        # Ensure config directories exist
        config.ensure_directories()

        # Set environment variables
        env = os.environ.copy()
        env.update({
            'FLASK_APP': 'app.py',
            'FLASK_ENV': 'development' if config.get('app', 'debug') else 'production',
            'PYTHONPATH': str(project_root)
        })

        # Try to start the app
        try:
            print(f"🚀 Starting Drug Discovery AI System on {self.host}:{self.port}")
            self.app_process = subprocess.Popen(
                [sys.executable, 'app.py'],
                cwd=str(project_root),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait for app to start
            time.sleep(3)

            # Check if process is still running
            if self.app_process.poll() is None:
                print("✅ Application started successfully!")
                print(f"🌐 Access at: http://localhost:{self.port}")
                print(f"🌐 Or: http://127.0.0.1:{self.port}")
                return True
            else:
                stdout, stderr = self.app_process.communicate()
                print("❌ Application failed to start")
                if stderr:
                    print("Error output:", stderr.decode())
                if stdout:
                    print("Standard output:", stdout.decode())
                return False

        except Exception as e:
            print(f"❌ Failed to start application: {e}")
            return False

    def wait_for_app_ready(self, timeout=30):
        """Wait for the app to be ready"""
        import requests

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f'http://localhost:{self.port}', timeout=2)
                if response.status_code == 200:
                    return True
            except:
                pass
            time.sleep(1)

        return False

    def launch_browser(self):
        """Launch browser if possible"""
        try:
            import webbrowser
            url = f'http://localhost:{self.port}'
            print(f"🌐 Opening browser to {url}")
            webbrowser.open(url)
        except:
            print("💡 Please open your browser and navigate to:")
            print(f"   http://localhost:{self.port}")

def main():
    """Main startup function"""
    print("🧬 Drug Discovery AI System - Robust Startup")
    print("=" * 50)

    # Run health checks
    checker = SystemHealthChecker()
    if not checker.run_all_checks():
        print("\n❌ System health check failed. Please resolve the issues above.")
        sys.exit(1)

    print()

    # Initialize launcher
    launcher = RobustAppLauncher()

    # Find available port
    if not launcher.check_port_available(launcher.port):
        print(f"⚠️  Port {launcher.port} is in use, finding alternative...")
        new_port = launcher.find_available_port(launcher.port + 1)
        if new_port:
            launcher.port = new_port
            config.set('app', 'port', new_port)
            print(f"✅ Using port {new_port}")
        else:
            print("❌ Could not find available port")
            sys.exit(1)

    # Kill existing processes
    print("🧹 Cleaning up existing processes...")
    launcher.kill_existing_processes()

    # Start the application
    if launcher.start_app():
        # Wait for app to be ready
        if launcher.wait_for_app_ready():
            print("\n🎉 System is ready!")
            launcher.launch_browser()

            # Keep the script running
            print("\n📊 System Status:")
            print("   - Press Ctrl+C to stop the application")
            print("   - Check logs in the terminal above")

            try:
                # Wait for the app process
                launcher.app_process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Shutting down...")
                launcher.app_process.terminate()
                launcher.app_process.wait()
                print("✅ Application stopped")
        else:
            print("❌ Application started but is not responding")
            sys.exit(1)
    else:
        print("❌ Failed to start application")
        sys.exit(1)

if __name__ == "__main__":
    main()