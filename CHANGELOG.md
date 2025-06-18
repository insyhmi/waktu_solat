# Changelog.md
All notable changes to project Waktu Solat will be documented in this file.
## 1.0 - 2025-06-05
Project Waktu Solat is created
### Added
- The main script itself, ```waktu_solat.py``` and its peripheral files.

## 1.1 - 2025-06-06
### Added
- Tarikh Masa label now has a functional, ticking clock sourced from the system.
- Added <b>Menu</b> action as a placeholder for future implementation.
- Added ```CHANGELOG.md```
### Changed
- The default time zone has changed to ```JHR01``` Johor.
- Upcoming Subuh time will properly show its time of the following day during Isyak time of the current day.
- Label ```Tarikh Masa``` and ```Waktu solat seterusnya``` is centered within its respective label

## 1.2 - 2025-06-15
### Added
- Folder `src` which saves source files and user settings.
- Settings window.
- Functionality to change the prayer time zone
- Warning dialogs and Critical dialogs on error events
### Changed
- Removed spaces in `README.md` dates in accordance to ISO 8601

## 1.3 - 2025-06-16
### Added 
- A description of places about the saved time zone on the main window
- Quit functionality on 'Quit' action button
### Changed
- Changed source files from ```.txt``` to ```.dat```
- Set the default window size to 960px x 540px
- Fixed critical message box not spawning properly on certain errors
- Fixed issue of saving prayer time zone for the first time 
### Removed
- Refresh action button 

## 1.4 - 2025-06-18
### Removed
- Qt status bar