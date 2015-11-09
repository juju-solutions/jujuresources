PROJECT=jujuresources
SUITE=unstable

.PHONY: all
all:
	@echo "make test"
	@echo "make source - Create source package"
	@echo "make clean"
	@echo "make userinstall - Install locally"
	@echo "make docs - Build html documentation"
	@echo "make release - Build and upload package and docs to PyPI"

.PHONY: source
source: setup.py
	scripts/update-revno
	python setup.py sdist

.PHONY: clean
clean:
	-python setup.py clean
	find . -name '*.pyc' -delete
	rm -rf dist/*
	rm -rf .tox
	rm -rf docs/_build

.PHONY: docclean
docclean:
	-rm -rf docs/_build

.PHONY: userinstall
userinstall:
	scripts/update-revno
	python setup.py install --user

.PHONY: test
test:
	tox

.PHONY: lint
lint:
	tox -e lint

.PHONY: docs
docs:
	- [ -z "`.venv/bin/pip list | grep -i 'sphinx '`" ] && .venv/bin/pip install sphinx
	- [ -z "`.venv/bin/pip list | grep -i sphinx-pypi-upload`" ] && .venv/bin/pip install sphinx-pypi-upload
	# If sphinx is installed on the system, pip installing into the venv does not
	# put the binaries into .venv/bin. Test for and use the .venv binary if it's
	# there; otherwise, we probably have a system sphinx in /usr/bin, so use that.
	SPHINX=$$(test -x .venv/bin/sphinx-build && echo \"../.venv/bin/sphinx-build\" || echo \"../.venv/bin/python /usr/bin/sphinx-build\"); \
	    cd docs && make html SPHINXBUILD=$$SPHINX && cd -

.PHONY: release
release: test docs
	scripts/update-revno
	.tox/py27/bin/python setup.py register sdist upload upload_docs
