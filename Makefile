export SHELL := /bin/bash

test:
	python -m unittest discover .

unittests:
	pytest doodad

coverage:
	pytest --cov=doodad --cov-config=.coveragerc doodad

