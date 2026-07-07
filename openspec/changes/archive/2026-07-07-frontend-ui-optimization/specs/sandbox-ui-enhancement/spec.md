## ADDED Requirements

### Requirement: Enhanced Sandbox Toolbar
The sandbox toolbar (SandboxHeader) SHALL have a restyled appearance.

- **Background**: Glassmorphism or elevated surface to separate from editor area
- **Layout**: Clean horizontal bar with consistent spacing between action groups
- **Buttons**: Icon + label pattern with brand hover state

#### Scenario: Toolbar renders with elevated appearance
- **WHEN** the sandbox page renders
- **THEN** the toolbar SHALL appear as a visually distinct bar above the editor area

---

### Requirement: Enhanced Monaco Editor Container
The Monaco editor container SHALL be updated to match the new design.

- **Border**: Subtle border matching theme, rounded corners
- **Background**: Consistent with surface color
- **Theme sync**: Monaco editor theme SHALL switch between `vs` (light) and `vs-dark` (dark) when app theme changes

#### Scenario: Editor container has themed border and corner
- **WHEN** the sandbox page renders
- **THEN** the Monaco editor container SHALL have a border matching the current theme and rounded corners

#### Scenario: Editor theme syncs with app theme
- **WHEN** user switches app theme
- **THEN** the Monaco editor SHALL switch to the corresponding light/dark theme

---

### Requirement: Enhanced Diff View
The diff view (SandboxDiffView) SHALL have improved visual styling.

- **Additions**: Green background with subtle green border
- **Removals**: Red background with subtle red border
- **Header**: Clear section labels with line count badges

#### Scenario: Diff view shows clear addition/removal colors
- **WHEN** a diff is displayed
- **THEN** additions SHALL have green styling and removals SHALL have red styling

---

### Requirement: Enhanced Snapshot Panel
The snapshot panel (SandboxSnapshotPanel) SHALL be restyled.

#### Scenario: Snapshot items have card-like appearance
- **WHEN** snapshots are listed
- **THEN** each snapshot SHALL display as a card with hover elevation effect
