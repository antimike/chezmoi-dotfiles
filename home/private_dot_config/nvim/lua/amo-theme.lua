-- The amontillado palette as nvim's colorscheme (chz-8bg.17; docs/plans/theming.md, "nvim").
--
-- Shared by the main (LazyVim) config and the kitty-scrollback config (ksb-nvim, chz-8bg.18):
--   require("amo-theme").setup()
-- loads ~/.cache/theme/current/palette.lua (amo's built-in `nvim` template) into tinted-nvim
-- as the base24 scheme `base24-amontillado` and re-applies it after every `amo theme apply`
-- (an fs_event watch on ~/.cache/theme/, lua/amontillado/watch.lua) while it is still the
-- active colorscheme. Light/dark follows the palette's `variant`.
--
-- colors/base24-amontillado.lua makes the name a real colorscheme: tinted-nvim sets
-- colors_name to it, and anything that re-runs `:colorscheme <colors_name>` (fzf-lua's
-- picker restoring the scheme it started from, a `background` change) needs the file.
--
-- If the palette or tinted-nvim is missing (a fresh machine before the first `amo theme
-- apply`, or ksb-nvim without the plugin), setup() falls back to `fallback` and says why once;
-- the watch still starts, so the first apply switches the running nvim over.

local M = {}

M.name = "base24-amontillado"
M.fallback = "gruvbox"

local watching = false
local fell_back = false -- setup() used the fallback; the first good apply clears it
local last_opts = {}

-- amontillado's default theme.cache, as lua/amontillado/watch.lua resolves it.
local function cache_dir()
  local base = vim.env.XDG_CACHE_HOME
  if base == nil or base == "" then
    base = vim.fs.joinpath(vim.env.HOME, ".cache")
  end
  return vim.fs.joinpath(base, "theme")
end

-- Mix `amount` of colour a into colour b ("#rrggbb").
local function blend(a, b, amount)
  local out = {}
  for i = 0, 2 do
    local ca = tonumber(a:sub(2 + 2 * i, 3 + 2 * i), 16)
    local cb = tonumber(b:sub(2 + 2 * i, 3 + 2 * i), 16)
    out[#out + 1] = string.format("%02x", math.floor(ca * amount + cb * (1 - amount) + 0.5))
  end
  return "#" .. table.concat(out)
end

-- tinted-nvim's diff groups are background-coloured text on a darkened base0D (DiffAdd) or link
-- to CursorLine/NonText: unreadable on either variant here (dark text on dark blue). Ours tint
-- the background with the hue and keep the normal text colour, so syntax colours stay readable.
local function diff_overrides(p)
  return {
    DiffAdd = { bg = blend(p.base0B, p.base00, 0.22) },
    DiffDelete = { fg = p.base08, bg = blend(p.base08, p.base00, 0.18) },
    DiffChange = { bg = blend(p.base0D, p.base00, 0.14) },
    DiffText = { bg = blend(p.base0D, p.base00, 0.32), bold = true },
  }
end

--- Apply the palette now; raises on a missing palette or tinted-nvim.
--- (colors/base24-amontillado.lua calls this, with the options setup() was last given.)
--- @param opts? { setup?: table }
function M.apply(opts)
  opts = opts or last_opts
  local setup = vim.tbl_deep_extend("force", {}, opts.setup or {})
  local user = setup.highlights and setup.highlights.overrides
  setup.highlights = setup.highlights or {}
  setup.highlights.overrides = function(p)
    return vim.tbl_extend("force", diff_overrides(p), user and user(p) or {})
  end
  require("amontillado.tinted").apply({ setup = setup })
end

--- `:colorscheme base24-amontillado` (colors/base24-amontillado.lua).
--- palette.lua holds one variant, so a 'background' change while amo is active (nvim re-runs
--- `:colorscheme <current>`; LazyVim's <leader>ub) cannot be honoured here: say so and put
--- 'background' back after the option change returns (setting it inside the reload leaves
--- colors_name unset). Switch variants with `amo theme apply --variant dark|light`.
function M.colorscheme()
  if vim.g.colors_name == M.name then
    local ok, palette = pcall(require("amontillado.palette").load)
    if ok and palette.variant ~= vim.o.background then
      vim.notify(
        ("amo-theme: the amo palette is %s; switch with `amo theme apply --variant %s`"):format(
          palette.variant,
          vim.o.background
        ),
        vim.log.levels.WARN
      )
      vim.schedule(function()
        vim.o.background = palette.variant
      end)
      return
    end
  end
  M.apply()
end

--- @param opts? { fallback?: string, setup?: table }
--- @return boolean ok true when the amo palette is in use
function M.setup(opts)
  opts = opts or {}
  last_opts = opts
  local fallback = opts.fallback or M.fallback
  local ok, err = pcall(M.apply)
  if not ok then
    vim.notify("amo-theme: " .. tostring(err) .. "; using " .. fallback, vim.log.levels.WARN)
    pcall(vim.cmd.colorscheme, fallback)
    fell_back = true
  end
  -- The cache directory must exist to be watched; without it there is no amo on this machine.
  if not watching and vim.uv.fs_stat(cache_dir()) then
    watching = true
    require("amontillado.watch").start(function()
      -- Follow the theme only while amo is the colorscheme, or the startup fallback still
      -- stands in for it: a scheme picked by hand stays until `:colorscheme base24-amontillado`.
      local current = vim.g.colors_name
      if current ~= M.name and not (fell_back and current == fallback) then
        return
      end
      local reok, reerr = pcall(M.apply)
      if reok then
        fell_back = false
      else
        vim.notify("amo-theme: re-apply failed: " .. tostring(reerr), vim.log.levels.WARN)
      end
    end)
  end
  return ok
end

return M
