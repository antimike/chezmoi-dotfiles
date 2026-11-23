-- tinted-nvim: the colorscheme since chz-8bg.17, loaded on require by lua/amo-theme.lua (through
-- lua/amontillado/tinted.lua, vendored from amontillado's nvim example), which feeds
-- ~/.cache/theme/current/palette.lua to setup({ schemes = { ["base24-amontillado"] = palette } }).
-- 1.* because setup({ schemes = ... }) exists only from v1.0.0. Its selector stays off: it reads
-- tinty's current_scheme file, and there is no tinty here (D73).
return {
  "tinted-theming/tinted-nvim",
  lazy = true,
  version = "1.*",
}
