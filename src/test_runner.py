"""
Test runner script for executing all tests in the project.
"""
import unittest
import os
import sys

# Add the current directory to the path so that the tests can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_all_tests():
    """Run all test modules under src directory"""
    # Discover and run all tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('src', pattern='*_test.py')
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return non-zero exit code if tests failed
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)