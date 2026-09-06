from steam_linux_check.compatibility import evaluate_compatibility
from steam_linux_check.models import (
    AntiCheatInfo,
    CompatibilityStatus,
    OwnedGame,
    ProtonDBInfo,
    SteamDeckInfo,
    SteamStoreInfo,
)


def make_game() -> OwnedGame:
    return OwnedGame(
        app_id=123,
        name="Test Game",
    )


def test_native_linux_build_is_native() -> None:
    game = make_game()

    store_info = SteamStoreInfo(
        app_id=123,
        name="Test Game",
        app_type="game",
        windows=True,
        mac=False,
        linux=True,
    )

    result = evaluate_compatibility(
        game=game,
        store_info=store_info,
        proton_info=None,
        anticheat_info=None,
        deck_info=None,
    )

    assert result.status == CompatibilityStatus.NATIVE


def test_protondb_gold_is_works() -> None:
    game = make_game()

    proton_info = ProtonDBInfo(
        app_id=123,
        tier="gold",
        confidence="strong",
        total_reports=100,
        best_reported_tier="platinum",
        trending_tier="gold",
    )

    result = evaluate_compatibility(
        game=game,
        store_info=None,
        proton_info=proton_info,
        anticheat_info=None,
        deck_info=None,
    )

    assert result.status == CompatibilityStatus.WORKS


def test_protondb_silver_is_partial() -> None:
    game = make_game()

    proton_info = ProtonDBInfo(
        app_id=123,
        tier="silver",
        confidence="strong",
        total_reports=50,
        best_reported_tier="gold",
        trending_tier="silver",
    )

    result = evaluate_compatibility(
        game=game,
        store_info=None,
        proton_info=proton_info,
        anticheat_info=None,
        deck_info=None,
    )

    assert result.status == CompatibilityStatus.PARTIAL


def test_strong_trending_borked_is_broken() -> None:
    game = make_game()

    proton_info = ProtonDBInfo(
        app_id=123,
        tier="bronze",
        confidence="strong",
        total_reports=200,
        best_reported_tier="platinum",
        trending_tier="borked",
    )

    result = evaluate_compatibility(
        game=game,
        store_info=None,
        proton_info=proton_info,
        anticheat_info=None,
        deck_info=None,
    )

    assert result.status == CompatibilityStatus.BROKEN


def test_anticheat_denied_overrides_protondb_gold() -> None:
    game = make_game()

    proton_info = ProtonDBInfo(
        app_id=123,
        tier="gold",
        confidence="strong",
        total_reports=100,
        best_reported_tier="platinum",
        trending_tier="gold",
    )

    anticheat_info = AntiCheatInfo(
        app_id=123,
        name="Test Game",
        status="Denied",
        anticheats=["BattlEye"],
    )

    result = evaluate_compatibility(
        game=game,
        store_info=None,
        proton_info=proton_info,
        anticheat_info=anticheat_info,
        deck_info=None,
    )

    assert result.status == CompatibilityStatus.BROKEN


def test_steamos_playable_is_partial_without_protondb() -> None:
    game = make_game()

    deck_info = SteamDeckInfo(
        app_id=123,
        deck_category=1,
        steamos_category=2,
    )

    result = evaluate_compatibility(
        game=game,
        store_info=None,
        proton_info=None,
        anticheat_info=None,
        deck_info=deck_info,
    )

    assert result.status == CompatibilityStatus.PARTIAL


def test_no_compatibility_data_is_unknown() -> None:
    game = make_game()

    result = evaluate_compatibility(
        game=game,
        store_info=None,
        proton_info=None,
        anticheat_info=None,
        deck_info=None,
    )

    assert result.status == CompatibilityStatus.UNKNOWN

def test_steamos_unsupported_does_not_override_protondb_gold() -> None:
    game = make_game()

    proton_info = ProtonDBInfo(
        app_id=123,
        tier="gold",
        confidence="strong",
        total_reports=100,
        best_reported_tier="platinum",
        trending_tier="gold",
    )

    deck_info = SteamDeckInfo(
        app_id=123,
        deck_category=1,
        steamos_category=1,
    )

    result = evaluate_compatibility(
        game=game,
        store_info=None,
        proton_info=proton_info,
        anticheat_info=None,
        deck_info=deck_info,
    )

    assert result.status == CompatibilityStatus.WORKS


def test_anticheat_denied_overrides_native_linux_build() -> None:
    game = make_game()

    store_info = SteamStoreInfo(
        app_id=123,
        name="Test Game",
        app_type="game",
        windows=True,
        mac=False,
        linux=True,
    )

    anticheat_info = AntiCheatInfo(
        app_id=123,
        name="Test Game",
        status="Denied",
        anticheats=["BattlEye"],
    )

    result = evaluate_compatibility(
        game=game,
        store_info=store_info,
        proton_info=None,
        anticheat_info=anticheat_info,
        deck_info=None,
    )

    assert result.status == CompatibilityStatus.BROKEN


def test_weak_trending_borked_does_not_override_bronze() -> None:
    game = make_game()

    proton_info = ProtonDBInfo(
        app_id=123,
        tier="bronze",
        confidence="low",
        total_reports=5,
        best_reported_tier="gold",
        trending_tier="borked",
    )

    result = evaluate_compatibility(
        game=game,
        store_info=None,
        proton_info=proton_info,
        anticheat_info=None,
        deck_info=None,
    )

    assert result.status == CompatibilityStatus.PARTIAL