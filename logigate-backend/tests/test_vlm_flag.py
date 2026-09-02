from vlm_flag import vlm_enabled


def test_vlm_enabled_defaults_to_true_when_unset(monkeypatch):
    monkeypatch.delenv("VLM_ENABLED", raising=False)

    assert vlm_enabled() is True


def test_vlm_enabled_false_when_env_set_to_false(monkeypatch):
    monkeypatch.setenv("VLM_ENABLED", "false")

    assert vlm_enabled() is False


def test_vlm_enabled_case_insensitive(monkeypatch):
    monkeypatch.setenv("VLM_ENABLED", "FALSE")

    assert vlm_enabled() is False


def test_vlm_enabled_true_when_env_set_to_true(monkeypatch):
    monkeypatch.setenv("VLM_ENABLED", "true")

    assert vlm_enabled() is True
