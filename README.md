# FastAPI Posts API

A REST API for user accounts, JWT authentication, posts, and post votes. It is built with FastAPI, SQLAlchemy, and PostgreSQL.

Run all commands from this project directory unless a command says otherwise.

## Features

- Create users with bcrypt-hashed passwords
- Log in with an email and password to receive a JWT access token
- Create, read, update, and delete posts (owners can modify only their own posts)
- Search and paginate posts, with vote counts
- Add or remove a vote from a post
- Interactive OpenAPI documentation at `/docs`

## Prerequisites

- Python 3.10 or newer
- PostgreSQL 14 or newer, running locally or remotely
- Git (optional, for cloning)

## 1. Get the project ready

Clone the repository (if needed), then open a terminal in the project directory:

```powershell
git clone <repository-url>
cd fastapi_app_sqlalchemy
```

Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell prevents activation, run this for the current terminal and try again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Install the dependencies used by the current API package:

```powershell
pip install -r requirements.txt
```

## 2. Create a PostgreSQL database

Create a database and a user. The following example uses `fastapi` for both names; choose your own strong password.

```sql
CREATE USER fastapi_user WITH PASSWORD 'choose-a-strong-password';
CREATE DATABASE fastapi OWNER fastapi_user;
```

Run those statements in `psql`, pgAdmin, or another PostgreSQL client. Ensure that the database server accepts connections from the host where you will run the API.

## 3. Configure environment variables

At the project root, create a file named `.env`. It is ignored by Git, so credentials will not be committed. Add the following values and replace the examples:

```env
DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_PASSWORD=choose-a-strong-password
DATABASE_NAME=fastapi
DATABASE_USERNAME=fastapi_user
SECRET_KEY=replace-with-a-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Generate a suitable `SECRET_KEY`, for example:

```powershell
py -c "import secrets; print(secrets.token_urlsafe(32))"
```

On startup, SQLAlchemy creates the required tables (`users`, `posts_sqlalchemy`, and `votes`) if they do not already exist. There are currently no Alembic migration files in this repository.

## 4. Run the API

Start the development server with automatic reload:

```powershell
uvicorn main:app --reload
```

The server listens at <http://127.0.0.1:8000> by default. Verify it is running:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/
```

Expected response:

```json
{"message":"Hello this is Ashish and you have reached my fastapi app using orm"}
```

Open the interactive documentation in a browser:

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

Press `Ctrl+C` in the server terminal to stop it.

## API overview

| Method | Endpoint | Authentication | Purpose |
| --- | --- | --- | --- |
| `GET` | `/` | No | Basic API response |
| `GET` | `/sqlalchemy` | No | Database connectivity route |
| `POST` | `/users` | No | Register a user |
| `GET` | `/users/{id}` | No | Get a user by ID |
| `POST` | `/login` | No | Get a JWT access token |
| `GET` | `/posts` | Bearer token | List posts; supports `limit`, `skip`, `search` |
| `POST` | `/posts` | Bearer token | Create a post |
| `GET` | `/posts/{id}` | Bearer token | Get a post and its vote count |
| `PUT` | `/posts/{id}` | Bearer token, owner | Update a post |
| `DELETE` | `/posts/{id}` | Bearer token, owner | Delete a post |
| `POST` | `/vote/` | Bearer token | Add (`dir: 1`) or remove (`dir: 0`) a vote |

## 5. Test the API manually

Keep Uvicorn running in one terminal. Run the commands below in a second PowerShell terminal, from any directory.

### A. Create a user

```powershell
$baseUrl = "http://127.0.0.1:8000"
$email = "test.user@example.com"
$password = "test-password-123"

$user = Invoke-RestMethod -Method Post -Uri "$baseUrl/users" -ContentType "application/json" -Body (@{
  email = $email
  password = $password
} | ConvertTo-Json)
$user
```

Confirm that the response contains an `id`, `email`, and `created_at`, but never a password. Use a new email if this command returns a duplicate-user error.

### B. Log in and save the token

`/login` expects form data (not JSON):

```powershell
$login = Invoke-RestMethod -Method Post -Uri "$baseUrl/login" -ContentType "application/x-www-form-urlencoded" -Body "username=$email&password=$password"
$token = $login.access_token
$headers = @{ Authorization = "Bearer $token" }
$login
```

### C. Create a post

```powershell
$post = Invoke-RestMethod -Method Post -Uri "$baseUrl/posts" -Headers $headers -ContentType "application/json" -Body (@{
  title = "My first API post"
  content = "Created while verifying the FastAPI project."
  published = $true
} | ConvertTo-Json)
$postId = $post.id
$post
```

### D. List and retrieve posts

```powershell
Invoke-RestMethod -Uri "$baseUrl/posts?limit=10&skip=0&search=API" -Headers $headers
Invoke-RestMethod -Uri "$baseUrl/posts/$postId" -Headers $headers
```

### E. Vote for the post

```powershell
Invoke-RestMethod -Method Post -Uri "$baseUrl/vote/" -Headers $headers -ContentType "application/json" -Body (@{
  post_id = $postId
  dir = 1
} | ConvertTo-Json)
```

Run the post retrieval command again and confirm its `votes` value increased. To remove the vote, submit the same request with `dir = 0`.

### F. Delete the post

```powershell
Invoke-WebRequest -Method Delete -Uri "$baseUrl/posts/$postId" -Headers $headers
```

Expect HTTP status `204 No Content`. Creating the post under a test account before deleting it keeps this check isolated.

### Testing with Swagger UI

Alternatively, visit `/docs` and use the built-in **Authorize** button. After logging in, copy the `access_token` into the OAuth2 authorization dialog; Swagger then includes it with protected requests.

## Automated tests

This repository does not currently include pytest tests or test configuration. The manual sequence above is the available end-to-end verification workflow. A future test suite should use FastAPI's `TestClient`, a separate test database, and fixtures that create users and authenticated clients.

## Notes and troubleshooting

- **Database connection error:** confirm PostgreSQL is running and that every `DATABASE_*` value in `.env` is correct.
- **Settings validation error at startup:** all eight variables shown in the `.env` example are required.
- **401 "Could not validate credentails":** log in again and send `Authorization: Bearer <access_token>` with the request.
- **403 when editing or deleting:** only the user who created a post may edit or delete it.
- **Port 8000 is already in use:** use another port, for example `uvicorn main:app --reload --port 8001`.
- **Update endpoint:** the current `PUT /posts/{id}` implementation references an undefined variable and will fail until that application bug is corrected. The rest of the manual flow can be tested as written.
