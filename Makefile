PROFILE=build/profile.txt
CONFIG=build_config.yaml
PROFILE_LIMIT=30
CONFIG_LIMIT=4

.PHONY: profile update-build-config build

profile:
	@mkdir -p build
	python -m cProfile -o $(PROFILE) -s cumtime -m compileall fletplus

update-build-config: $(PROFILE)
	python tools/select_cython_modules.py --profile $(PROFILE) --config $(CONFIG) --limit $(CONFIG_LIMIT)

build: update-build-config
	python setup.py build_ext --inplace
