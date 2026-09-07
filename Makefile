.PHONY: render validate smoke
render:
	python3 scripts/render.py
validate:
	python3 scripts/install-tools.py
	python3 scripts/validate.py
smoke:
	python3 scripts/smoke.py
