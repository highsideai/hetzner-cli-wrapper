#!/usr/bin/env python3
"""
Test runner script for the Hetzner Cloud deployment tool tests.
Run this from the project root directory.
"""

import subprocess
import sys
import os
import argparse


def run_test_file(test_file, description):
    """Run a specific test file and return success status"""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([
            sys.executable, f"tests/{test_file}"
        ], cwd=os.getcwd(), capture_output=False)
        
        return result.returncode == 0
    except Exception as e:
        print(f"Error running {test_file}: {e}")
        return False


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(
        description='Run test suites for Hetzner Cloud tools',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 run_tests.py                    # Run all tests
  python3 run_tests.py --deploy           # Run only deploy.py tests
  python3 run_tests.py --manage           # Run only manage.py tests
  python3 run_tests.py --deploy --manage  # Run both test suites
        """
    )
    
    parser.add_argument('--deploy', action='store_true', 
                       help='Run deploy.py tests only')
    parser.add_argument('--manage', action='store_true', 
                       help='Run manage.py tests only')
    
    args = parser.parse_args()
    
    # If no specific tests requested, run all
    if not args.deploy and not args.manage:
        args.deploy = True
        args.manage = True
    
    success_count = 0
    total_count = 0
    
    # Run deploy tests
    if args.deploy:
        total_count += 1
        if run_test_file("test_deploy.py", "Deploy Tool Tests (test_deploy.py)"):
            success_count += 1
    
    # Run manage tests  
    if args.manage:
        total_count += 1
        if run_test_file("test_manage.py", "Management Tool Tests (test_manage.py)"):
            success_count += 1
    
    # Print overall summary
    print(f"\n{'='*60}")
    print("OVERALL TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Test suites run: {total_count}")
    print(f"Test suites passed: {success_count}")
    print(f"Test suites failed: {total_count - success_count}")
    
    if success_count == total_count:
        print(f"\n🎉 All test suites passed successfully!")
        return 0
    else:
        print(f"\n❌ {total_count - success_count} test suite(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
