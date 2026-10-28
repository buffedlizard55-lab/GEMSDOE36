"""Compatibility publisher: delegate to the current fail-closed review."""
from publish_current_review import main, publish

__all__ = ["publish"]


if __name__ == "__main__":
    raise SystemExit(main())
