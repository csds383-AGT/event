# FestHub

## first run

1. install latest [docker desktop](https://www.docker.com/products/docker-desktop/) and open it. 
2. clone the repo and go into it
   ```bash
   git clone https://github.com/csds383-AGT/microservice.git
   cd microservice
   ```
3. start everything
   ```bash
   docker compose up --build --watch
   ```
   the first run takes a few minutes: it builds the images, generates the gRPC code from the service `.proto` files, and creates the databases from each service's `schema.sql` and `seed.sql`. after that it starts in seconds
4. open http://localhost:5001
5. press ctrl+c to stop

nothing else needs installing on your machine, since python, the gRPC code and postgres all live in the containers.

## CLI

The CLI lives in `clients/cli/` and uses Kong's gRPC gateway. To run with Docker:

```bash
docker compose run --rm cli show concert
docker compose run --rm cli create artist "Example Artist" artist@example.com
```

To run outside Docker, install the packages in `requirements.txt` and
set `GATEWAY_HOST` and `GATEWAY_PORT` in clients/cli/cli_api.py (defaults: `localhost` and `9080`).

```bash
python3 -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows

pip install -r requirements.txt
```

python3 -m grpc_tools.protoc \
  -I services/concerts \
  -I services/artists \
  -I services/categories \
  -I services/media \
  --python_out=clients/cli \
  --grpc_python_out=clients/cli \
  services/concerts/concerts.proto \
  services/artists/artists.proto \
  services/categories/categories.proto \
  services/media/media.proto


  cd clients/cli
python3 cli.py show concert

## what's running

| container | inside docker | from your machine |
|---|---|---|
| kong (api gateway) | `172.30.83.30:8000` (http) and `:9080` (gRPC) on `app_net` | http://localhost:5001 and `localhost:9080` |
| web (flask site) | `172.30.83.10:5000` on `app_net` | through kong at http://localhost:5001 |
| cli (on-demand client) | short-lived client on `app_net` | `docker compose run --rm cli ...` |
| logic (concerts, categories and media gRPC server) | `172.30.83.20:50051` on `app_net` | not reachable, it only accepts calls from kong and artists |
| artists (gRPC server) | `172.30.83.50:50051` on `app_net` | not reachable, it only accepts calls from kong and logic |
| db (postgres) | `db:5432` on `db_net` | `localhost:5433`, user, password and database all `festhub` |
| artists-db (postgres) | `artists-db:5432` on `artists_db_net` | `localhost:5435`, user, password and database all `artists` |

## dev notes

while it's running, saved changes to `clients/`, `services/`, and `common/` show up on their own, and changes to any service `.proto` file, `requirements.txt`, or `gateway/kong.yml` rebuild the relevant containers.

to reset the databases to the demo data (needed whenever a service `schema.sql` or `seed.sql` changes):

```bash
docker compose down -v
```

if you want to access the postgres database  in your ide, use this config: ![img.png](img.png)
