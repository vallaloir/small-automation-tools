powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
CHCP 65001 > NUL
uv run https://vallaloir.github.io/small-automation-tools/apps/public/importació.py %1