import os
import subprocess
import paramiko
from typing import Tuple, Optional

def generate_ssh_key_pair() -> Tuple[str, str]:
    """Generate a new SSH key pair."""
    # Create a temporary directory for the keys
    temp_dir = os.path.join(os.getcwd(), "temp_ssh")
    os.makedirs(temp_dir, exist_ok=True)

    # Generate key paths
    private_key_path = os.path.join(temp_dir, "id_ed25519")
    public_key_path = os.path.join(temp_dir, "id_ed25519.pub")

    try:
        # Generate the key pair using ssh-keygen
        subprocess.run(
            [
                "ssh-keygen",
                "-t", "ed25519",
                "-f", private_key_path,
                "-N", "",  # No passphrase
                "-C", f"discord-bot-panel-{os.getpid()}"
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Read the generated keys
        with open(private_key_path, "r") as f:
            private_key = f.read()

        with open(public_key_path, "r") as f:
            public_key = f.read()

        return private_key, public_key
    finally:
        # Clean up temporary files
        if os.path.exists(private_key_path):
            os.remove(private_key_path)
        if os.path.exists(public_key_path):
            os.remove(public_key_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)

def generate_ssh_key_pair_paramiko() -> Tuple[str, str]:
    """Generate a new SSH key pair using paramiko."""
    # Generate a new key
    key = paramiko.Ed25519Key.generate()

    # Get the private key in OpenSSH format
    private_key = key.export_private_key().decode("utf-8")

    # Get the public key in OpenSSH format
    public_key = f"{key.get_name()} {key.get_base64()} discord-bot-panel-{os.getpid()}"

    return private_key, public_key

def save_ssh_key_to_file(private_key: str, key_path: str) -> bool:
    """Save the SSH private key to a file."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(key_path), exist_ok=True)

        # Write the private key to the file
        with open(key_path, "w") as f:
            f.write(private_key)

        # Set correct permissions (read/write for owner only)
        os.chmod(key_path, 0o600)

        return True
    except Exception:
        return False

def git_clone_with_ssh(repo_url: str, target_dir: str, private_key_path: str) -> Tuple[bool, Optional[str]]:
    """Clone a Git repository using SSH."""
    try:
        # Get the absolute path for the target directory
        abs_target_dir = os.path.abspath(target_dir)

        # Ensure target directory exists
        os.makedirs(os.path.dirname(abs_target_dir), exist_ok=True)

        # Set up GIT_SSH_COMMAND to use the private key
        env = os.environ.copy()
        env["GIT_SSH_COMMAND"] = f"ssh -i {private_key_path} -o StrictHostKeyChecking=no"

        # Clone the repository
        result = subprocess.run(
            ["git", "clone", repo_url, abs_target_dir],
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        return True, None
    except subprocess.CalledProcessError as e:
        return False, e.stderr.decode("utf-8")
    except Exception as e:
        return False, str(e)

def git_pull_with_ssh(repo_dir: str, private_key_path: str) -> Tuple[bool, Optional[str]]:
    """Pull updates from a Git repository using SSH."""
    try:
        # Get the absolute path for the repository directory
        abs_repo_dir = os.path.abspath(repo_dir)

        # Set up GIT_SSH_COMMAND to use the private key
        env = os.environ.copy()
        env["GIT_SSH_COMMAND"] = f"ssh -i {private_key_path} -o StrictHostKeyChecking=no"

        # Pull the repository
        result = subprocess.run(
            ["git", "pull"],
            cwd=abs_repo_dir,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        return True, result.stdout.decode("utf-8")
    except subprocess.CalledProcessError as e:
        return False, e.stderr.decode("utf-8")
    except Exception as e:
        return False, str(e)
