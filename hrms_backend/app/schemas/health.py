from pydantic import BaseModel


class HealthCheck(BaseModel):
    status: str
    app: str
    version: str
    environment: str
    company: str
    db: str
    redis: str
