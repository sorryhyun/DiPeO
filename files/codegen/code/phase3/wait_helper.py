"""Simple wait helper for master diagram"""
import time

def wait_for_completion(inputs):
    """Small delay to ensure file writes are complete"""
    time.sleep(1)
    return inputs