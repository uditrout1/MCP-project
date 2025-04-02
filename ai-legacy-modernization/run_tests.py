"""
Test runner script for AI Legacy Modernization PoC.
This script runs all tests and generates a report.
"""

import os
import sys
import logging
import json
import time
import subprocess
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_unit_tests():
    """Run unit tests."""
    logger.info("Running unit tests...")
    
    result = subprocess.run(
        ["python", "tests/unit_test.py"],
        capture_output=True,
        text=True
    )
    
    success = result.returncode == 0
    
    if success:
        logger.info("Unit tests passed")
    else:
        logger.error("Unit tests failed")
        logger.error(result.stderr)
    
    return success, result.stdout, result.stderr

def run_integration_tests():
    """Run integration tests."""
    logger.info("Running integration tests...")
    
    result = subprocess.run(
        ["python", "tests/integration_test.py"],
        capture_output=True,
        text=True
    )
    
    success = result.returncode == 0
    
    if success:
        logger.info("Integration tests passed")
    else:
        logger.error("Integration tests failed")
        logger.error(result.stderr)
    
    return success, result.stdout, result.stderr

def run_e2e_tests():
    """Run end-to-end tests."""
    logger.info("Running end-to-end tests...")
    
    result = subprocess.run(
        ["python", "tests/e2e_test.py"],
        capture_output=True,
        text=True
    )
    
    success = result.returncode == 0
    
    if success:
        logger.info("End-to-end tests passed")
    else:
        logger.error("End-to-end tests failed")
        logger.error(result.stderr)
    
    return success, result.stdout, result.stderr

def generate_report(unit_results, integration_results, e2e_results):
    """Generate a test report."""
    logger.info("Generating test report...")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "unit_tests": {
            "success": unit_results[0],
            "stdout": unit_results[1],
            "stderr": unit_results[2]
        },
        "integration_tests": {
            "success": integration_results[0],
            "stdout": integration_results[1],
            "stderr": integration_results[2]
        },
        "e2e_tests": {
            "success": e2e_results[0],
            "stdout": e2e_results[1],
            "stderr": e2e_results[2]
        },
        "overall_success": unit_results[0] and integration_results[0] and e2e_results[0]
    }
    
    # Save report to file
    with open("test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Generate HTML report
    html_report = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Legacy Modernization PoC - Test Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            .summary {{ margin: 20px 0; padding: 10px; border-radius: 5px; }}
            .success {{ background-color: #dff0d8; border: 1px solid #d6e9c6; }}
            .failure {{ background-color: #f2dede; border: 1px solid #ebccd1; }}
            .test-section {{ margin: 20px 0; }}
            .test-header {{ padding: 10px; background-color: #f5f5f5; border: 1px solid #ddd; }}
            .test-content {{ padding: 10px; border: 1px solid #ddd; border-top: none; white-space: pre-wrap; }}
        </style>
    </head>
    <body>
        <h1>AI Legacy Modernization PoC - Test Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary {'success' if report['overall_success'] else 'failure'}">
            <h2>Summary: {'All tests passed' if report['overall_success'] else 'Some tests failed'}</h2>
        </div>
        
        <div class="test-section">
            <div class="test-header">
                <h3>Unit Tests: {'Passed' if report['unit_tests']['success'] else 'Failed'}</h3>
            </div>
            <div class="test-content">
                {report['unit_tests']['stdout']}
                {report['unit_tests']['stderr']}
            </div>
        </div>
        
        <div class="test-section">
            <div class="test-header">
                <h3>Integration Tests: {'Passed' if report['integration_tests']['success'] else 'Failed'}</h3>
            </div>
            <div class="test-content">
                {report['integration_tests']['stdout']}
                {report['integration_tests']['stderr']}
            </div>
        </div>
        
        <div class="test-section">
            <div class="test-header">
                <h3>End-to-End Tests: {'Passed' if report['e2e_tests']['success'] else 'Failed'}</h3>
            </div>
            <div class="test-content">
                {report['e2e_tests']['stdout']}
                {report['e2e_tests']['stderr']}
            </div>
        </div>
    </body>
    </html>
    """
    
    with open("test_report.html", "w") as f:
        f.write(html_report)
    
    logger.info(f"Test report generated: test_report.html")
    
    return report["overall_success"]

def run_all_tests():
    """Run all tests and generate a report."""
    logger.info("Running all tests...")
    
    # Run tests
    unit_results = run_unit_tests()
    integration_results = run_integration_tests()
    e2e_results = run_e2e_tests()
    
    # Generate report
    overall_success = generate_report(unit_results, integration_results, e2e_results)
    
    if overall_success:
        logger.info("All tests passed")
        return 0
    else:
        logger.error("Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
