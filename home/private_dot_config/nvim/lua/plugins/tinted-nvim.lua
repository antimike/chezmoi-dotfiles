-- tinted-nvim: loaded on require only, for amontillado's theming example (docs/examples/nvim/,
-- amo-aqp.22), which feeds ~/.cache/theme/current/palette.lua to
-- require("tinted-nvim").setup({ schemes = { ["base24-amo"] = palette } }). Not the colorscheme.
-- 1.* because setup({ schemes = ... }) exists only from v1.0.0. Its selector stays off (the
-- default): it reads tinty's current_scheme file, and there is no tinty here (D73).
return {
  "tinted-theming/tinted-nvim",
  lazy = true,
  version = "1.*",
}
