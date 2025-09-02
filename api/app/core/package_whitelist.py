"""
Package whitelist for secure dependency management.
Following Linus's principle: "Trust, but verify"
"""

from typing import Set, Dict, Optional
import re
import logging

logger = logging.getLogger(__name__)

# Whitelisted packages - only these can be installed
# Each entry maps package name to allowed version patterns
ALLOWED_PACKAGES: Dict[str, Optional[str]] = {
    # Core ML packages
    "torch": None,  # Any version
    "tensorflow": ">=2.0.0",
    "transformers": ">=4.0.0",
    "scikit-learn": None,
    "numpy": ">=1.19.0",
    "pandas": None,
    
    # NLP packages
    "spacy": ">=3.0.0",
    "nltk": None,
    "langdetect": None,
    "jieba": None,
    
    # Audio/Video processing
    "openai-whisper": None,
    "pydub": None,
    "moviepy": None,
    
    # Image processing
    "pillow": ">=10.2.0",  # Security fix for CVE
    "opencv-python": None,
    
    # Web scraping
    "beautifulsoup4": None,
    "requests": ">=2.25.0",
    "feedparser": None,
    
    # Utilities
    "python-multipart": None,
    "aiofiles": None,
    "python-dotenv": None,
}

# Patterns for dangerous operations
DANGEROUS_PATTERNS = [
    r"__import__",
    r"eval\s*\(",
    r"exec\s*\(",
    r"compile\s*\(",
    r"globals\s*\(",
    r"locals\s*\(",
]


class PackageValidator:
    """
    Validates packages against whitelist.
    Simple, direct, no magic - just like the kernel.
    """
    
    def __init__(self):
        self.whitelist = ALLOWED_PACKAGES.copy()
        self.dangerous_pattern = re.compile(
            "|".join(DANGEROUS_PATTERNS), 
            re.IGNORECASE
        )
    
    def is_package_allowed(self, package_name: str) -> bool:
        """
        Check if a package is in the whitelist.
        No partial matches, no regex - exact names only.
        """
        # Remove version specifiers if present
        base_name = package_name.split("==")[0].split(">=")[0].split("<=")[0].strip()
        return base_name.lower() in {k.lower() for k in self.whitelist.keys()}
    
    def validate_install_command(self, command: str) -> tuple[bool, str]:
        """
        Validate a pip install command.
        Returns (is_valid, reason)
        """
        # Check for dangerous patterns
        if self.dangerous_pattern.search(command):
            return False, "Command contains dangerous patterns"
        
        # Extract package names from command
        # Simple parsing - no complex regex
        parts = command.replace("pip install", "").strip().split()
        packages = []
        
        skip_next = False
        for part in parts:
            if skip_next:
                skip_next = False
                continue
            
            # Skip flags
            if part.startswith("-"):
                # Some flags take arguments
                if part in ["-i", "--index-url", "-f", "--find-links"]:
                    skip_next = True
                continue
            
            packages.append(part)
        
        # Validate each package
        invalid_packages = []
        for pkg in packages:
            if not self.is_package_allowed(pkg):
                invalid_packages.append(pkg)
        
        if invalid_packages:
            return False, f"Packages not in whitelist: {', '.join(invalid_packages)}"
        
        return True, "All packages are allowed"
    
    def add_to_whitelist(self, package: str, version_spec: Optional[str] = None):
        """Add a package to the whitelist - use with extreme caution"""
        logger.warning(f"Adding package to whitelist: {package}")
        self.whitelist[package] = version_spec
    
    def remove_from_whitelist(self, package: str):
        """Remove a package from the whitelist"""
        if package in self.whitelist:
            logger.warning(f"Removing package from whitelist: {package}")
            del self.whitelist[package]


# Global validator instance
validator = PackageValidator()


def validate_package_installation(packages: list[str]) -> tuple[bool, list[str]]:
    """
    Validate a list of packages for installation.
    Returns (all_valid, invalid_packages)
    """
    invalid = []
    for pkg in packages:
        if not validator.is_package_allowed(pkg):
            invalid.append(pkg)
    
    return len(invalid) == 0, invalid
