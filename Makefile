PHONY: test

# You may need
# export PATH=~/.local/bin:$PATH

all: test

test:
	DEBUG=1 DB_NAME=mrs_test DB_ENGINE=django.db.backends.postgresql tox -e py36-dj21

qa:
	tox -e qa

jsqa:
	yarn run lint

run:
	DEBUG=1 DB_NAME=mrs_test DB_ENGINE=django.db.backends.postgresql mrs runserver

runprod:
	DEBUG= ALLOWED_HOSTS="localhost" SECRET_KEY="secret" mrs runserver

crawltests:
	DEBUG=1 DB_NAME=mrs_test DB_ENGINE=django.db.backends.postgresql tox -e py36-dj21 src/mrs/tests/test_crawl.py

crawlupdate:
	rm -rf src/mrs/tests/response_fixtures && make crawltests || make crawltests
