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
4. open http://localhost:5001
5. press ctrl+c to stop

nothing else needs installing on your machine, since python, the gRPC code and postgres all live in the containers.

## CLI

The CLI lives in `clients/cli/` and uses Kong's gRPC gateway. To run with Docker:

```bash
docker compose run --rm --build cli shell
```

To run outside Docker (with the containers running), install the packages in `requirements.txt`, generate the gRPC code into `clients/cli/`, and run it from there. It connects to `localhost:9080` unless you set the `GATEWAY_HOST` and `GATEWAY_PORT` environment variables.

```bash
python3 -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\activate        # Windows

pip install -r requirements.txt

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
```

## what's running

| container | inside docker | from your machine |
|---|---|---|
| kong (api gateway) | `172.30.83.30:8000` (http) and `:9080` (gRPC) on `app_net` | http://localhost:5001 and `localhost:9080` |
| web (flask site) | `172.30.83.10:5000` on `app_net` | through kong at http://localhost:5001 |
| cli (on-demand client) | short-lived client on `app_net` | `docker compose run --rm --build cli ...` |
| concerts (gRPC server) | `172.30.83.40:50051` on `app_net` | not reachable, it only accepts calls from kong, artists, categories and media |
| artists (gRPC server) | `172.30.83.50:50051` on `app_net` | not reachable, it only accepts calls from kong and concerts |
| categories (gRPC server) | `172.30.83.60:50051` on `app_net` | not reachable, it only accepts calls from kong and concerts |
| media (gRPC server) | `172.30.83.70:50051` on `app_net` | not reachable, it only accepts calls from kong and concerts |
| concerts-db (postgres) | `concerts-db:5432` on `concerts_db_net` | `localhost:5434`, user, password and database all `concerts` |
| artists-db (postgres) | `artists-db:5432` on `artists_db_net` | `localhost:5435`, user, password and database all `artists` |
| categories-db (postgres) | `categories-db:5432` on `categories_db_net` | `localhost:5436`, user, password and database all `categories` |
| media-db (postgres) | `media-db:5432` on `media_db_net` | `localhost:5437`, user, password and database all `media` |

## dev notes

while it's running, saved changes to `clients/`, `services/`, and `common/` show up on their own, and changes to any service `.proto` file, `requirements.txt`, or `gateway/kong.yml` rebuild the relevant containers.

to reset the databases to the demo data (needed whenever a service `schema.sql` or `seed.sql` changes):

```bash
docker compose down -v
```

if you want to access a postgres database in your ide, use this config with the port, user, password and database from the table above: ![img.png](img.png)
