# fast-syntax-highlighting style overrides, sourced by the plugin's atload ice
# (.chezmoitemplates/zsh/plugins.d/0050.syntax-highlighting.yaml).
# The plugin's default theme draws comments black, which is invisible on a dark
# background (kitty does not brighten bold). Colour 8 is the theme's dim grey;
# the kitty palette keeps it legible (check with tools/term-contrast).
FAST_HIGHLIGHT_STYLES[${FAST_THEME_NAME}comment]='fg=8'
