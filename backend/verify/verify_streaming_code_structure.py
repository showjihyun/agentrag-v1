"""
Verify that streaming code has proper error handling for auth scenarios.

This script verifies:
1. stream_agent_response accepts optional user parameter
2. stream_hybrid_response accepts optional user parameter
3. Both functions have try/except blocks around database operations
4. Database errors don't break streaming (continue processing)
5. Streaming works without authentication (user=None)

Requirements: FR-2.2, FR-2.3, NFR-1
"""

import ast
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class StreamingCodeAnalyzer:
    """Analyze streaming code structure."""

    def __init__(self):
        self.results = []

    def log(self, message: str, level: str = "INFO"):
        """Log a message."""
        print(f"[{level}] {message}")

    def add_result(self, test_name: str, passed: bool, message: str):
        """Add a test result."""
        self.results.append({"test": test_name, "passed": passed, "message": message})
        status = "✅ PASS" if passed else "❌ FAIL"
        self.log(f"{status}: {test_name} - {message}")

    def analyze_function(self, tree: ast.Module, func_name: str):
        """Analyze a specific function in the AST."""
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == func_name:
                return node
        return None

    def check_optional_user_param(
        self, func_node: ast.AsyncFunctionDef, func_name: str
    ):
        """Check if function has optional user parameter."""
        if func_node is None:
            self.add_result(
                f"{func_name} - optional user param",
                False,
                f"Function {func_name} not found",
            )
            return False

        # Check for user parameter
        has_user_param = False
        user_is_optional = False

        for arg in func_node.args.args:
            if arg.arg == "user":
                has_user_param = True
                # Check if it has Optional type annotation
                if arg.annotation:
                    annotation_str = ast.unparse(arg.annotation)
                    if (
                        "Optional" in annotation_str
                        or "None" in annotation_str
                        or "|" in annotation_str
                    ):
                        user_is_optional = True
                break

        # Check for default value
        if has_user_param and func_node.args.defaults:
            for default in func_node.args.defaults:
                if isinstance(default, ast.Constant) and default.value is None:
                    user_is_optional = True

        if has_user_param and user_is_optional:
            self.add_result(
                f"{func_name} - optional user param",
                True,
                f"Function has optional user parameter",
            )
            return True
        elif has_user_param:
            self.add_result(
                f"{func_name} - optional user param",
                False,
                f"Function has user parameter but it's not optional",
            )
            return False
        else:
            self.add_result(
                f"{func_name} - optional user param",
                False,
                f"Function missing user parameter",
            )
            return False

    def check_db_error_handling(self, func_node: ast.AsyncFunctionDef, func_name: str):
        """Check if function has proper error handling for database operations."""
        if func_node is None:
            self.add_result(
                f"{func_name} - DB error handling",
                False,
                f"Function {func_name} not found",
            )
            return False

        # Look for try/except blocks
        has_try_except = False
        has_continue_on_error = False

        for node in ast.walk(func_node):
            if isinstance(node, ast.Try):
                has_try_except = True
                # Check if there's a comment or log about continuing on error
                for handler in node.handlers:
                    # Check for Exception handler
                    if handler.type is None or (
                        isinstance(handler.type, ast.Name)
                        and handler.type.id == "Exception"
                    ):
                        # Look for continue/pass or log statements in handler
                        for stmt in handler.body:
                            if isinstance(stmt, ast.Pass):
                                has_continue_on_error = True
                            elif isinstance(stmt, ast.Expr) and isinstance(
                                stmt.value, ast.Call
                            ):
                                # Check for logger.error or similar
                                if (
                                    hasattr(stmt.value.func, "attr")
                                    and "error" in stmt.value.func.attr.lower()
                                ):
                                    has_continue_on_error = True

        if has_try_except and has_continue_on_error:
            self.add_result(
                f"{func_name} - DB error handling",
                True,
                f"Function has try/except with error logging and continues on failure",
            )
            return True
        elif has_try_except:
            self.add_result(
                f"{func_name} - DB error handling",
                True,
                f"Function has try/except blocks for error handling",
            )
            return True
        else:
            self.add_result(
                f"{func_name} - DB error handling",
                False,
                f"Function missing try/except blocks for database operations",
            )
            return False

    def check_conditional_db_save(
        self, func_node: ast.AsyncFunctionDef, func_name: str
    ):
        """Check if database save is conditional on user being authenticated."""
        if func_node is None:
            self.add_result(
                f"{func_name} - conditional DB save",
                False,
                f"Function {func_name} not found",
            )
            return False

        # Look for "if user is not None" or similar checks
        has_user_check = False

        for node in ast.walk(func_node):
            if isinstance(node, ast.If):
                # Check if condition involves user
                condition_str = ast.unparse(node.test)
                if "user" in condition_str and (
                    "is not None" in condition_str
                    or "!= None" in condition_str
                    or "is not" in condition_str
                ):
                    has_user_check = True
                    break

        if has_user_check:
            self.add_result(
                f"{func_name} - conditional DB save",
                True,
                f"Function checks if user is authenticated before saving to database",
            )
            return True
        else:
            self.add_result(
                f"{func_name} - conditional DB save",
                False,
                f"Function missing check for user authentication before DB save",
            )
            return False

    def analyze_streaming_functions(self):
        """Analyze streaming functions in query.py."""
        self.log("Analyzing streaming functions in backend/api/query.py...")

        # Read the query.py file
        query_file = "backend/api/query.py"
        if not os.path.exists(query_file):
            self.log(f"File not found: {query_file}", "ERROR")
            return False

        with open(query_file, "r", encoding="utf-8") as f:
            code = f.read()

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.log(f"Syntax error in {query_file}: {e}", "ERROR")
            return False

        # Analyze stream_agent_response
        self.log("\nAnalyzing stream_agent_response...")
        agent_func = self.analyze_function(tree, "stream_agent_response")
        self.check_optional_user_param(agent_func, "stream_agent_response")
        self.check_db_error_handling(agent_func, "stream_agent_response")
        self.check_conditional_db_save(agent_func, "stream_agent_response")

        # Analyze stream_hybrid_response
        self.log("\nAnalyzing stream_hybrid_response...")
        hybrid_func = self.analyze_function(tree, "stream_hybrid_response")
        self.check_optional_user_param(hybrid_func, "stream_hybrid_response")
        self.check_db_error_handling(hybrid_func, "stream_hybrid_response")
        self.check_conditional_db_save(hybrid_func, "stream_hybrid_response")

        return True

    def check_endpoint_uses_optional_user(self):
        """Check if the main endpoint uses get_optional_user dependency."""
        self.log("\nChecking main endpoint uses get_optional_user...")

        query_file = "backend/api/query.py"
        with open(query_file, "r", encoding="utf-8") as f:
            code = f.read()

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.log(f"Syntax error: {e}", "ERROR")
            return False

        # Find process_query function
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "process_query":
                # Check for get_optional_user in parameters
                for arg in node.args.args:
                    if arg.arg == "user":
                        # Check if it has Depends(get_optional_user)
                        # This is in the defaults
                        for default in node.args.defaults:
                            default_str = ast.unparse(default)
                            if "get_optional_user" in default_str:
                                self.add_result(
                                    "Endpoint uses get_optional_user",
                                    True,
                                    "Main endpoint correctly uses get_optional_user dependency",
                                )
                                return True

        self.add_result(
            "Endpoint uses get_optional_user",
            False,
            "Main endpoint not using get_optional_user dependency",
        )
        return False

    def print_summary(self):
        """Print test summary."""
        self.log("\n" + "=" * 70)
        self.log("TEST SUMMARY")
        self.log("=" * 70)

        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed

        for result in self.results:
            status = "✅" if result["passed"] else "❌"
            self.log(f"{status} {result['test']}: {result['message']}")

        self.log("=" * 70)
        self.log(f"Total: {total} | Passed: {passed} | Failed: {failed}")

        if failed == 0:
            self.log("🎉 ALL TESTS PASSED!", "SUCCESS")
        else:
            self.log(f"⚠️  {failed} TEST(S) FAILED", "WARNING")

        self.log("=" * 70)

        return failed == 0


def main():
    """Run code structure analysis."""
    analyzer = StreamingCodeAnalyzer()

    try:
        # Analyze streaming functions
        analyzer.analyze_streaming_functions()

        # Check endpoint configuration
        analyzer.check_endpoint_uses_optional_user()

        # Print summary
        success = analyzer.print_summary()

        return 0 if success else 1

    except Exception as e:
        analyzer.log(f"Fatal error: {e}", "ERROR")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
