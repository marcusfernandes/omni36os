# Omni36OS release notes

## 1.17.1 (06/11/2026)

- Clones: the R36Max hung before the first-boot setup. The image no longer runs the CPU/GPU/memory boost or the welcome screen early in boot, and writes /boot/omni36os-diag.txt (boot diagnostics) during the first 3 minutes.

## 1.17.0 (06/11/2026)

- R36Max and other clones (720x720): new image built from dArkOS4Clone (imagem/gerar-imagem-clone.sh), with emulators. The 640x480 menu and screens are centered on the device screen.
- Clones: Change DTB, overclock and USB drive mode are unavailable (they edited the R36S DTB); the first-boot screen test does not run.

## 1.16.1 (06/11/2026)

- Emulators: the missing RetroArch warning now checks the actual program (/opt/retroarch), not just the shortcut kept by the ports-only image.

## 1.16.0 (06/11/2026)

- Emulators (optional): Tools > Emulators shows in the library, after the ports, the RetroArch systems with games on the card. X and Y switch systems; the Ports card warns about missing BIOS.
- Image with emulators: sudo EMULADORES=1 imagem/gerar-imagem.sh builds Omni36OS-<version>-emu.img.xz, with RetroArch and the option already on. The default image stays ports-only.

## 1.15.31 (06/11/2026)

- Status bar: anchor icon while the internet comes through USB phone tethering.

## 1.15.30 (06/11/2026)

- USB tethering: more Android phones recognized, with the new Phone tethering option in the Network card.

## 1.15.29 (05/11/2026)

- What's new before updating: the screen now follows the console language.
- Runtimes: fixed the download error when space runs out or the file does not match.

## 1.15.28 (04/11/2026)

- Full English translation: messages, battery warnings, tool dialogs, port test reports and USB drive mode follow the chosen language.
- First boot asks for the language before the player name. Reset the system asks again.
- In English, error messages no longer appear as success.

## 1.15.27 (02/11/2026)

- Wi-Fi: the adapter is no longer powered off after 10 minutes without a network (the base Wi-Fi monitor disabled the radio and removed the driver, preventing Wi-Fi from reconnecting automatically).
- Ports copied on a PC with the card in a reader now appear in the library without using Refresh Ports.
- One-time system cleanup, with an on-screen menu: removes services, packages, documentation, and languages not used by a ports-only system (frees about 700 MB more).
- Credits: special thanks to h1ghland3r for testing the project and reporting bugs. Credit links are navigable: ↑↓ move focus and A opens the QR code (mpjsilva's GitHub and h1ghland3r's links).

## 1.15.26 (01/11/2026)

- Tools > Change DTB: change the console screen without a PC. A red warning includes a 10-second hold; the console restarts in ‘DTB search mode’ and tests screens one by one. L1 + R1 at startup still works.
- The dArkOSen DTB catalog is included with Omni36OS and updates automatically; the clone-console warning is now based on the model and no longer appears unnecessarily.
- Cards: Eject Card 2 and Mount Card 2 let you remove and insert the card without shutting down. Removing it without ejecting shows a red warning (also when returning from a game).
- When Card 2 is absent, ROMS2 is hidden everywhere: Game Source, Files, Images, runtimes, and Help. The Cards page refreshes automatically when the card is inserted or removed.
- Ports opens with the most recently played port selected.
- Test Ports: View Reports (opens in Notes) and Missing Runtimes (searches ports and downloads over Wi-Fi). Reports now flag incomplete copies (zero-byte files) and missing runtimes.
- Test Ports also closes processes a port leaves running separately (such as Cuphead); previously the game remained behind the menu and the screen flickered.
- FN shortcuts now detect ports that run separately (Cuphead, Blasphemous). For ports that do not support the FPS counter, limit, or screenshot, a warning appears once per play session.
- SCREENSHOT SAVED appears at the bottom center, no longer underneath the resource monitor. FN + Y in the menu works again with the File Browser enabled.
- USB drive mode shows when the PC is copying to or from the console, and B no longer interrupts a copy in progress.

## 1.15.25 (31/10/2026)

- Apps now includes Images: screenshots (FN + Y) from the menu and each game, newest first. Left/right changes images; X deletes.
- System logs are collected in one folder on Card 1: logs/<function> (system, ports, USB drive, display, network). Test Ports reports are saved to logs/port test/port_test_<port name>.txt. Older reports were moved there.
- Notes can read logs: System Logs opens each log read-only at the end (the newest entries).
- Tools > Refresh Ports rereads the port list, covers, and descriptions when a copied port does not appear.
- Wi-Fi: an adapter plugged in while the console is on and stuck in disk mode is now re-enabled automatically.
- USB drive mode respects the ROMS2 selection (previously it fell back to ROMS at startup), and ‘Partition on PC’ only appears when Card 2 is present.

## 1.15.24 (31/10/2026)

- Port covers and descriptions can be supplied in the infos folder inside ports, using the game name: for abismo.sh, use abismo.txt (description) and abismo.png, .jpg, or .webp (cover). An optional abismo.json can provide the name, studio, year, and genres.
- R36XX: USB drive mode warns that built-in Wi-Fi shares the OTG port, so the PC may not detect the console; the USB-drive log records the model.
- Credits and text now identify only dArkOSen as the base; File Browser is presented as Omni36OS.

## 1.15.23 (31/10/2026)

- USB drive mode lasts for one boot: ejecting it on the PC, unplugging the cable, or pressing B returns the console to normal mode and restarts it with Wi-Fi. Any restart during this mode also returns to normal.
- USB drive mode logs USB-port status while waiting for the PC (/home/ark/usb-disco.log), helping diagnose why the PC does not show the drive.

## 1.15.22 (31/10/2026)

- For a card moved to another console or a different screen: when ‘Loading’ appears at startup, hold L1 + R1 until you hear an arpeggio. The test screen replaces it and Omni36OS detects the screen again without a PC.

## 1.15.21 (31/10/2026)

- The default A, B, X, and Y button mapping applies only to new images on first boot. Updating no longer changes the selection made in Controls > Swap Buttons.

## 1.15.20 (31/10/2026)

- Buttons now behave as labeled by default (dArkOSen previously swapped A and B). Swap them in Controls > Swap Buttons if you prefer.
- Apps now includes GeForce NOW (cloud gaming) and Moonlight (stream games from your PC over your home network). Each has Install/Update; GeForce NOW lets you choose whether FN belongs to the system or to the app.
- The power menu opens immediately during a game. Left/right adjusts the counter, 30 FPS limit, and mouse mode without closing the menu. New: Type Text using the Omni36OS keyboard.
- Mouse mode (FN + R3 or the power menu): the right stick moves, A or R3 clicks, B is right-click, and the left stick scrolls.
- Carousel counter on FN + X: FPS; CPU; GPU; RAM used; hide.
- Power now freezes separately running ports correctly (such as Gran Turismo); the menu no longer flickers.
- When FPS cannot be read, CPU and GPU in Automatic mode stay at maximum without overclocking.
- PortMaster runtimes are included in the image and update automatically when Wi-Fi connects.
- Battery Calibration now uses one button that toggles between Start and Stop.
- New ports appear in the list without reopening Omni36OS.

## 1.15.19 (31/10/2026)

- CPU and GPU in Automatic mode (Performance): in games they start at minimum and rise one step at a time only until the game reaches 60 FPS (or 30 with the FN + B limit). GPU load decides which rises first. Maximum is 1296/520 MHz, or unrestricted with overclock unlocked. New images include this setting.
- The FPS counter now also works in 32-bit games (Asphalt and others), along with screenshots and the FPS limit.
- FN + X cycles through: FPS; FPS with CPU and GPU frequencies in the same pill; then hidden.
- While FN is held, the shortcut key (FN + X, B, Y) is no longer sent to the game. Omni36OS system shortcuts using FN continue to work.
- Backup is now a snapshot: it saves the Omni36OS version, all settings, Wi-Fi networks, console name, SSH keys, sound, and brightness. Restoring returns the console exactly to the backup state and asks you to restart.

## 1.15.18 (31/10/2026)

- Missing PortMaster runtimes are downloaded before launching a port (they are no longer copied from Card 2). Without internet, copy the file from a PC to tools/PortMaster/libs on the system card.
- Port-test results now keep long text, such as the report path, inside the box.

## 1.15.17 (31/10/2026)

- Ports now fetch missing requirements: before launch, Omni36OS finds the PortMaster runtimes a game uses (Mono, Godot, Java, etc.) and copies them from Card 2 or downloads them, with a progress bar. This fixes games such as TMNT that requested Mono even when it was already on the card.
- Card 2 games: folder changes made while a game runs are always undone when it closes, even if part of the game remains running. Previously, Card 1 ports could disappear from the list and Card 2 ports could appear twice.

## 1.15.16 (30/10/2026)

- Port library: A now launches the game directly. The second screen (details with Play and Back) was removed because the list already shows the cover and description.

## 1.15.15 (30/10/2026)

- Low-battery warnings now also appear over system tools: the tool pauses, the warning appears, and after OK (or connecting the charger) it continues where it left off.

## 1.15.14 (30/10/2026)

- The low-battery warning now disappears automatically when the charger is connected, and ‘Charging’ is shown.
- LED: while charging, low battery no longer makes the LED blink (for both new cards and new images).

## 1.15.13 (30/10/2026)

- Cover and description searches now work on networks whose router does not answer IPv6 queries: Omni36OS resolves names using IPv4 only (previously each site took about 6 seconds just to resolve, causing the search to time out).

## 1.15.12 (30/10/2026)

- Status pill: Wi-Fi is shown as connected only when there is a real network connection and IP address (the Realtek adapter reported ‘on’ even with no network).
- A Realtek Wi-Fi adapter stuck in ‘disk’ mode after boot (sometimes the switch to Wi-Fi mode is lost) is now detected and re-enabled automatically by Omni36OS.

## 1.15.11 (30/10/2026)

- Card 2 ports now launch even without the game folder on Card 1: while one is running, /roms/ports points to the Card 2 ports folder (PortMaster scripts look for the game there).

## 1.15.10 (30/10/2026)

- Port list: each game now shows which card it is on (SD-card icon with number 1 or 2), and game details say ‘Card 1’ or ‘Card 2’.

## 1.15.9 (30/10/2026)

- Safer screen selection on first boot: each test changes only the screen entry in the console’s original DTB. boot.ini, u-boot, and other hardware settings are never replaced, so the wrong screen can blank the display but cannot prevent booting.
- Faster screen selection: each screen is tested for 10 seconds and the process starts earlier in boot. Worst case with 12 screens dropped from about 8 to about 5 minutes.
- During screen search, the LED flashes red and green. The prompt plays a ding-dong through the speaker and confirmation plays an arpeggio.

## 1.15.8 (30/10/2026)

- Short pages (What's New, Help) no longer show scrolling buttons when there is nothing to scroll.

## 1.15.7 (30/10/2026)

- Check for Update now shows the new version’s release notes before installation (What's New button), fetched from GitHub.
- Update and Revert to Previous Version now open with ‘Not now’ or ‘Cancel’ selected, preventing accidental installation with one extra press.

## 1.15.6 (30/10/2026)

- USB Network: the page shows which mode is enabled (‘Universal mode: on’) and when networking is off.
- USB network compatibility: the DHCP client is shown on one line; missing dhcpcd is no longer a problem (only one client is needed).

## 1.15.5 (30/10/2026)

- USB Network and USB drive mode now switch automatically: enabling one disables the other, with no manual warning (leaving USB drive mode restarts once and USB networking turns on automatically afterward).
- Scan for Networks turns Wi-Fi on if it is off. Without a Wi-Fi adapter, the Network card mentions this without an alert.
- Status pill: the Wi-Fi icon shows signal strength, dims when disconnected, is crossed out when the radio is off, and updates on every screen.

## 1.15.4 (30/10/2026)

- Omni36OS is now open-source under the GNU GPL v3.0 license.

## 1.15.3 (30/10/2026)

- Complete credits are available under General > About: base system, PortMaster, gptokeyb, ogage, File Browser, BatteryPlus, SDL2, FFmpeg, fonts, icons, data sources, and the R36S community, with links.

## 1.15.2 (30/10/2026)

- Shutdown and restart now show the goodbye screen directly, without briefly flashing the menu or welcome screen first.

## 1.15.1 (30/10/2026)

- Keyboard: X inserts a space and Y switches between letters and symbols. Caps lock is toggled on the on-screen key with a double press. This applies throughout the system.

## 1.15.0 (30/10/2026)

- Notes: opening a note shows the whole text for reading with scrolling. A edits the full note like a typewriter: text scrolls as lines fill, the keyboard includes Enter, L1/R1 move the cursor between lines, and START saves.

## 1.14.2 (30/10/2026)

- Videos and Notes lists are full-screen like Music, with the status pill (Wi-Fi, volume, battery, temperature, and time). Video playback remains full-screen. Deleting a note asks for confirmation, with Cancel selected by default.

## 1.14.1 (30/10/2026)

- The release manual was revised with a new introduction, EASYROMS paths for video and note folders, Cards in Check Everything, SDL2 and FFmpeg credits, and no mention of RetroArch, which is no longer included.

## 1.14.0 (30/10/2026)

- The new keyboard is consistent throughout the system and Android-like: it starts uppercase and returns to lowercase after the first letter (and uppercase again after a period); double-tapping Shift locks it, Y locks it directly, and X switches letters and symbols. Passwords start lowercase.

## 1.13.0 (30/10/2026)

- Apps now includes Videos (a simple player using FFmpeg’s open codecs) and Notes (a text editor with keyboard and punctuation).
- In Files, music, videos, and text files open directly in the appropriate app.

## 1.12.7 (30/10/2026)

- The Storage card is now called Cards, with a font size matching the other cards and labels for USB drive, space, and repair.

## 1.12.6 (30/10/2026)

- The Display & Sound card title is restored (it had been clipped); the subtitle still mentions brightness, sound, and battery.

## 1.12.5 (30/10/2026)

- Apps now shows only the app list; Music options (visualization, screen-off, and subfolders) are inside the app under START.

## 1.12.4 (30/10/2026)

- Music: the status pill (Wi-Fi, volume, battery, temperature, and time) now appears in the player; visualization names use the system hint, and FN screenshot capture wakes the screen first if it is off.

## 1.12.3 (30/10/2026)

- Music now turns the screen back on automatically if the launcher restarts while the display is off.

## 1.12.2 (30/10/2026)

- Music now has an Album Cover visualization, using folder art or artwork embedded in the MP3. The cover also appears in the now-playing bar.

## 1.12.1 (30/10/2026)

- Password-protected Samba now allows only the omni user, and the network exposes only Card 1 and Card 2.

## 1.12.0 (30/10/2026)

- New Apps card: Music plays MP3s from the cards’ music folders, including subfolders, with visualizations (Bars, Waves, Ring, and Aurora) and automatic screen-off during playback.
- Battery information now appears under Display & Sound. Ports is centered and highlighted whenever the menu opens.
- Each card now describes its three functions.

## 1.11.11 (30/10/2026)

- Shortened the Swap Buttons text.

## 1.11.10 (30/10/2026)

- Revised overclock-unlock text and button help.

## 1.11.9 (30/10/2026)

- When the password lock is enabled, unlocking overclock now requires the console password.

## 1.11.8 (30/10/2026)

- Overclock locking is now enforced: CPU speeds above 1296 MHz and GPU speeds above 520 MHz appear only after Performance > Unlock Overclock. Lock Overclock restores defaults.

## 1.11.7 (30/10/2026)

- Tools > Automatic Search now turns cover and description searches on or off.
- The library now says whether it is searching for an image and description, only a description, or only an image. Missing results are not searched again, and searches do not run while a game is open.

## 1.11.6 (30/10/2026)

- Cover and description searches now run only when Wi-Fi is connected.

## 1.11.5 (30/10/2026)

- The library now shows ‘Searching for description…’ and ‘Description not found’ instead of metadata text.

## 1.11.4 (30/10/2026)

- Wikipedia descriptions are now in Portuguese and include release years for ports without PortMaster or Steam information.

## 1.11.3 (30/10/2026)

- When PortMaster and Steam have no covers or descriptions, Omni36OS now searches DuckDuckGo.

## 1.11.2 (30/10/2026)

- The ports-only library now reads only ports folders on the cards. Emulator folders are excluded, and scanning is nearly instantaneous.

## 1.11.1 (30/10/2026)

- Controls now has one option, Swap Buttons (On/Off), which swaps A/B and X/Y together.

## 1.11.0 (30/10/2026)

- Faster boot with no black screen: everything runs at maximum until the menu is ready (about 3 seconds faster), then switches to minimum. The logo and welcome screen continue directly into Omni36OS.
- USB Wi-Fi starts automatically at boot; date, time, and time zone are set when internet becomes available, and volume stays at your chosen level.
- Display & Sound has its own brightness, contrast, and volume panel. A/B and X/Y swapping is in Controls.
- FN + Y captures the menu screen to the Images folder. Files displays images full-screen.
- Card 2 appears automatically. Power always opens the power menu; FN + Power shuts down after saving everything.
- SSH and browser access use omni/omni. Remote services are enabled only when network is available.
- Visual updates: custom icons, higher-contrast text, button-art hints, and pixel-aligned layout. The Network card no longer shows an alert after Wi-Fi connects.
