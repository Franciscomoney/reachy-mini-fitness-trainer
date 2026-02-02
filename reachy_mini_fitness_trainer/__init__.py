"""Reachy Mini Fitness Trainer - AI-powered workout companion"""
__version__ = "1.0.0"


def __getattr__(name):
    """Lazy import to avoid loading reachy_mini when running standalone."""
    if name == "ReachyMiniFitnessTrainer":
        from .main import ReachyMiniFitnessTrainer
        return ReachyMiniFitnessTrainer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["ReachyMiniFitnessTrainer"]
