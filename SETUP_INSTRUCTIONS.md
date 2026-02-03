# Setup Instructions for Python 3.8

## Important: Python 3.8 Compatibility Fix

This system requires a one-time fix for Python 3.8 compatibility with ChromaDB's posthog dependency.

### Run the Fix Script

**Before using the system, you MUST run:**

```bash
python fix_all_posthog.py
```

This will patch all posthog Python files to work with Python 3.8 by replacing Python 3.9+ type hints (`dict[str]`, `list[str]`, etc.) with Python 3.8 compatible versions (`Dict[str]`, `List[str]`, etc.).

**Note**: This fix only needs to be run once after installing dependencies. If you reinstall posthog or chromadb, you may need to run it again.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the compatibility fix (REQUIRED for Python 3.8):
```bash
python fix_all_posthog.py
```

3. Start the server:
```bash
python main.py
```

## What the Fix Does

The fix patches `posthog/types.py` to replace `dict[str, Type]` syntax (which doesn't work in Python 3.8) with `Dict[str, Type]` and ensures `Dict` is imported from `typing`.

## Alternative: Upgrade Python

If you prefer, you can upgrade to Python 3.9+ which natively supports the `dict[str, Type]` syntax and doesn't require this fix.
