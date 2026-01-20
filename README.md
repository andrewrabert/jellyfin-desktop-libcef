# jellyfin-desktop-libcef

Prebuilt CEF (Chromium Embedded Framework) for [jellyfin-desktop-cef](https://github.com/jellyfin/jellyfin-desktop-cef).

## Platforms

- Windows x64
- macOS arm64
- macOS x86_64

## Usage

1. Download the release for your platform from [Releases](../../releases)
2. Extract the archive
3. Build jellyfin-desktop-cef with:
   ```bash
   cmake -B build -DEXTERNAL_CEF_DIR=/path/to/extracted/libcef ...
   ```

## Building

Trigger the workflow manually from Actions tab. It will:
1. Download latest stable CEF from Spotify CDN
2. Build `libcef_dll_wrapper` for each platform
3. Create a GitHub Release with all artifacts
