# Steam Linux Compatibility Checker

A local Linux compatibility checker for your Steam library.

The application reads the locally detected Steam installation, loads the
owned Steam library through the Steam Web API and combines information from
multiple compatibility sources to estimate how well each game should work
on Linux.

The result is exported as JSON, CSV and an interactive HTML dashboard.

## Features

- Automatically detects the local Steam installation
- Detects configured Steam library folders
- Detects locally installed Steam apps
- Loads the owned Steam library through the Steam Web API
- Checks native Linux support
- Uses ProtonDB compatibility information
- Uses SteamOS / Steam Deck compatibility information
- Uses AreWeAntiCheatYet anti-cheat information
- Combines the available information into one compatibility status
- Tracks changes between successful runs
- Generates JSON, CSV and HTML reports
- Provides search and filtering in the HTML report
- Uses local caching to reduce requests
- Falls back to stale cache data during temporary provider outages
- Detects incomplete provider runs and protects the previous comparison state

Version 1 is read-only with regard to Steam.

The application does not modify Steam libraries, Steam collections or game
files.

## Compatibility Status

Each Steam game receives one of five statuses:

### Native

The Steam Store reports an official native Linux build.

### Works

The available compatibility data indicates that the game should generally
work well on Linux.

Typical examples include strong ProtonDB Gold or Platinum ratings.

### Partial

The game is expected to work, but limitations, configuration changes or
other issues may exist.

Typical examples include ProtonDB Silver or Bronze ratings or a SteamOS
Playable fallback.

### Broken

The available information indicates that the game is currently not expected
to work reliably.

Examples include:

- ProtonDB Borked
- strong ProtonDB trending rating of Borked
- incompatible or denied anti-cheat support

### Unknown

There is not enough compatibility information available to make a useful
classification.

## Data Sources

The checker currently combines information from:

- Steam Web API
- Steam Store
- ProtonDB
- Steam Deck / SteamOS compatibility data
- AreWeAntiCheatYet

Some of these interfaces are unofficial and may change in the future.

The provider implementations are intentionally separated from the
compatibility engine so that individual data sources can be replaced without
rewriting the complete application.

## Compatibility Evaluation

The current evaluation priority is approximately:

1. Broken or denied anti-cheat support -> Broken
2. Official native Linux version -> Native
3. ProtonDB Borked -> Broken
4. Strong ProtonDB trending Borked -> Broken
5. ProtonDB Gold or Platinum -> Works
6. ProtonDB Silver or Bronze -> Partial
7. SteamOS Verified -> Works
8. SteamOS Playable -> Partial
9. Insufficient data -> Unknown

SteamOS Unsupported alone does not automatically mark a game as Broken.

Steam Deck compatibility and desktop Linux compatibility are not identical,
so positive SteamOS information is primarily used as a fallback.

## Requirements

- Linux
- Python 3.14 or newer
- Steam installed locally
- Steam account with a Steam Web API key
- Internet connection for refreshing compatibility data

The project is currently developed and tested primarily on Fedora Linux with
KDE Plasma.

## Installation

Clone the repository and enter the project directory:

```bash
git clone <repository-url>
cd steam-linux-check