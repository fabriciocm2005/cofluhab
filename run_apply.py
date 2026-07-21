import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')

exec(open('scripts/apply_mapping_v2.py', encoding='utf-8').read())
