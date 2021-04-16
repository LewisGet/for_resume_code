# this project is not working not

not working now.

## These codes are just written to prove my personal working ability

coding some code for resume.

let's build a online card game with django server first.

this is my first time using this framework, it will take a while.

# Getting start

setting up config files

```sh
cp ember/_settings.py ember/settings.py
```

# Tests

```sh
python -m coverage run manage.py test

python -m coverage report
```

### without coverage

```sh
python manage.py test
```

### test one function

```sh
python manage.py test game.tests.GameTestCase.test_battle
```

### login test by curl

```sh
curl http://127.0.0.1:8000/login/ --data "username={username_string}&password={password_string}"
```
