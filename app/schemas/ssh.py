from pydantic import BaseModel


class SSHKeyResponse(BaseModel):
    """
    SSH key response schema
    """
    public_key: str
