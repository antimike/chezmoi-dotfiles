# fast-syntax-highlighting style overrides, sourced by the plugin's atload ice
# (.chezmoitemplates/zsh/plugins.d/0050.syntax-highlighting.yaml).
# The plugin's default theme draws comments black, which is invisible on a dark
# background (kitty does not brighten bold). Colour 8 is the theme's dim grey;
# the kitty palette keeps it legible (check with tools/term-contrast).
FAST_HIGHLIGHT_STYLES[${FAST_THEME_NAME}comment]='fg=8'

# The default theme's 256-colour entries, onto ANSI 0-15 so they follow the palette in both
# variants (chz-djc): under a light theme variable's 113 (light green) was 1.67:1 and text on
# subtle-bg's and the here-strings' 18 (navy) 1.10:1. Colour 8 is fsh's own subtle background
# when the terminal lacks 256 colours (it falls back to blue; 8 reads better on both variants).
FAST_HIGHLIGHT_STYLES[${FAST_THEME_NAME}variable]='fg=10'
FAST_HIGHLIGHT_STYLES[${FAST_THEME_NAME}subtle-bg]='bg=8'
FAST_HIGHLIGHT_STYLES[${FAST_THEME_NAME}here-string-text]='bg=8'
FAST_HIGHLIGHT_STYLES[${FAST_THEME_NAME}here-string-var]='fg=6,bg=8'

# The matching bracket under the cursor: the default bg=blue under the default foreground is
# 1.78:1 under light-soft (amontillado v0.11.0 tone, chz-lfs); bg=8 like subtle-bg reads on both.
FAST_HIGHLIGHT_STYLES[${FAST_THEME_NAME}paired-bracket]='bg=8'
