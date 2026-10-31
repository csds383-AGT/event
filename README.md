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
   the first run takes a few minutes: it builds the six images, generates the gRPC code from the `.proto` files in `concerts/`, `artists/`, `categories/` and `media/` inside them, and creates the two databases from the `schema.sql` and `seed.sql` files in `db/` and `artists/db/`. after that it starts in seconds
4. open http://localhost:5001
5. press ctrl+c to stop

nothing else needs installing on your machine, since python, the gRPC code and postgres all live in the containers.

## what's running

| container | inside docker | from your machine |
|---|---|---|
| kong (api gateway) | `172.30.83.30:8000` (http) and `:9080` (gRPC) on `app_net` | http://localhost:5001 and `localhost:9080` |
| web (flask site) | `172.30.83.10:5000` on `app_net` | through kong at http://localhost:5001 |
| logic (concerts, categories and media gRPC server) | `172.30.83.20:50051` on `app_net` | not reachable, it only accepts calls from kong and artists |
| artists (gRPC server) | `172.30.83.50:50051` on `app_net` | not reachable, it only accepts calls from kong and logic |
| db (postgres) | `db:5432` on `db_net` | `localhost:5433`, user, password and database all `festhub` |
| artists-db (postgres) | `artists-db:5432` on `artists_db_net` | `localhost:5435`, user, password and database all `artists` |

## dev notes

while it's running, saved changes to `website.py`, `templates/`, `backend-server.py`, `logic/`, `common/`, `artists/service.py`, and `artists/server.py` show up on their own, and changes to any of the `.proto` files, `requirements.txt`, or `kong/kong.yml` rebuild the containers.

to reset the databases to the demo data (needed whenever a `schema.sql` or `seed.sql` in `db/` or `artists/db/` changes):

```bash
docker compose down -v
```

if you want to access the postgres database  in your ide, use this config: ![img.png](img.png)
