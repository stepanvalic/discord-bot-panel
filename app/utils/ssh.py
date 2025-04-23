import os
import subprocess
import paramiko
import logging
import stat

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/ssh.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ssh")


def ensure_ssh_configured() -> str:
    """
    Ensure SSH is configured for Git operations
    Returns the path to the private key file
    """
    try:
        # Check if we have our SSH key
        ssh_dir = os.path.expanduser("~/.ssh")
        panel_ssh_dir = os.path.join(ssh_dir, "discord-bot-panel")
        private_key_file = os.path.join(panel_ssh_dir, "id_rsa")

        if os.path.exists(private_key_file):
            # Set up SSH agent with our key
            setup_ssh_agent(private_key_file)
            logger.info("SSH configuration verified")
            return private_key_file
        else:
            logger.warning("SSH key not found, generating new key pair")
            # Generate a new key pair if none exists
            generate_ssh_key_pair()
            return private_key_file
    except Exception as e:
        logger.error(f"Error ensuring SSH configuration: {e}")
        raise


def setup_ssh_agent(private_key_file: str) -> None:
    """
    Set up SSH agent with our key
    """
    try:
        # Start ssh-agent if not running
        subprocess.run(
            ["ssh-agent", "-s"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Add the key to ssh-agent
        subprocess.run(
            ["ssh-add", private_key_file],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        logger.info(f"Added key {private_key_file} to ssh-agent")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to set up ssh-agent: {e}")
    except Exception as e:
        logger.warning(f"Error setting up ssh-agent: {e}")


def generate_ssh_key_pair() -> tuple[str, str]:
    """
    Generate a new SSH key pair for use with Git without modifying global SSH config
    """
    try:
        # Create SSH directory if it doesn't exist
        ssh_dir = os.path.expanduser("~/.ssh")
        panel_ssh_dir = os.path.join(ssh_dir, "discord-bot-panel")
        os.makedirs(panel_ssh_dir, exist_ok=True)

        # Generate a new key pair
        key = paramiko.RSAKey.generate(2048)

        # Define key file paths
        private_key_file = os.path.join(panel_ssh_dir, "id_rsa")
        public_key_file = os.path.join(panel_ssh_dir, "id_rsa.pub")

        # Write the private key
        key.write_private_key_file(private_key_file)

        # Set correct permissions for private key (600)
        os.chmod(private_key_file, stat.S_IRUSR | stat.S_IWUSR)

        # Get the public key in OpenSSH format
        public_key = f"ssh-rsa {key.get_base64()} discord-bot-panel"

        # Write the public key to file
        with open(public_key_file, "w") as f:
            f.write(public_key)

        # Set correct permissions for public key (644)
        os.chmod(public_key_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

        # Read the private key
        with open(private_key_file, "r") as f:
            private_key = f.read()

        # Add github.com to known_hosts if not already there
        known_hosts_file = os.path.join(ssh_dir, "known_hosts")
        try:
            # Check if github.com is already in known_hosts
            if os.path.exists(known_hosts_file):
                with open(known_hosts_file, "r") as f:
                    known_hosts_content = f.read()
                if "github.com" not in known_hosts_content:
                    # Add github.com to known_hosts
                    subprocess.run(
                        ["ssh-keyscan", "-t", "rsa", "github.com"],
                        stdout=open(known_hosts_file, "a"),
                        stderr=subprocess.PIPE,
                        check=True
                    )
            else:
                # Create known_hosts file with github.com
                subprocess.run(
                    ["ssh-keyscan", "-t", "rsa", "github.com"],
                    stdout=open(known_hosts_file, "w"),
                    stderr=subprocess.PIPE,
                    check=True
                )

            # Set correct permissions for known_hosts file (644)
            os.chmod(known_hosts_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

            logger.info("Added github.com to known_hosts")
        except Exception as e:
            logger.warning(f"Failed to add github.com to known_hosts: {e}")

        # Set up SSH agent with our key
        setup_ssh_agent(private_key_file)

        logger.info("SSH key pair generated and configured successfully")

        return public_key, private_key
    except Exception as e:
        logger.error(f"Error generating SSH key pair: {e}")
        raise
