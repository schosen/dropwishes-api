# wishlist-app-api
Wishlist API


## Build and Run locally

Create migrations files:
```
docker compose run --rm app sh -c "python manage.py makemigrations"
```

Run command to wait for database to build and then run migrate locally:
```
docker compose run --rm app sh -c "python manage.py wait_for_db && python manage.py migrate"
```

build application locally:
```
docker compose build
```

run application:
```
docker compose up
```

to stop and remove containers and volumes:
```
docker compose down
```


## API

After build and run, you can find api documentation at `http://localhost:8000/api/docs/`

Admin url is `http://127.0.0.1:8000/admin/login/`


## Tests

Run tests locally:
```
docker compose run --rm app sh -c "python manage.py test"
```

Run linting locally:
```
docker compose run --rm app sh -c "python manage.py wait_for_db && flake8"
```

## Pipeline

Github actions is used to push the image to dockerhub and run tests locally


