import shutil, datetime, os
src = r'c:\Users\fabri\cofluhab\cofluhab\db.sqlite3'
if os.path.exists(src):
    dst = f"{src}.bak-{datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    shutil.copy2(src, dst)
    print('backup-created', dst)
else:
    print('no-db-file', src)
