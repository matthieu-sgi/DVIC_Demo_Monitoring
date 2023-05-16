echo "Packaging DVIC Demo watcher node client"

rm -fr .venv
python -m venv .venv
./.venv/bin/python3 -m pip install -r requirements.txt

tar -czvf DVIC_DemoWatcher_latest.tar.gz .venv client main.py