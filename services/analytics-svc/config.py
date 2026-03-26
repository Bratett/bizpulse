import os


class Settings:
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "bizpulse")
    POSTGRES_READONLY_USER: str = os.getenv("POSTGRES_READONLY_USER", "bizpulse_readonly")
    POSTGRES_READONLY_PASSWORD: str = os.getenv("POSTGRES_READONLY_PASSWORD", "")
    POSTGRES_SSLMODE: str = os.getenv("POSTGRES_SSLMODE", "disable")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    ANALYTICS_SVC_PORT: int = int(os.getenv("ANALYTICS_SVC_PORT", "8081"))
    ALLOWED_ORIGINS: list[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_READONLY_USER}:{self.POSTGRES_READONLY_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            f"?sslmode={self.POSTGRES_SSLMODE}"
        )


settings = Settings()
