PROFILE=build/profile.txt
CONFIG=build_config.yaml
PROFILE_LIMIT=30
CONFIG_LIMIT=4
RUST_MANIFESTS=fletplus/router/router_pr_rs/Cargo.toml fletplus/router/router_rs/Cargo.toml fletplus/animation/listeners_rs/Cargo.toml fletplus/animation/listeners_pr_rs/Cargo.toml fletplus/components/smart_table_rs/Cargo.toml

.PHONY: profile update-build-config build build-rust rustify-auto qa check-canonical-repo-links test-preflight test-preflight-full test-preflight-perf pytest ruff black mypy bandit pip-audit safety qa-all

profile:
	@mkdir -p build
	python -m cProfile -o $(PROFILE) -s cumtime -m compileall fletplus

update-build-config: profile
	python tools/select_cython_modules.py --profile $(PROFILE) --config $(CONFIG) --limit $(CONFIG_LIMIT)

build-rust:
	# Nota: en Makefile, cada línea de receta debe iniciar con TAB real (no espacios).
	@if command -v maturin >/dev/null 2>&1; then \
		for manifest in $(RUST_MANIFESTS); do \
			maturin build --manifest-path $$manifest --release; \
			WHEEL=$$(find $$(dirname $$manifest)/target/wheels -maxdepth 1 -name '*.whl' -print -quit); \
			if [ "$$WHEEL" != "" ]; then pip install $$WHEEL; fi; \
		done; \
	else \
		echo "maturin no está instalado; omitiendo build de extensiones Rust"; \
	fi

rustify-auto:
	tools/pyrust_native_auto.sh

build: update-build-config build-rust
	python -m build

qa:
	./tools/qa.sh

check-canonical-repo-links:
	python tools/check_canonical_repo_links.py

test-preflight:
	python tools/check_test_dependencies.py --suite default

test-preflight-full:
	python tools/check_test_dependencies.py --suite unit --suite cli --suite websocket

test-preflight-perf:
	python tools/check_test_dependencies.py --suite perf

pytest:
	python -m pytest

ruff:
	python -m ruff check .

black:
	python -m black --check .

mypy:
	python -m mypy fletplus

bandit:
	python -m bandit -c pyproject.toml -r fletplus

pip-audit:
	python -m pip_audit -r requirements.txt -r requirements-dev.txt --policy pip-audit.policy.json

safety:
	python -m safety check -r requirements.txt -r requirements-dev.txt --policy-file safety-policy.yml

qa-all: test-preflight-full ruff black mypy bandit pip-audit safety pytest
