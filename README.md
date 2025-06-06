# IngeXai

A simplified document connector and API service for Engineering Lead assessment.

## Features

- RESTful API for document management (CRUD)
- OAuth2 authentication middleware (token-based)
- Mocked external document system integration
- Document ingestion pipeline (PDF/docx/txt extraction, chunking)
- PostgreSQL storage with SQLAlchemy ORM
- In-memory vector embedding store (mocked)
- Logging and error handling
- Unit tests for key components
- Auto-generated API docs (Swagger UI & ReDoc)
- Alembic migrations

## Setup

1. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```
2. **Set up environment variables:**  
   Create a `.env` file with:
   ```
   DATABASE_URL=postgresql://user:password@localhost/ingexai
   SECRET_KEY=your_secret_key
   ALGORITHM=HS256
   ```
3. **Run database migrations:**
   ```
   PYTHONPATH=. alembic upgrade head
   ```
   **If you make changes to the models:**
   1. Generate a new migration:
      ```
      PYTHONPATH=. alembic revision --autogenerate -m "Describe your change"
      ```
   2. Apply the migration:
      ```
      PYTHONPATH=. alembic upgrade head
      ```
4. **Start the app:**
   ```
   uvicorn app.main:app --reload
   ```
5. **Run tests:**
   ```
   PYTHONPATH=. pytest --maxfail=3 --disable-warnings -v
   ```

## API Documentation

- Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative ReDoc docs: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Example Usage

- **Register a user:**  
  `POST /users/` with form data `username` and `password`
- **Login:**  
  `POST /users/token` with form data `username` and `password` (returns access token)
- **Upload a document:**  
  `POST /documents/upload` with file upload and Bearer token
- **List documents:**  
  `GET /documents` with Bearer token

## Architectural Decisions

- **FastAPI** for async REST API and automatic documentation.
- **SQLAlchemy ORM** for PostgreSQL integration and migrations via Alembic.
- **Modular structure:**  
  - `app/api` for routes  
  - `app/models` for DB models  
  - `app/services` for business logic (ingestion, vector store, mock external API)  
  - `app/core` for config and authentication  
  - `app/db` for DB session and init
- **In-memory vector store** for embeddings (mocked, easily swappable for a real vector DB).
- **Mock external document system** to simulate integration with third-party APIs.
- **Comprehensive error handling** and logging for observability and debugging.

## Security Considerations

- OAuth2 with password hashing for authentication.
- Secrets and DB credentials loaded from environment variables.
- File type validation and input sanitization on upload.
- All document endpoints require authentication.
- Recommendations for production:
  - Use HTTPS
  - Use strong, unique secrets
  - Enable rate limiting and monitoring
  - Regularly update dependencies

## Potential Improvements

- Replace in-memory vector store with a persistent vector DB (e.g., Pinecone, Weaviate).
- Add role-based access control and user management endpoints.
- Implement background tasks for heavy processing (e.g., Celery).
- Add more granular logging and monitoring.
- Use Docker for reproducible deployment.
- Add more comprehensive integration and security tests.
- Support more document types and advanced chunking strategies.

## Database Design

The PostgreSQL schema consists of three main tables:

### users

| Column          | Type      | Constraints                | Description                |
|-----------------|-----------|----------------------------|----------------------------|
| id              | Integer   | Primary Key, Auto-increment| User ID                    |
| username        | String    | Unique, Not Null, Indexed  | Username                   |
| hashed_password | String    | Not Null                   | Hashed password            |
| created_at      | DateTime  | Not Null                   | User creation timestamp    |

### documents

| Column     | Type      | Constraints                | Description                |
|------------|-----------|----------------------------|----------------------------|
| id         | Integer   | Primary Key, Auto-increment| Document ID                |
| name       | String    | Not Null                   | Document name              |
| owner_id   | Integer   | ForeignKey(users.id)       | Owner (user) ID            |
| content    | Text      | Not Null                   | Extracted document text    |
| created_at | DateTime  | Not Null                   | Document creation timestamp|

### document_chunks

| Column      | Type      | Constraints                | Description                |
|-------------|-----------|----------------------------|----------------------------|
| id          | Integer   | Primary Key, Auto-increment| Chunk ID                   |
| document_id | Integer   | ForeignKey(documents.id)   | Parent document ID         |
| chunk_index | Integer   | Not Null                   | Chunk order/index          |
| chunk_text  | Text      | Not Null                   | Chunked text               |
| embedding   | Text      | Nullable                   | Mocked embedding (JSON/text)|
| created_at  | DateTime  | Not Null                   | Chunk creation timestamp   |
| status      | String    | Default 'active'           | Chunk status               |

### Migration Scripts

- Alembic migration scripts are located in `alembic/versions/`.
- To apply migrations, run:
  ```
  alembic upgrade head
  ```

# License

MIT License

# Author

[Your Name]

