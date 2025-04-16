#!/usr/bin/env python3
"""
Test Runner for Payymo

This script runs all tests for the Payymo system, or specific test modules
if specified.

Usage:
  python run_tests.py                   # Run all tests
  python run_tests.py -m test_module    # Run specific test module
"""

import os
import sys
import unittest
import argparse

def run_tests(test_module=None):
    """Run tests from the flask_backend/tests directory"""
    # Set up test discovery path
    test_dir = os.path.join(os.path.dirname(__file__), 'flask_backend', 'tests')
    
    # Create test suite
    if test_module:
        # Run specific test module
        test_suite = unittest.defaultTestLoader.discover(
            test_dir,
            pattern=f"{test_module}.py"
        )
    else:
        # Run all tests
        test_suite = unittest.defaultTestLoader.discover(test_dir)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Payymo tests")
    parser.add_argument("-m", "--module", 
                        help="Run specific test module (without .py extension)")
    
    args = parser.parse_args()
    sys.exit(run_tests(args.module))