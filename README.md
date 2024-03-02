# dropwishes-api
API for DropWishes App

To run locally run the below and go to http://127.0.0.1:8000/api/docs/:
```
docker-compose up
```

Run test locally
```
docker-compose run --rm app sh -c "python manage.py test"
```

Run linting locally
```
docker-compose run --rm app sh -c "python manage.py wait_for_db && flake8"
```

Create migrations files:
```
docker-compose run --rm app sh -c "python manage.py makemigrations"
```

Run the wait for database to build and then run migrate locally
```
docker-compose run --rm app sh -c "python manage.py wait_for_db && python manage.py migrate"
```



