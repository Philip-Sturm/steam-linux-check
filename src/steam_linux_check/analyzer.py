from .compatibility import evaluate_compatibility
from .models import (
    AntiCheatInfo,
    CompatibilityResult,
    GameReportEntry,
    OwnedGame,
    ProtonDBInfo,
    SteamDeckInfo,
    SteamStoreInfo,
)
from .providers.steam_deck import category_name


def build_report_entries(
    owned_games: list[OwnedGame],
    store_info_by_app: dict[int, SteamStoreInfo],
    proton_info_by_app: dict[int, ProtonDBInfo],
    anticheat_by_app_id: dict[int, AntiCheatInfo],
    deck_info_by_app: dict[int, SteamDeckInfo],
    installed_app_ids: set[int],
) -> tuple[list[CompatibilityResult], list[GameReportEntry]]:
    """Evaluate all games and build their report entries."""

    compatibility_results: list[CompatibilityResult] = []
    report_entries: list[GameReportEntry] = []

    for game in owned_games:
        store_info = store_info_by_app.get(game.app_id)
        proton_info = proton_info_by_app.get(game.app_id)
        anticheat_info = anticheat_by_app_id.get(game.app_id)
        deck_info = deck_info_by_app.get(game.app_id)

        result = evaluate_compatibility(
            game=game,
            store_info=store_info,
            proton_info=proton_info,
            anticheat_info=anticheat_info,
            deck_info=deck_info,
        )

        compatibility_results.append(result)

        report_entries.append(
            GameReportEntry(
                app_id=game.app_id,
                name=game.name,
                status=result.status.value,
                reason=result.reason,
                native_linux=(
                    store_info.linux
                    if store_info is not None
                    else False
                ),
                protondb_tier=(
                    proton_info.tier
                    if proton_info is not None
                    else None
                ),
                protondb_confidence=(
                    proton_info.confidence
                    if proton_info is not None
                    else None
                ),
                protondb_reports=(
                    proton_info.total_reports
                    if proton_info is not None
                    else None
                ),
                protondb_trending=(
                    proton_info.trending_tier
                    if proton_info is not None
                    else None
                ),
                steamos_status=(
                    category_name(deck_info.steamos_category)
                    if deck_info is not None
                    else None
                ),
                anticheat_status=(
                    anticheat_info.status
                    if anticheat_info is not None
                    else None
                ),
                anticheats=(
                    list(anticheat_info.anticheats)
                    if anticheat_info is not None
                    else []
                ),
                installed=game.app_id in installed_app_ids,
            )
        )

    return compatibility_results, report_entries