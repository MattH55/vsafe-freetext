"""Tests run as if no OSF registration exists, whatever config/analysis.yaml says, so the
pre-registration guards stay tested. A test that needs the registered state patches
config.analysis itself."""

import pytest

from vsafe_ft import config


@pytest.fixture(autouse=True)
def _unregistered(monkeypatch):
    real = config.analysis()
    monkeypatch.setattr(config, "analysis", lambda: {**real, "osf_registration": None})
