"""Unit tests for payload classification utilities."""

import pytest

from dipeo.domain.diagram.cc_translate.payload_utils import (
    classify_payload,
    extract_error_message,
    extract_original_content,
    extract_patch_data,
    extract_write_content,
    is_error_payload,
    is_full_write,
    is_partial_diff,
    is_rich_diff,
    should_create_diff_node,
    should_create_write_node,
    validate_rich_diff_payload,
)


class TestErrorPayloadDetection:
    """Tests for error payload detection."""

    def test_string_error_payload(self):
        """Test detection of string error messages."""
        assert is_error_payload("Error: File not found") is True
        assert is_error_payload("Error: String not found in file") is True
        assert is_error_payload("The string was not found") is True
        assert is_error_payload("Success!") is False
        assert is_error_payload("") is False

    def test_dict_error_payload(self):
        """Test detection of dict error payloads."""
        assert is_error_payload({"error": "Something went wrong"}) is True
        assert is_error_payload({"status": "error", "message": "Failed"}) is True
        assert is_error_payload({"content": "Error: Operation failed"}) is True
        assert is_error_payload({"status": "success"}) is False
        assert is_error_payload({"content": "Success!"}) is False

    def test_extract_error_message(self):
        """Test error message extraction."""
        assert extract_error_message("Error: File not found") == "Error: File not found"
        assert extract_error_message({"error": "Something went wrong"}) == "Something went wrong"
        assert extract_error_message({"content": "Error: Failed"}) == "Error: Failed"
        assert extract_error_message("Success!") is None
        assert extract_error_message({"status": "success"}) is None


class TestRichDiffDetection:
    """Tests for rich diff payload detection."""

    def test_rich_diff_with_structured_patch(self):
        """Test detection of rich diffs with structured patches."""
        payload = {
            "originalFile": "def hello():\n    print('world')\n",
            "structuredPatch": "@@ -1,2 +1,2 @@\n def hello():\n-    print('world')\n+    print('hello world')\n",
        }
        assert is_rich_diff(payload) is True
        assert should_create_diff_node(payload) is True

    def test_rich_diff_with_patch_field(self):
        """Test detection of rich diffs with patch field."""
        payload = {
            "originalFileContents": "original content",
            "patch": "--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-original\n+modified\n",
        }
        assert is_rich_diff(payload) is True

    def test_rich_diff_with_diff_field(self):
        """Test detection of rich diffs with diff field."""
        payload = {"originalFile": "content", "diff": "some diff data"}
        assert is_rich_diff(payload) is True

    def test_not_rich_diff_missing_original(self):
        """Test payloads without original content are not rich diffs."""
        payload = {
            "structuredPatch": "@@ -1 +1 @@\n-old\n+new\n",
            "oldString": "old",
            "newString": "new",
        }
        assert is_rich_diff(payload) is False

    def test_not_rich_diff_missing_patch(self):
        """Test payloads without patch data are not rich diffs."""
        payload = {"originalFile": "content", "oldString": "old", "newString": "new"}
        assert is_rich_diff(payload) is False

    def test_not_rich_diff_error_payload(self):
        """Test error payloads are not rich diffs."""
        payload = {
            "originalFile": "content",
            "structuredPatch": "patch",
            "error": "Something failed",
        }
        assert is_rich_diff(payload) is False


class TestPartialDiffDetection:
    """Tests for partial diff payload detection."""

    def test_partial_diff_with_strings(self):
        """Test detection of partial diffs with old/new strings."""
        payload = {"oldString": "old text", "newString": "new text"}
        assert is_partial_diff(payload) is True
        assert is_rich_diff(payload) is False

    def test_partial_diff_with_original(self):
        """Test partial diff with original content but no patch."""
        payload = {"originalFile": "full content", "oldString": "old", "newString": "new"}
        # This IS a partial diff - has strings but no patch data
        assert is_partial_diff(payload) is True
        assert is_rich_diff(payload) is False  # Not rich without patch

    def test_not_partial_diff_missing_strings(self):
        """Test payloads without old/new strings are not partial diffs."""
        payload = {"content": "something"}
        assert is_partial_diff(payload) is False

        payload = {"oldString": "old"}  # Missing newString
        assert is_partial_diff(payload) is False


class TestFullWriteDetection:
    """Tests for full write payload detection."""

    def test_full_write_with_content(self):
        """Test detection of full write with content field."""
        payload = {"content": "new file contents"}
        assert is_full_write(payload) is True
        assert should_create_write_node(payload) is True

    def test_full_write_with_new_file(self):
        """Test detection of full write with newFile field."""
        payload = {"newFile": "new file contents"}
        assert is_full_write(payload) is True

    def test_full_write_with_file_contents(self):
        """Test detection of full write with fileContents field."""
        payload = {"fileContents": "new file contents"}
        assert is_full_write(payload) is True

    def test_not_full_write_has_original(self):
        """Test payloads with original content are not full writes."""
        payload = {"content": "new content", "originalFile": "old content"}
        assert is_full_write(payload) is False

    def test_not_full_write_error(self):
        """Test error payloads are not full writes."""
        payload = {
            "content": "Error: Failed to write",
        }
        assert is_full_write(payload) is False


class TestPayloadClassification:
    """Tests for overall payload classification."""

    def test_classify_error(self):
        """Test classification of error payloads."""
        assert classify_payload("Error: Failed") == "error"
        assert classify_payload({"error": "Failed"}) == "error"

    def test_classify_rich_diff(self):
        """Test classification of rich diff payloads."""
        payload = {"originalFile": "content", "structuredPatch": "patch"}
        assert classify_payload(payload) == "rich_diff"

    def test_classify_partial_diff(self):
        """Test classification of partial diff payloads."""
        payload = {"oldString": "old", "newString": "new"}
        assert classify_payload(payload) == "partial_diff"

    def test_classify_full_write(self):
        """Test classification of full write payloads."""
        payload = {"content": "new content"}
        assert classify_payload(payload) == "full_write"

    def test_classify_unknown(self):
        """Test classification of unknown payloads."""
        assert classify_payload(None) == "unknown"
        assert classify_payload([]) == "unknown"
        assert classify_payload({}) == "unknown"
        assert classify_payload("random string") == "unknown"


class TestDataExtraction:
    """Tests for data extraction from payloads."""

    def test_extract_patch_data(self):
        """Test patch data extraction."""
        # String patch
        assert extract_patch_data({"structuredPatch": "patch data"}) == "patch data"
        assert extract_patch_data({"patch": "patch data"}) == "patch data"
        assert extract_patch_data({"diff": "diff data"}) == "diff data"

        # List patch
        assert extract_patch_data({"structuredPatch": ["line1", "line2"]}) == "line1\nline2"

        # Priority order
        payload = {"structuredPatch": "structured", "patch": "regular", "diff": "diff"}
        assert extract_patch_data(payload) == "structured"

        # No patch
        assert extract_patch_data({}) is None

    def test_extract_original_content(self):
        """Test original content extraction."""
        assert extract_original_content({"originalFile": "content"}) == "content"
        assert extract_original_content({"originalFileContents": "content"}) == "content"

        # Priority
        payload = {"originalFile": "file1", "originalFileContents": "file2"}
        assert extract_original_content(payload) == "file1"

        # No original
        assert extract_original_content({}) is None

    def test_extract_write_content(self):
        """Test write content extraction."""
        assert extract_write_content({"content": "data"}) == "data"
        assert extract_write_content({"newFile": "data"}) == "data"
        assert extract_write_content({"fileContents": "data"}) == "data"

        # Priority
        payload = {"content": "content1", "newFile": "content2", "fileContents": "content3"}
        assert extract_write_content(payload) == "content1"

        # No content
        assert extract_write_content({}) is None


class TestRichDiffValidation:
    """Tests for rich diff payload validation."""

    def test_valid_rich_diff(self):
        """Test validation of valid rich diff."""
        payload = {"originalFile": "content", "structuredPatch": "patch"}
        is_valid, error = validate_rich_diff_payload(payload)
        assert is_valid is True
        assert error is None

    def test_invalid_not_rich_diff(self):
        """Test validation fails for non-rich diff."""
        payload = {"content": "something"}
        is_valid, error = validate_rich_diff_payload(payload)
        assert is_valid is False
        assert error == "Payload is not a rich diff"

    def test_invalid_missing_original(self):
        """Test validation fails without original content."""
        payload = {"structuredPatch": "patch"}
        is_valid, error = validate_rich_diff_payload(payload)
        assert is_valid is False
        assert "not a rich diff" in error

    def test_invalid_missing_patch(self):
        """Test validation fails without patch data."""
        payload = {"originalFile": "content"}
        is_valid, error = validate_rich_diff_payload(payload)
        assert is_valid is False
        assert "not a rich diff" in error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
