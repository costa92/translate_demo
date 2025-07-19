#!/bin/bash
# Final Testing Script for Unified Knowledge Base System
# This script runs the comprehensive testing script and displays the results

echo "=== Starting Final Testing ==="
echo "Running comprehensive test suite..."

# Run the Python testing script
python run_final_testing.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo "=== Final Testing Completed Successfully ==="
    echo "All tests passed and requirements met!"
    echo "See comprehensive_test_report.md for details."
    exit 0
else
    echo "=== Final Testing Completed with Issues ==="
    echo "Some tests failed or requirements not met."
    echo "See comprehensive_test_report.md for details."
    exit 1
fi