import os
import sys

# Ensure correct path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cofluhab.settings')

# Now run the mapper script
exec(open('scripts/link_contrato_mutuario_v2.py', encoding='utf-8').read())
