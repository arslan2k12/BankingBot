"""
Comprehensive Test Runner for Banking Bot

This script runs all tests in the banking bot testing suite with various
configurations and generates comprehensive reports.
"""

import os
import sys
import pytest
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class BankingBotTestRunner:
    """Comprehensive test runner for banking bot."""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.results = {}
        
    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests."""
        print("🧪 Running Unit Tests...")
        result = pytest.main([
            str(self.test_dir),
            "-m", "unit",
            "-v",
            "--tb=short",
            "--durations=10"
        ])
        
        self.results['unit'] = {
            'exit_code': result,
            'timestamp': datetime.now().isoformat()
        }
        return self.results['unit']
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""
        print("🔗 Running Integration Tests...")
        result = pytest.main([
            str(self.test_dir),
            "-m", "integration",
            "-v",
            "--tb=short",
            "--durations=10"
        ])
        
        self.results['integration'] = {
            'exit_code': result,
            'timestamp': datetime.now().isoformat()
        }
        return self.results['integration']
    
    def run_validation_tests(self) -> Dict[str, Any]:
        """Run validation tests."""
        print("✅ Running Validation Tests...")
        result = pytest.main([
            str(self.test_dir),
            "-m", "validation",
            "-v",
            "--tb=short",
            "--durations=10"
        ])
        
        self.results['validation'] = {
            'exit_code': result,
            'timestamp': datetime.now().isoformat()
        }
        return self.results['validation']
    
    def run_database_tests(self) -> Dict[str, Any]:
        """Run database tests."""
        print("🗄️  Running Database Tests...")
        result = pytest.main([
            str(self.test_dir),
            "-m", "database",
            "-v",
            "--tb=short",
            "--durations=10"
        ])
        
        self.results['database'] = {
            'exit_code': result,
            'timestamp': datetime.now().isoformat()
        }
        return self.results['database']
    
    def run_agent_tests(self) -> Dict[str, Any]:
        """Run agent tests."""
        print("🤖 Running Agent Tests...")
        result = pytest.main([
            str(self.test_dir),
            "-m", "agent",
            "-v",
            "--tb=short",
            "--durations=10"
        ])
        
        self.results['agent'] = {
            'exit_code': result,
            'timestamp': datetime.now().isoformat()
        }
        return self.results['agent']
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests."""
        print("⚡ Running Performance Tests...")
        result = pytest.main([
            str(self.test_dir),
            "-m", "performance",
            "-v",
            "--tb=short",
            "--durations=10"
        ])
        
        self.results['performance'] = {
            'exit_code': result,
            'timestamp': datetime.now().isoformat()
        }
        return self.results['performance']
    
    def run_all_tests(self, include_slow=False) -> Dict[str, Any]:
        """Run all tests."""
        print("🚀 Running All Banking Bot Tests...")
        
        # Determine which tests to run
        markers = []
        if not include_slow:
            markers.append("not slow")
        
        args = [
            str(self.test_dir),
            "-v",
            "--tb=short",
            "--durations=20",
            "--strict-markers"
        ]
        
        if markers:
            args.extend(["-m", " and ".join(markers)])
        
        result = pytest.main(args)
        
        self.results['all'] = {
            'exit_code': result,
            'timestamp': datetime.now().isoformat(),
            'include_slow': include_slow
        }
        return self.results['all']
    
    def run_quick_tests(self) -> Dict[str, Any]:
        """Run quick tests for continuous integration."""
        print("⚡ Running Quick Tests (CI/CD)...")
        result = pytest.main([
            str(self.test_dir),
            "-m", "not slow and not performance",
            "-v",
            "--tb=line",
            "--durations=5",
            "-x"  # Stop on first failure
        ])
        
        self.results['quick'] = {
            'exit_code': result,
            'timestamp': datetime.now().isoformat()
        }
        return self.results['quick']
    
    def run_specific_test_file(self, test_file: str) -> Dict[str, Any]:
        """Run tests from a specific file."""
        test_path = self.test_dir / test_file
        if not test_path.exists():
            print(f"❌ Test file not found: {test_file}")
            return {'exit_code': 2, 'error': 'File not found'}
        
        print(f"📁 Running tests from {test_file}...")
        result = pytest.main([
            str(test_path),
            "-v",
            "--tb=short"
        ])
        
        self.results[test_file] = {
            'exit_code': result,
            'timestamp': datetime.now().isoformat()
        }
        return self.results[test_file]
    
    def generate_coverage_report(self) -> None:
        """Generate test coverage report."""
        print("📊 Generating Coverage Report...")
        try:
            result = pytest.main([
                str(self.test_dir / ".."),  # Test the src directory
                "--cov=src",
                "--cov-report=html",
                "--cov-report=term",
                "--cov-config=.coveragerc",
                "-m", "not slow"
            ])
            print("✅ Coverage report generated in htmlcov/")
        except Exception as e:
            print(f"⚠️  Coverage report generation failed: {e}")
    
    def print_summary(self) -> None:
        """Print test results summary."""
        print("\n" + "="*60)
        print("🏁 BANKING BOT TEST RESULTS SUMMARY")
        print("="*60)
        
        if not self.results:
            print("❌ No tests have been run")
            return
        
        total_runs = len(self.results)
        successful_runs = sum(1 for r in self.results.values() if r.get('exit_code') == 0)
        
        print(f"📊 Total test runs: {total_runs}")
        print(f"✅ Successful runs: {successful_runs}")
        print(f"❌ Failed runs: {total_runs - successful_runs}")
        print(f"📈 Success rate: {(successful_runs/total_runs)*100:.1f}%")
        
        print("\n📋 Detailed Results:")
        for test_type, result in self.results.items():
            status = "✅ PASS" if result.get('exit_code') == 0 else "❌ FAIL"
            timestamp = result.get('timestamp', 'Unknown')[:19]  # Remove microseconds
            print(f"   {status} {test_type:20} - {timestamp}")
        
        if successful_runs == total_runs:
            print("\n🎉 All tests passed successfully!")
        else:
            print("\n⚠️  Some tests failed. Please review the output above.")


def main():
    """Main test runner entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Banking Bot Test Runner")
    parser.add_argument("--type", choices=[
        "unit", "integration", "validation", "database", "agent", 
        "performance", "all", "quick"
    ], default="all", help="Type of tests to run")
    parser.add_argument("--file", help="Run specific test file")
    parser.add_argument("--slow", action="store_true", help="Include slow tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--summary", action="store_true", help="Show summary only")
    
    args = parser.parse_args()
    
    runner = BankingBotTestRunner()
    
    print(f"🚀 Banking Bot Test Runner - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Test directory: {runner.test_dir}")
    print("-" * 60)
    
    if args.file:
        runner.run_specific_test_file(args.file)
    elif args.type == "unit":
        runner.run_unit_tests()
    elif args.type == "integration":
        runner.run_integration_tests()
    elif args.type == "validation":
        runner.run_validation_tests()
    elif args.type == "database":
        runner.run_database_tests()
    elif args.type == "agent":
        runner.run_agent_tests()
    elif args.type == "performance":
        runner.run_performance_tests()
    elif args.type == "quick":
        runner.run_quick_tests()
    elif args.type == "all":
        runner.run_all_tests(include_slow=args.slow)
    
    if args.coverage:
        runner.generate_coverage_report()
    
    if not args.summary:
        runner.print_summary()


if __name__ == "__main__":
    main()
