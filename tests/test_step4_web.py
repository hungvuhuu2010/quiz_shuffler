"""
Unit tests for Step 4 Web Application module structure.
"""
import pytest
from pathlib import Path


def test_web_app_file_exists():
    web_app_path = Path("src/web_app.py")
    assert web_app_path.exists() is True, "src/web_app.py script should be created."


def test_requirements_web_file_exists():
    req_path = Path("requirements_web.txt")
    assert req_path.exists() is True, "requirements_web.txt should be created."
