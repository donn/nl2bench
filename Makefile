PYTHON3 ?= python3
ANTLR4 ?= antlr4
PARSERS ?= _nl2bench_antlr4_liblogic/LogicParser.py

all: dist

.PHONY: dist
dist: venv/manifest.txt $(PARSERS)
	./venv/bin/poetry build
	
parsers: $(PARSERS)

_nl2bench_antlr4_liblogic/LogicParser.py: grammars/lib/logic.g4
	cd $$(dirname $<); antlr4 -Dlanguage=Python3 -visitor logic.g4 -o $(PWD)/$(@D)
	
.PHONY: lint
lint: venv/manifest.txt
	./venv/bin/black --check .
	./venv/bin/flake8 .

venv: venv/manifest.txt
venv/manifest.txt: ./pyproject.toml ./poetry.lock
	rm -rf venv
	python3 -m venv ./venv
	PYTHONPATH= ./venv/bin/python3 -m pip install --upgrade pip
	PYTHONPATH= ./venv/bin/python3 -m pip install --upgrade wheel poetry poetry-plugin-export
	PYTHONPATH= ./venv/bin/poetry export --with dev --without-hashes --format=requirements.txt --output=requirements_tmp.txt
	PYTHONPATH= ./venv/bin/python3 -m pip install --upgrade -r requirements_tmp.txt
	PYTHONPATH= ./venv/bin/python3 -m pip freeze > $@
	@echo ">> Venv prepared."

.PHONY: clean
clean:
	rm -rf _nl2bench_antlr4*/
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/
	rm -rf *.egg-info/
	rm -rf .antlr/
	rm -f .coverage
