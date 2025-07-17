#!/usr/bin/env python3
"""
Test handler locally without Docker
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Mock runpod module
class MockRunPod:
    class serverless:
        @staticmethod
        def start(config):
            print("Handler registered")
            # Test the handler
            test_job = {
                "id": "test-001",
                "input": {
                    "audio": "https://github.com/ggerganov/whisper.cpp/raw/master/samples/jfk.wav",
                    "generate_insights": False
                }
            }
            handler = config["handler"]
            result = handler(test_job)
            print(f"Result: {result}")

sys.modules['runpod'] = MockRunPod()

# Now import and test
import handler

print("Handler module loaded successfully")