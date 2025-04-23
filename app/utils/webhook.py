import os
import secrets
import hmac
import hashlib
from typing import Optional

def generate_webhook_key(length: int = 32) -> str:
    """Generate a random webhook key."""
    return secrets.token_urlsafe(length)

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify the webhook signature."""
    if not signature or not secret:
        return False
    
    # Remove prefix if present
    if signature.startswith("sha256="):
        signature = signature[7:]
    
    # Calculate expected signature
    expected_signature = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(signature, expected_signature)

def process_github_webhook(payload: dict) -> Optional[dict]:
    """Process a GitHub webhook payload."""
    # Check if this is a push event
    if payload.get("ref") != "refs/heads/main" and payload.get("ref") != "refs/heads/master":
        return {"status": "ignored", "reason": "Not a push to main/master branch"}
    
    # Get repository information
    repository = payload.get("repository", {})
    repo_name = repository.get("name")
    repo_url = repository.get("clone_url")
    
    if not repo_name or not repo_url:
        return {"status": "error", "reason": "Missing repository information"}
    
    # Get commit information
    commits = payload.get("commits", [])
    commit_messages = [commit.get("message") for commit in commits if commit.get("message")]
    
    return {
        "status": "success",
        "repository": repo_name,
        "url": repo_url,
        "branch": payload.get("ref").replace("refs/heads/", ""),
        "commits": len(commits),
        "commit_messages": commit_messages
    }

def process_gitlab_webhook(payload: dict) -> Optional[dict]:
    """Process a GitLab webhook payload."""
    # Check if this is a push event
    if payload.get("ref") != "refs/heads/main" and payload.get("ref") != "refs/heads/master":
        return {"status": "ignored", "reason": "Not a push to main/master branch"}
    
    # Get repository information
    project = payload.get("project", {})
    repo_name = project.get("name")
    repo_url = project.get("git_ssh_url")
    
    if not repo_name or not repo_url:
        return {"status": "error", "reason": "Missing repository information"}
    
    # Get commit information
    commits = payload.get("commits", [])
    commit_messages = [commit.get("message") for commit in commits if commit.get("message")]
    
    return {
        "status": "success",
        "repository": repo_name,
        "url": repo_url,
        "branch": payload.get("ref").replace("refs/heads/", ""),
        "commits": len(commits),
        "commit_messages": commit_messages
    }
