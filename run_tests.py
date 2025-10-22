#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test runner for Health Monitor
個別のテストを実行して問題を特定するためのスクリプト
"""

import unittest
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_single_test(test_module):
    """単一のテストモジュールを実行"""
    print(f"\n{'='*50}")
    print(f"Running {test_module}")
    print('='*50)
    
    try:
        # テストモジュールをインポート
        module = __import__(f'tests.{test_module}', fromlist=[test_module])
        
        # テストスイートを作成
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        
        # テストを実行
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except Exception as e:
        print(f"Error running {test_module}: {e}")
        return False

def run_all_tests():
    """全てのテストを実行"""
    test_modules = [
        'test_website_checker',
        'test_database_checker',
        'test_health_check_engine',
        'test_log_manager',
        'test_retry_handler',
        'test_self_monitor',
        'test_status_display',
        'test_main_integration'
    ]
    
    results = {}
    
    for module in test_modules:
        print(f"\n🧪 Testing {module}...")
        success = run_single_test(module)
        results[module] = success
        
        if success:
            print(f"✅ {module} - PASSED")
        else:
            print(f"❌ {module} - FAILED")
    
    # 結果サマリー
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for module, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{module:<30} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed.")
        return False

def run_quick_test():
    """基本的なテストのみを実行"""
    print("Running quick tests...")
    
    # 基本的なテストのみ
    basic_tests = [
        'test_website_checker',
        'test_log_manager'
    ]
    
    for module in basic_tests:
        print(f"\n🧪 Quick test: {module}")
        success = run_single_test(module)
        if not success:
            print(f"❌ Quick test failed: {module}")
            return False
    
    print("✅ Quick tests passed!")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "quick":
            run_quick_test()
        elif sys.argv[1] == "single" and len(sys.argv) > 2:
            test_name = sys.argv[2]
            run_single_test(test_name)
        else:
            print("Usage:")
            print("  python run_tests.py           # Run all tests")
            print("  python run_tests.py quick     # Run quick tests")
            print("  python run_tests.py single <test_name>  # Run single test")
    else:
        run_all_tests()