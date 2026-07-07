# design-token-system Specification

## Purpose
TBD - created by archiving change frontend-ui-optimization. Update Purpose after archive.
## Requirements
### Requirement: Brand Color Palette
The system SHALL define a unified brand color palette based on light blue as the primary hue.

- **Primary**: Light blue (#4A9EFF 或相近色值)
- **Primary Hover**: Slightly darker blue (#3B8CEE)
- **Primary Active**: (#2D7AD9)
- **Background Light**: (#F8FAFE)
- **Surface**: (#FFFFFF)
- **Text Primary**: (#1A1A2E)
- **Text Secondary**: (#6B7280)
- **Border**: (#E5E7EB)

#### Scenario: Colors are defined as CSS variables
- **WHEN** the application loads
- **THEN** CSS custom properties for all brand colors SHALL be available on `:root`

#### Scenario: Colors use Ant Design token overrides
- **WHEN** Ant Design ConfigProvider initializes
- **THEN** `token.colorPrimary`, `token.colorBgContainer`, `token.colorText`, `token.borderRadius`, and related tokens SHALL be set to match the brand palette

#### Scenario: Tailwind theme is extended to match brand colors
- **WHEN** Tailwind utility classes are used
- **THEN** `primary-*` color scale SHALL match the brand palette defined in Ant Design tokens

---

### Requirement: Typography System
The system SHALL define a consistent typography scale.

- **Font family**: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
- **Font sizes**: 12px / 14px / 16px / 20px / 24px / 30px / 38px
- **Line heights**: 1.0 / 1.25 / 1.5 / 1.75
- **Font weights**: 400 (regular) / 500 (medium) / 600 (semibold) / 700 (bold)

#### Scenario: Typography tokens are applied globally
- **WHEN** any text is rendered in the application
- **THEN** the default font family SHALL be Inter or fallback sans-serif

#### Scenario: Ant Design typography tokens are overridden
- **WHEN** Ant Design ConfigProvider initializes
- **THEN** `token.fontFamily`, `token.fontSize*`, `token.lineHeight*`, `token.fontWeight*` SHALL be set

---

### Requirement: Spacing and Radius System
The system SHALL define consistent spacing and border radius values.

- **Border radius**: 4px (small) / 8px (default) / 12px (large) / 16px (xl)
- **Shadows**: sm / default / md / lg / xl levels, matching Linear-style elevation
- **Spacing scale**: 4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64 (px)

#### Scenario: Ant Design radius tokens are overridden
- **WHEN** ConfigProvider initializes
- **THEN** `token.borderRadius`, `token.borderRadiusLG`, `token.borderRadiusSM` SHALL be set to match the radius system

#### Scenario: Ant Design box shadow tokens are overridden
- **WHEN** ConfigProvider initializes
- **THEN** `token.boxShadow` and related tokens SHALL match the Linear-style elevation

