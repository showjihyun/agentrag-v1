"""
Tests for Input Validator
"""

import pytest
from pydantic import ValidationError

from backend.core.security.input_validator import (
    InputValidator,
    SecureWorkflowInput,
    SecureQueryInput,
    SecureFileUpload
)


class TestSQLInjectionDetection:
    """Test SQL injection detection"""
    
    def test_detect_select_statement(self):
        """Test detection of SELECT statement"""
        assert InputValidator.check_sql_injection("SELECT * FROM users")
        assert InputValidator.check_sql_injection("select * from users")
    
    def test_detect_union_attack(self):
        """Test detection of UNION attack"""
        assert InputValidator.check_sql_injection("' UNION SELECT password FROM users--")
    
    def test_detect_comment_injection(self):
        """Test detection of comment injection"""
        assert InputValidator.check_sql_injection("admin'--")
        assert InputValidator.check_sql_injection("/* comment */")
    
    def test_detect_or_equals(self):
        """Test detection of OR equals pattern"""
        assert InputValidator.check_sql_injection("' OR '1'='1")
        assert InputValidator.check_sql_injection("' OR 1=1--")
    
    def test_safe_input(self):
        """Test that safe input is not flagged"""
        assert not InputValidator.check_sql_injection("normal text")
        assert not InputValidator.check_sql_injection("user@example.com")


class TestXSSDetection:
    """Test XSS detection"""
    
    def test_detect_script_tag(self):
        """Test detection of script tags"""
        assert InputValidator.check_xss("<script>alert('xss')</script>")
        assert InputValidator.check_xss("<SCRIPT>alert('xss')</SCRIPT>")
    
    def test_detect_javascript_protocol(self):
        """Test detection of javascript: protocol"""
        assert InputValidator.check_xss("javascript:alert('xss')")
    
    def test_detect_event_handlers(self):
        """Test detection of event handlers"""
        assert InputValidator.check_xss("<img onerror='alert(1)'>")
        assert InputValidator.check_xss("<body onload='alert(1)'>")
    
    def test_detect_iframe(self):
        """Test detection of iframe tags"""
        assert InputValidator.check_xss("<iframe src='evil.com'>")
    
    def test_safe_html(self):
        """Test that safe HTML is not flagged"""
        assert not InputValidator.check_xss("<p>Normal paragraph</p>")
        assert not InputValidator.check_xss("<b>Bold text</b>")


class TestCommandInjection:
    """Test command injection detection"""
    
    def test_detect_semicolon(self):
        """Test detection of command separator"""
        assert InputValidator.check_command_injection("ls; rm -rf /")
    
    def test_detect_pipe(self):
        """Test detection of pipe operator"""
        assert InputValidator.check_command_injection("cat file | grep secret")
    
    def test_detect_backticks(self):
        """Test detection of command substitution"""
        assert InputValidator.check_command_injection("`whoami`")
    
    def test_detect_dollar_paren(self):
        """Test detection of $() substitution"""
        assert InputValidator.check_command_injection("$(whoami)")
    
    def test_safe_input(self):
        """Test that safe input is not flagged"""
        assert not InputValidator.check_command_injection("normal text")


class TestCodeSafety:
    """Test Python code safety validation"""
    
    def test_detect_os_import(self):
        """Test detection of os import"""
        code = "import os\nos.system('ls')"
        is_safe, error = InputValidator.validate_code_safety(code)
        
        assert not is_safe
        assert "os" in error
    
    def test_detect_subprocess(self):
        """Test detection of subprocess"""
        code = "import subprocess\nsubprocess.call(['ls'])"
        is_safe, error = InputValidator.validate_code_safety(code)
        
        assert not is_safe
        assert "subprocess" in error
    
    def test_detect_file_operations(self):
        """Test detection of file operations"""
        code = "with open('/etc/passwd') as f:\n    data = f.read()"
        is_safe, error = InputValidator.validate_code_safety(code)
        
        assert not is_safe
        assert "File operations" in error
    
    def test_detect_network_operations(self):
        """Test detection of network operations"""
        code = "import requests\nrequests.get('http://evil.com')"
        is_safe, error = InputValidator.validate_code_safety(code)
        
        assert not is_safe
        assert "Network operations" in error
    
    def test_safe_code(self):
        """Test that safe code is allowed"""
        code = """
def add(a, b):
    return a + b

result = add(1, 2)
print(result)
"""
        is_safe, error = InputValidator.validate_code_safety(code)
        
        assert is_safe
        assert error is None


class TestStringSanitization:
    """Test string sanitization"""
    
    def test_remove_html_tags(self):
        """Test HTML tag removal"""
        result = InputValidator.sanitize_string("<b>Bold</b> text")
        assert "<b>" not in result
        assert "Bold text" in result
    
    def test_truncate_long_string(self):
        """Test string truncation"""
        long_string = "a" * 2000
        result = InputValidator.sanitize_string(long_string, max_length=100)
        
        assert len(result) == 100
    
    def test_remove_null_bytes(self):
        """Test null byte removal"""
        result = InputValidator.sanitize_string("text\x00with\x00nulls")
        assert "\x00" not in result
    
    def test_strip_whitespace(self):
        """Test whitespace stripping"""
        result = InputValidator.sanitize_string("  text  ")
        assert result == "text"


class TestSecureWorkflowInput:
    """Test secure workflow input validation"""
    
    def test_valid_workflow(self):
        """Test valid workflow input"""
        workflow = SecureWorkflowInput(
            name="My Workflow",
            description="Process data",
            nodes=[
                {"type": "start", "data": {}},
                {"type": "llm", "data": {"model": "gpt-4"}},
                {"type": "end", "data": {}}
            ],
            edges=[
                {"source": "start", "target": "llm"},
                {"source": "llm", "target": "end"}
            ]
        )
        
        assert workflow.name == "My Workflow"
        assert len(workflow.nodes) == 3
    
    def test_reject_short_name(self):
        """Test rejection of short name"""
        with pytest.raises(ValidationError):
            SecureWorkflowInput(
                name="ab",  # Too short
                nodes=[{"type": "start", "data": {}}],
                edges=[]
            )
    
    def test_reject_sql_injection_in_name(self):
        """Test rejection of SQL injection in name"""
        with pytest.raises(ValidationError):
            SecureWorkflowInput(
                name="'; DROP TABLE users--",
                nodes=[{"type": "start", "data": {}}],
                edges=[]
            )
    
    def test_reject_xss_in_description(self):
        """Test rejection of XSS in description"""
        with pytest.raises(ValidationError):
            SecureWorkflowInput(
                name="Valid Name",
                description="<script>alert('xss')</script>",
                nodes=[{"type": "start", "data": {}}],
                edges=[]
            )
    
    def test_reject_too_many_nodes(self):
        """Test rejection of too many nodes"""
        with pytest.raises(ValidationError):
            SecureWorkflowInput(
                name="Valid Name",
                nodes=[{"type": "start", "data": {}} for _ in range(101)],
                edges=[]
            )
    
    def test_reject_invalid_node_type(self):
        """Test rejection of invalid node type"""
        with pytest.raises(ValidationError):
            SecureWorkflowInput(
                name="Valid Name",
                nodes=[{"type": "invalid_type", "data": {}}],
                edges=[]
            )
    
    def test_reject_unsafe_code_node(self):
        """Test rejection of unsafe code in code node"""
        with pytest.raises(ValidationError):
            SecureWorkflowInput(
                name="Valid Name",
                nodes=[{
                    "type": "code",
                    "data": {"code": "import os; os.system('ls')"}
                }],
                edges=[]
            )


class TestSecureQueryInput:
    """Test secure query input validation"""
    
    def test_valid_query(self):
        """Test valid query input"""
        query = SecureQueryInput(
            query="What is the capital of France?",
            filters={"category": "geography"}
        )
        
        assert query.query == "What is the capital of France?"
        assert query.filters["category"] == "geography"
    
    def test_reject_sql_injection(self):
        """Test rejection of SQL injection in query"""
        with pytest.raises(ValidationError):
            SecureQueryInput(
                query="'; DROP TABLE documents--"
            )
    
    def test_reject_too_many_filters(self):
        """Test rejection of too many filters"""
        with pytest.raises(ValidationError):
            SecureQueryInput(
                query="Valid query",
                filters={f"filter_{i}": "value" for i in range(21)}
            )
    
    def test_sanitize_query(self):
        """Test query sanitization"""
        query = SecureQueryInput(
            query="  <b>Query</b> with HTML  "
        )
        
        assert "<b>" not in query.query
        assert "Query with HTML" in query.query


class TestSecureFileUpload:
    """Test secure file upload validation"""
    
    def test_valid_pdf_upload(self):
        """Test valid PDF upload"""
        upload = SecureFileUpload(
            filename="document.pdf",
            content_type="application/pdf",
            size=1024000
        )
        
        assert upload.filename == "document.pdf"
    
    def test_reject_invalid_extension(self):
        """Test rejection of invalid file extension"""
        with pytest.raises(ValidationError):
            SecureFileUpload(
                filename="malware.exe",
                content_type="application/x-msdownload",
                size=1024
            )
    
    def test_reject_path_traversal(self):
        """Test rejection of path traversal"""
        with pytest.raises(ValidationError):
            SecureFileUpload(
                filename="../../../etc/passwd",
                content_type="text/plain",
                size=1024
            )
    
    def test_reject_invalid_mime_type(self):
        """Test rejection of invalid MIME type"""
        with pytest.raises(ValidationError):
            SecureFileUpload(
                filename="document.pdf",
                content_type="application/x-executable",
                size=1024
            )
    
    def test_reject_too_large_file(self):
        """Test rejection of too large file"""
        with pytest.raises(ValidationError):
            SecureFileUpload(
                filename="huge.pdf",
                content_type="application/pdf",
                size=100 * 1024 * 1024  # 100MB
            )
    
    def test_reject_zero_size_file(self):
        """Test rejection of zero-size file"""
        with pytest.raises(ValidationError):
            SecureFileUpload(
                filename="empty.pdf",
                content_type="application/pdf",
                size=0
            )
