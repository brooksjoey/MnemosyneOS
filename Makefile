Makefile
.PHONY: venv serve worker beat migrate test fmt seed bench enable-services start stop logs

venv:
	./scripts/venv.sh

serve:
	venv/bin/gunicorn --factory -w `python -c 'import os,psutil; print(max(2, os.cpu_count()//2))'` \
		-k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 src.main:create_app

worker:
	venv/bin/celery -A src.jobs.celery_app:app worker --loglevel=INFO --concurrency=4 -Q ingest,reflect,compress,rebuild

beat:
	venv/bin/celery -A src.jobs.celery_app:app beat --loglevel=INFO

migrate:
	venv/bin/alembic upgrade head

test:
	venv/bin/pytest -q

seed:
	venv/bin/python scripts/load_seed.py

bench:
	venv/bin/python scripts/bench.py

enable-services:
	sudo ./scripts/install_systemd.sh

start:
	sudo systemctl start mnemosyneos mnemo-worker mnemo-beat

stop:
	sudo systemctl stop mnemosyneos mnemo-worker mnemo-beat

logs:
	sudo journalctl -u mnemosyneos -u mnemo-worker -u mnemo-beat -f