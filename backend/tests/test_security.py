import pytest
from backend.security.code_sandbox import execute_code_safely

def test_block_file_system_access():
    """Malicious code should not access file system"""
    malicious_code = "__import__('os').remove('/etc/passwd')"
    result = execute_code_safely(malicious_code, {})
    assert result["success"] == False
    # Depending on the __builtins__ restriction, it will be a NameError or ImportError
    assert "name '__import__' is not defined" in result["error"] or "import" in result["error"].lower()

def test_block_network_access():
    """Malicious code should not make network requests"""
    malicious_code = "__import__('urllib').request.urlopen('http://evil.com')"
    result = execute_code_safely(malicious_code, {})
    assert result["success"] == False

def test_timeout_enforcement():
    """Infinite loops should timeout"""
    infinite_loop = "while True: pass"
    result = execute_code_safely(infinite_loop, {}, timeout=1)
    assert result["success"] == False
    assert "timed out" in result["error"].lower()

def test_memory_limit():
    """MemoryError should be caught by the sandbox"""
    # Simulate a memory error by raising it directly via exec
    memory_bomb = "raise MemoryError('Simulated memory limit exceeded')"
    result = execute_code_safely(memory_bomb, {})
    assert result["success"] == False
    assert "memory" in result["error"].lower()

