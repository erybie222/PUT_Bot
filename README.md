## 🗄️ Database

This project uses a PostgreSQL database with the `pgvector` extension. The database is run in a Docker environment.

### How to run the database

1. Make sure you have [Docker](https://www.docker.com/) installed and running.
2. Copy the `.env.example` file to `.env` and set your desired database credentials:
   ```bash
   cp .env.example .env
   ```
3. In the root directory of the project, run the following command:
   ```bash
   docker-compose up -d
   ```
   _The `-d` flag runs the container in the background (detached mode)._

On the first run, Docker will use the `init.sql` file to automatically create the required database schema.

### Managing the database via pgAdmin

The environment includes **pgAdmin** to easily manage and query the database through a web interface:

1. Open your browser and navigate to `http://localhost:5050`.
2. Log in using the default credentials:
   - **Email:** `admin@admin.com`
   - **Password:** `root`
3. Register a new server connection:
   - **Connection tab:**
     - **Host name/address:** `PUT_Bot_db`
     - **Port:** `5432`
     - **Maintenance database:** Use the `DB_NAME` value from your `.env` (default: `wiitek_db`)
     - **Username:** Use the `DB_USER` value from your `.env` (default: `wiitek_admin`)
     - **Password:** Use the `DB_PASSWORD` value from your `.env` (default: `bezpieczne_haslo_projektowe`)
   - Click **Save**.

### Stopping the database

To stop the running database container (without deleting data), execute:

```bash
docker-compose down
```

If you want to stop the database **and delete all its data** (hard reset, deleting the Docker volume):

```bash
docker-compose down -v
```

## 📦 Package Management (uv)

This project uses `uv` for fast Python package management and virtual environment handling.

### Installing dependencies

1. Make sure you have `uv` installed (e.g., via `pip install uv` or follow instructions on [their GitHub](https://github.com/astral-sh/uv)).
2. To create the virtual environment and install all dependencies defined in `pyproject.toml` / `uv.lock`, run:
   ```bash
   uv sync
   ```

### Adding new packages

To add a new package to the project and update the configuration, use:
```bash
uv add <package_name>
```

### Running the application

To execute scripts within the project's virtual environment, use:
```bash
uv run main.py
```
