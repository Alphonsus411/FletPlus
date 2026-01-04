PROFILE=build/profile.txt
CONFIG=build_config.yaml
PROFILE_LIMIT=30
CONFIG_LIMIT=4
RUST_MANIFEST=fletplus/router/router_rs/Cargo.toml

.PHONY: profile update-build-config build build-rust

profile:
	@mkdir -p build
	python -m cProfile -o $(PROFILE) -s cumtime -m compileall fletplus

update-build-config: $(PROFILE)
	python tools/select_cython_modules.py --profile $(PROFILE) --config $(CONFIG) --limit $(CONFIG_LIMIT)

build-rust:
	@if command -v maturin >/dev/null 2>&1; then \
		maturin build --manifest-path $(RUST_MANIFEST) --release; \
		WHEEL=$$(find fletplus/router/router_rs/target/wheels -maxdepth 1 -name 'router_rs-*.whl' -print -quit); \
		if [ "$$WHEEL" != "" ]; then pip install $$WHEEL; fi; \
	else \
		echo "maturin no está instalado; omitiendo build de router_rs"; \
	fi

build: update-build-config build-rust
	python setup.py build_ext --inplace
