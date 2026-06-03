def safe_json_loads(val, default=None):
    import json
    if not val:
        return default if default is not None else []
    try:
        return json.loads(val)
    except Exception:
        return default if default is not None else []
