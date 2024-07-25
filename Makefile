PYTHON3 ?= python3
ANTLR4 ?= antlr4

parsers: $(PWD)/nl2bench/_antlr4_logic_parser $(PWD)/nl2bench/_antlr4_verilog_parser

$(PWD)/nl2bench/_antlr4_logic_parser: $(PWD)/grammars/lib/logic.g4
	cd $$(dirname $<); antlr4 -Dlanguage=Python3 -visitor $^ -o $@

$(PWD)/nl2bench/_antlr4_verilog_parser: $(PWD)/grammars/verilog/VerilogLexer.g4 $(PWD)/grammars/verilog/VerilogParser.g4
	cd $$(dirname $<); antlr4 -Dlanguage=Python3 -visitor $^ -o $@

all: dist

.PHONY: dist
dist: venv/manifest.txt $(parsers)
	./venv/bin/poetry build

.PHONY: lint
lint: venv/manifest.txt
	./venv/bin/black --check .
	./venv/bin/flake8 .

venv: venv/manifest.txt
venv/manifest.txt: ./pyproject.toml
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
	rm -rf _lef_parser_antlr/
	rm -rf build/
	rm -rf dist/
	rm -rf htmlcov/
	rm -rf *.egg-info/
	rm -rf .antlr/
	rm -f .coverage
