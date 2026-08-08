"""AdvisorSettingsStore: round trip, the honest-default-when-missing load,
and the fixed-width last-4 mask (M5 brief)."""

from __future__ import annotations

from sigma_engine.advisor.settings_store import AdvisorSettings, AdvisorSettingsStore, mask_api_key


def test_load_with_no_file_returns_honest_default(tmp_path):
    store = AdvisorSettingsStore(tmp_path)
    settings = store.load()
    assert settings.api_key is None
    assert settings.base_url is None
    assert settings.enabled is True


def test_save_then_load_round_trips(tmp_path):
    store = AdvisorSettingsStore(tmp_path)
    store.save(AdvisorSettings(api_key="sk-ant-abcdefgh1234", base_url="https://example.test", enabled=False))

    reloaded = AdvisorSettingsStore(tmp_path).load()
    assert reloaded.api_key == "sk-ant-abcdefgh1234"
    assert reloaded.base_url == "https://example.test"
    assert reloaded.enabled is False


def test_settings_file_is_a_sibling_of_projects_not_inside_one(tmp_path):
    # M5 brief: "stored in the project-store root ... NOT inside any
    # project" -- the file must land directly under the given root, never
    # under a project_id subdirectory.
    store = AdvisorSettingsStore(tmp_path)
    store.save(AdvisorSettings(api_key="sk-ant-xyz", enabled=True))
    assert (tmp_path / "settings.json").exists()
    assert not any(p.name == "settings.json" for p in tmp_path.glob("*/settings.json"))


def test_mask_api_key_shows_only_last_four_with_a_fixed_width_prefix():
    assert mask_api_key("sk-ant-api03-verylongkeyvalue9999") == "********9999"
    assert mask_api_key(None) is None
    assert mask_api_key("") is None


def test_mask_api_key_never_leaks_the_real_key_length():
    short = mask_api_key("ab12")
    long = mask_api_key("sk-ant-" + ("x" * 200) + "5678")
    # Same fixed prefix width regardless of the real key's length.
    assert short.startswith("*" * 8)
    assert long.startswith("*" * 8)
    assert short.endswith("ab12")
    assert long.endswith("5678")


def test_mask_api_key_short_key_does_not_crash():
    # Shorter than the unmasked suffix length -- still masked, never raises.
    assert mask_api_key("ab") == "********ab"
