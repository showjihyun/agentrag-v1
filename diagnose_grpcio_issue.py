"""
Diagnose grpcio installation issues
"""
import sys
import platform
import subprocess

def check_python_version():
    """Check Python version and platform"""
    print("=" * 60)
    print("Python Environment")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Platform: {platform.platform()}")
    print(f"Machine: {platform.machine()}")
    print(f"Architecture: {platform.architecture()}")
    print()

def check_pip_config():
    """Check pip configuration"""
    print("=" * 60)
    print("Pip Configuration")
    print("=" * 60)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "config", "list"],
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        else:
            print("No custom pip configuration found")
    except Exception as e:
        print(f"Error checking pip config: {e}")
    print()

def check_grpcio_versions():
    """Check available grpcio versions"""
    print("=" * 60)
    print("Available grpcio Versions")
    print("=" * 60)
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "index", "versions", "grpcio"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.stdout:
            lines = result.stdout.split('\n')[:10]  # First 10 lines
            for line in lines:
                print(line)
        print()
    except subprocess.TimeoutExpired:
        print("Timeout checking versions (network issue?)")
    except Exception as e:
        print(f"Error checking versions: {e}")
    print()

def check_installed_packages():
    """Check if grpcio or docling are already installed"""
    print("=" * 60)
    print("Currently Installed Packages")
    print("=" * 60)
    
    packages = ['grpcio', 'grpcio-tools', 'docling', 'pdfplumber']
    
    for package in packages:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", package],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines[:3]:  # Name, Version, Summary
                    if line.strip():
                        print(line)
                print()
            else:
                print(f"{package}: Not installed")
        except Exception as e:
            print(f"Error checking {package}: {e}")
    print()

def check_compiler():
    """Check if Visual Studio compiler is available"""
    print("=" * 60)
    print("C++ Compiler Check")
    print("=" * 60)
    
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ["where", "cl.exe"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"✓ Visual Studio compiler found:")
                print(result.stdout.strip())
            else:
                print("✗ Visual Studio compiler NOT found")
                print("  (This is OK if using pre-built wheels)")
        except Exception as e:
            print(f"Error checking compiler: {e}")
    else:
        print("Not Windows - compiler check skipped")
    print()

def recommend_solution():
    """Recommend solution based on findings"""
    print("=" * 60)
    print("Recommended Solution")
    print("=" * 60)
    
    py_version = sys.version_info
    
    if py_version >= (3, 12):
        print("⚠️  Python 3.12 detected - grpcio compilation issues expected")
        print()
        print("RECOMMENDED SOLUTIONS:")
        print()
        print("1. Use pdfplumber (FASTEST - 1 minute):")
        print("   install-with-pdfplumber.bat")
        print()
        print("2. Force grpcio wheel installation (2 minutes):")
        print("   fix-grpcio-python312.bat")
        print()
        print("3. Manual wheel installation:")
        print("   python -m pip install grpcio==1.62.2 --only-binary=:all:")
        print("   python -m pip install docling==2.14.0")
    else:
        print("✓ Python version should work with grpcio")
        print()
        print("Try:")
        print("   python -m pip install grpcio --only-binary=:all:")
        print("   python -m pip install docling")
    print()

def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "grpcio Issue Diagnosis" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    check_python_version()
    check_pip_config()
    check_installed_packages()
    check_compiler()
    recommend_solution()
    
    print("=" * 60)
    print("Diagnosis Complete")
    print("=" * 60)
    print()
    print("For detailed solutions, see: GRPCIO_PYTHON312_SOLUTION.md")
    print()

if __name__ == "__main__":
    main()
