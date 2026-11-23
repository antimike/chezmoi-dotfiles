-- `:colorscheme base24-amontillado`: the amontillado palette through tinted-nvim (chz-8bg.17).
-- tinted-nvim sets colors_name to this name, so anything that re-runs `:colorscheme <current>`
-- (fzf-lua's picker restoring its starting scheme, a 'background' change) lands here; without
-- this file that raised E185 and broke the picker. The work is in lua/amo-theme.lua.
require("amo-theme").colorscheme()
