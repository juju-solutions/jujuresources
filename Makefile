PROJECT=jujuresources
SUITE=unstable
VERSION=$(shell cat VERSION)

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
docs: test
	# If sphinx is installed on the system, pip installing into the venv may not
	# always put the binaries into the right place. Test for and use the venv
	# binary if it's there; otherwise, we probably have a system sphinx in
	# /usr/bin, so use that. (This may no longer be needed with move to tox)
	SPHINX=$$(test -x .tox/docs/bin/sphinx-build && echo \"../.tox/docs/bin/sphinx-build\" || echo \"../.tox/py27/bin/python /usr/bin/sphinx-build\"); \
	    cd docs && make html SPHINXBUILD=$$SPHINX && cd -

.PHONY: docrelease
docrelease: test docs
	.tox/docs/bin/python setup.py register upload_docs

.PHONY: release
release: test docs
	scripts/update-revno
	git tag release-${VERSION}
	git push --tags
	.tox/docs/bin/python setup.py register sdist upload upload_docs
