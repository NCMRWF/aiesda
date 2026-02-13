import sys
import argparse
import subprocess
import aiesda

def get_status():
    """Prints the current AIESDA environment and JEDI bridge status."""
    print(f"🌍 AIESDA [v{aiesda.__version__}]")
    print(f"📂 Root: {aiesda.__path__[0]}")
    
    # Try to verify JEDI via the bridge
    try:
        # We call 'jedi-run' which was added to PATH by the modulefile
        result = subprocess.run(
            ["jedi-run", "python3", "-c", "import ufo; print(ufo.__file__)"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print("✅ JEDI Bridge: Online")
            print(f"🔗 JEDI Source: {result.stdout.strip()}")
        else:
            print("⚠️ JEDI Bridge: Offline or jedi-run not configured.")
    except FileNotFoundError:
        print("ℹ️ JEDI Bridge: Not detected in PATH (HPC Native mode?)")

def run():
    """Main execution logic for 'aiesda-run'."""
    parser = argparse.ArgumentParser(description="AIESDA CLI - Earth System Data Assimilation")
    parser.add_argument("-v", "--version", action="store_true", help="Show version info")
    parser.add_argument("--status", action="store_true", help="Check JEDI bridge connectivity")
    parser.add_argument("command", nargs="?", help="Command to run inside the DA environment")

    args = parser.parse_args()

    if args.version:
        print(f"aiesda version {aiesda.__version__}")
        sys.exit(0)

    if args.status:
        get_status()
        sys.exit(0)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Future logic for executing specific DA tasks goes here
    print(f"🚀 Executing AIESDA task: {args.command}...")

if __name__ == "__main__":
    run()
