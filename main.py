import subprocess

# Exports the notebook as WASM to use locally or upload to GitHub Pages
subprocess.run(
    ["marimo", "export", "html-wasm", "tools.py", "-o", "tools", "--mode", "run"]
)
