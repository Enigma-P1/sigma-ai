"""AdvisorSettingsStore: round trip, the honest-default-when-missing load,
and the fixed-width last-4 mask (M5 brief). M5 exit critic pass adds:
load() surviving a corrupt/truncated file instead of raising (severity 1),
the atomic write's fsync (severity 1), and mask_api_key's short-key
handling actually masking instead of leaking (bullet finding)."""

from __future__ import annotations

import json

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
    # M5 exit critic (bullet finding): a key at or below the unmasked-
    # suffix length used to come back as the fixed star prefix PLUS the
    # entire real key ("********ab12") -- looked masked, wasn't. A key
    # this short is masked completely instead; only a longer key gets the
    # "prefix + last 4" treatment.
    short = mask_api_key("ab12")
    long = mask_api_key("sk-ant-" + ("x" * 200) + "5678")
    assert short == "****"
    assert long.startswith("*" * 8)
    assert long.endswith("5678")
    assert "ab12" not in short


def test_mask_api_key_short_key_is_masked_completely_never_leaked():
    # Shorter than the unmasked suffix length -- masked completely, never raises.
    assert mask_api_key("ab") == "****"
    assert mask_api_key("a") == "****"


def test_mask_api_key_boundary_at_exactly_four_chars_is_fully_masked():
    # The boundary the bug lived on: length == _UNMASKED_SUFFIX_LEN (4).
    assert mask_api_key("abcd") == "****"
    # One character longer crosses into the normal "prefix + last 4" path.
    assert mask_api_key("xabcd") == "********abcd"


# ---- load() surviving a corrupt/truncated settings.json (M5 exit critic,
# severity 1) -- the exact scenario a crash mid-write or a hand-edit gone
# wrong produces, and previously 500'd every advisor route. ----


def test_load_survives_a_zero_length_file(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("", encoding="utf-8")
    settings = AdvisorSettingsStore(tmp_path).load()
    assert settings == AdvisorSettings()  # honest default, not a raise


def test_load_survives_truncated_json(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"schema_version": 1, "api_key": "sk-ant-abc', encoding="utf-8")  # cut off mid-write
    settings = AdvisorSettingsStore(tmp_path).load()
    assert settings == AdvisorSettings()


def test_load_survives_valid_json_that_fails_schema_validation(tmp_path):
    path = tmp_path / "settings.json"
    # Valid JSON, wrong shape: enabled must be a bool.
    path.write_text(json.dumps({"schema_version": 1, "api_key": None, "base_url": None, "enabled": "not-a-bool"}), encoding="utf-8")
    settings = AdvisorSettingsStore(tmp_path).load()
    assert settings == AdvisorSettings()


def test_load_survives_a_hand_edited_garbage_file(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("not json at all, someone typed over the file", encoding="utf-8")
    settings = AdvisorSettingsStore(tmp_path).load()
    assert settings == AdvisorSettings()
    assert settings.api_key is None
    assert settings.enabled is True


def test_a_corrupt_file_does_not_block_saving_a_fresh_one(tmp_path):
    # The honest-default read must not be sticky -- a save right after a
    # corrupt load has to actually take.
    path = tmp_path / "settings.json"
    path.write_text("{{{not json", encoding="utf-8")
    store = AdvisorSettingsStore(tmp_path)
    assert store.load() == AdvisorSettings()  # survives the corruption

    store.save(AdvisorSettings(api_key="sk-ant-recovered1234", enabled=True))
    reloaded = AdvisorSettingsStore(tmp_path).load()
    assert reloaded.api_key == "sk-ant-recovered1234"


# ---- _atomic_write_json's fsync (M5 exit critic, severity 1) --
# existence-level smoke only: fsync is a real syscall here, never mocked,
# so this just proves the write path still produces a real, complete,
# reloadable file with fsync unconditionally in the way. ----


def test_save_round_trips_through_the_real_fsyncing_write_path(tmp_path):
    store = AdvisorSettingsStore(tmp_path)
    store.save(AdvisorSettings(api_key="sk-ant-fsync-check-9999", base_url="https://fsync.example.test", enabled=True))

    path = tmp_path / "settings.json"
    assert path.exists()
    assert path.stat().st_size > 0  # never the zero-length file a missing fsync could publish
    # No leftover temp file from the write (the rename completed cleanly).
    assert list(tmp_path.glob(".settings.json.*.tmp")) == []

    reloaded = AdvisorSettingsStore(tmp_path).load()
    assert reloaded.api_key == "sk-ant-fsync-check-9999"
    assert reloaded.base_url == "https://fsync.example.test"
