"""
Secure subprocess execution wrapper.
Principle: "Never trust input, always validate, contain the blast radius"
"""

import subprocess
import shlex
import os
from typing import List, Optional, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class SecureSubprocess:
    """
    Secure wrapper for subprocess operations.
    No shell=True, no unvalidated input, no unbounded execution.
    """
    
    # Commands that are allowed to run
    ALLOWED_COMMANDS = {
        "pip": ["{python}", "-m", "pip"],
        "python": ["{python}"],
        "git": ["git"],
        "npm": ["npm"],
        "node": ["node"],
    }
    
    # Maximum execution time in seconds
    DEFAULT_TIMEOUT = 300  # 5 minutes
    MAX_TIMEOUT = 600  # 10 minutes
    
    @classmethod
    def run_command(
        cls,
        command_type: str,
        args: List[str],
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
        check: bool = False
    ) -> Tuple[int, str, str]:
        """
        Run a command securely.
        
        Returns: (returncode, stdout, stderr)
        """
        if command_type not in cls.ALLOWED_COMMANDS:
            raise ValueError(f"Command type '{command_type}' not allowed")
        
        # Build command
        base_command = cls.ALLOWED_COMMANDS[command_type].copy()
        
        # Replace placeholders
        import sys
        for i, part in enumerate(base_command):
            if part == "{python}":
                base_command[i] = sys.executable
        
        # Full command with arguments
        full_command = base_command + args
        
        # Validate arguments don't contain shell metacharacters
        for arg in args:
            if cls._contains_shell_metacharacters(arg):
                raise ValueError(f"Argument contains shell metacharacters: {arg}")
        
        # Set timeout
        if timeout is None:
            timeout = cls.DEFAULT_TIMEOUT
        elif timeout > cls.MAX_TIMEOUT:
            timeout = cls.MAX_TIMEOUT
            logger.warning(f"Timeout capped at {cls.MAX_TIMEOUT} seconds")
        
        # Prepare environment
        safe_env = os.environ.copy()
        if env:
            # Only allow specific environment variables
            allowed_env_vars = ["PATH", "PYTHONPATH", "HOME", "USER", "LANG", "LC_ALL"]
            for key, value in env.items():
                if key in allowed_env_vars or key.startswith("PIP_"):
                    safe_env[key] = value
        
        # Add security environment variables
        safe_env["PIP_NO_INPUT"] = "1"  # Non-interactive pip
        safe_env["GIT_TERMINAL_PROMPT"] = "0"  # Non-interactive git
        safe_env["NPM_CONFIG_YES"] = "true"  # Non-interactive npm
        
        logger.info(f"Executing: {' '.join(full_command)}")
        
        try:
            result = subprocess.run(
                full_command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=check,
                shell=False,  # NEVER use shell=True
                env=safe_env,
                cwd=os.getcwd()  # Explicit working directory
            )
            
            return result.returncode, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout} seconds")
            return -1, "", f"Command timed out after {timeout} seconds"
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with code {e.returncode}")
            return e.returncode, e.stdout or "", e.stderr or ""
        except Exception as e:
            logger.error(f"Unexpected error running command: {e}")
            return -1, "", str(e)
    
    @staticmethod
    def _contains_shell_metacharacters(arg: str) -> bool:
        """Check if argument contains shell metacharacters"""
        dangerous_chars = [
            ";", "&", "|", "`", "$", "(", ")", "{", "}", 
            "[", "]", "<", ">", "*", "?", "!", "~", "\n", "\r"
        ]
        return any(char in arg for char in dangerous_chars)
    
    @classmethod
    def install_package(cls, package: str, user: bool = True) -> Tuple[bool, str]:
        """
        Safely install a Python package.
        Returns (success, message)
        """
        args = ["install"]
        
        if user:
            args.append("--user")
        
        # Add package name (already validated by whitelist)
        args.append(package)
        
        returncode, stdout, stderr = cls.run_command(
            "pip", 
            args,
            timeout=300
        )
        
        if returncode == 0:
            return True, f"Successfully installed {package}"
        else:
            return False, f"Failed to install {package}: {stderr}"


# Global instance
secure_subprocess = SecureSubprocess()
