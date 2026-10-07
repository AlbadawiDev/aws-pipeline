"""Run the CSV transform locally; no AWS client, account or credentials are used."""
import importlib.util
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pipeline', root / 'lambda' / 'app.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)
output, rows = pipeline.normalize_csv((root / 'sample' / 'ventas.csv').read_bytes())
target = root / '.demo' / 'ventas-utf8.csv'
target.parent.mkdir(exist_ok=True)
target.write_bytes(output)
print(f'Transformación local: {rows} filas. Salida: {target}')
