from .models import (
    AntiCheatInfo,
    CompatibilityResult,
    CompatibilityStatus,
    OwnedGame,
    ProtonDBInfo,
    SteamDeckInfo,
    SteamStoreInfo,
)


def evaluate_compatibility(
    game: OwnedGame,
    store_info: SteamStoreInfo | None,
    proton_info: ProtonDBInfo | None,
    anticheat_info: AntiCheatInfo | None,
    deck_info: SteamDeckInfo | None,
) -> CompatibilityResult:
    """Evaluate Linux compatibility from available providers."""

    # Anti-Cheat blockers have highest priority.
    if anticheat_info is not None and anticheat_info.status in {"Broken", "Denied"}:
        return CompatibilityResult(
            app_id=game.app_id,
            name=game.name,
            status=CompatibilityStatus.BROKEN,
            reason=f"Anti-Cheat status: {anticheat_info.status}",
        )

    # Official Linux build.
    if store_info is not None and store_info.linux:
        return CompatibilityResult(
            app_id=game.app_id,
            name=game.name,
            status=CompatibilityStatus.NATIVE,
            reason="Official native Linux build",
        )

    # ProtonDB data has priority for Windows games.
    if proton_info is not None:
        if proton_info.tier == "borked":
            return CompatibilityResult(
                app_id=game.app_id,
                name=game.name,
                status=CompatibilityStatus.BROKEN,
                reason="ProtonDB rating: borked",
            )

        if (
            proton_info.trending_tier == "borked"
            and proton_info.confidence == "strong"
        ):
            return CompatibilityResult(
                app_id=game.app_id,
                name=game.name,
                status=CompatibilityStatus.BROKEN,
                reason="ProtonDB trending rating: borked",
            )

        if proton_info.tier in {"platinum", "gold"}:
            return CompatibilityResult(
                app_id=game.app_id,
                name=game.name,
                status=CompatibilityStatus.WORKS,
                reason=f"ProtonDB rating: {proton_info.tier}",
            )

        if proton_info.tier in {"silver", "bronze"}:
            return CompatibilityResult(
                app_id=game.app_id,
                name=game.name,
                status=CompatibilityStatus.PARTIAL,
                reason=f"ProtonDB rating: {proton_info.tier}",
            )

    # SteamOS is used as a fallback if ProtonDB has no useful data.
    if deck_info is not None:
        if deck_info.steamos_category == 3:
            return CompatibilityResult(
                app_id=game.app_id,
                name=game.name,
                status=CompatibilityStatus.WORKS,
                reason="SteamOS compatibility: verified",
            )

        if deck_info.steamos_category == 2:
            return CompatibilityResult(
                app_id=game.app_id,
                name=game.name,
                status=CompatibilityStatus.PARTIAL,
                reason="SteamOS compatibility: playable",
            )

    # SteamOS Unsupported alone does not mean that a Fedora desktop
    # cannot run the game.
    return CompatibilityResult(
        app_id=game.app_id,
        name=game.name,
        status=CompatibilityStatus.UNKNOWN,
        reason="Insufficient compatibility data",
    )