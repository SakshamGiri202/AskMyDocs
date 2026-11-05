from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_USER: str = "askmydocs_user"
    POSTGRES_PASSWORD: str = "askmydocs_password"
    POSTGRES_DB: str = "askmydocs_db" 
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    OPENSEARCH_HOST: str = "localhost"
    OPENSEARCH_PORT: int = 9200

    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIM: int = 384


    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()

