# theme-switcher Specification

## Purpose
TBD - created by archiving change frontend-ui-optimization. Update Purpose after archive.
## Requirements
### Requirement: Theme Toggle Button
The system SHALL provide a visible UI control for switching between light and dark themes.

- **Location**: Sidebar bottom area, near user info / logout
- **Icon**: Sun icon (light mode) / Moon icon (dark mode), indicating the *other* mode
- **Behavior**: Click toggles between light and dark
- **Tooltip**: "切换深色模式" / "切换浅色模式"

#### Scenario: Theme toggle is visible on sidebar
- **WHEN** the application layout renders
- **THEN** a theme toggle button SHALL be displayed in the sidebar

#### Scenario: Clicking toggle switches theme
- **WHEN** user clicks the theme toggle
- **THEN** the theme SHALL switch to the opposite mode with a visual transition

#### Scenario: Toggle icon reflects current theme
- **WHEN** in light mode
- **THEN** the toggle SHALL show a moon icon (suggesting click to go dark)
- **WHEN** in dark mode
- **THEN** the toggle SHALL show a sun icon (suggesting click to go light)

