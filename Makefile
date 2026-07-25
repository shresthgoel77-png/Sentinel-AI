.PHONY: run test

run:
	bash launch.sh

test:
	cd backend && venv/Scripts/python -m pytest tests/test_gateway.py -v
