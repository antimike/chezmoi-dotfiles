-- ksb-nvim: the Neovim config kitty-scrollback.nvim runs in (chz-8bg.18). kitty.conf's
-- action_alias starts it with --env NVIM_APPNAME=ksb-nvim, so none of the main LazyVim config
-- loads: no dashboard flash, LSP, treesitter, noice or image.nvim, and no lazy.nvim either.
-- The plugins come from the main config's lazy.nvim install (kitty-scrollback.nvim, tinted-nvim;
-- lazy-lock.json pins them); the main config dir is on the runtimepath for the shared amo theme
-- (lua/amo-theme.lua, colors/base24-amontillado.lua) and holds nothing that auto-loads.
--
-- Scrollback can hold secrets (`pass` output), so nothing from here is kept on disk:
-- no ShaDa (registers and search history), no swap or undo files. Plain `y` stays in nvim's
-- unnamed register; only the keys below reach the clipboard.
--   <leader>y{motion}, visual <leader>y   copy to the clipboard (cliphist keeps it)  [ksb default]
--   <leader>s{motion}, visual <leader>s,  copy as sensitive: `wl-copy --sensitive`, which cliphist
--   <leader>ss                            skips; cleared after 45 s unless replaced (like pass -c)
-- Both close the overlay. Shift+Enter pastes at the prompt, Ctrl+Enter runs it, q quits.

local data = vim.env.XDG_DATA_HOME
if data == nil or data == "" then
  data = vim.fs.joinpath(vim.env.HOME, ".local", "share")
end
local config = vim.env.XDG_CONFIG_HOME
if config == nil or config == "" then
  config = vim.fs.joinpath(vim.env.HOME, ".config")
end
local lazy = vim.fs.joinpath(data, "nvim", "lazy")

-- Options --------------------------------------------------------------------------------------
vim.g.mapleader = " "
vim.g.maplocalleader = "\\"
vim.o.shada = "" -- nothing read or written: yanks and searches of scrollback stay in memory
vim.o.swapfile = false
vim.o.undofile = false
vim.o.clipboard = "" -- only the explicit keys copy to the system clipboard
vim.o.ignorecase = true
vim.o.smartcase = true
vim.o.termguicolors = true

-- nvim 0.11's OSC 133 handler (prompt marks for [[ ]] in :terminal) races the scrollback
-- replay: the line it marks is gone by the time it runs ("Invalid 'line': out of range" on
-- every open). The overlay needs no prompt marks: drop that one TermRequest handler.
for _, au in ipairs(vim.api.nvim_get_autocmds({ group = "nvim.terminal", event = "TermRequest" })) do
  if au.desc and au.desc:find("OSC 133", 1, true) then
    vim.api.nvim_del_autocmd(au.id)
  end
end

-- Plugins and theme ----------------------------------------------------------------------------
vim.opt.runtimepath:prepend(vim.fs.joinpath(lazy, "kitty-scrollback.nvim"))
vim.opt.runtimepath:prepend(vim.fs.joinpath(lazy, "tinted-nvim"))
vim.opt.runtimepath:append(vim.fs.joinpath(config, "nvim"))

require("amo-theme").setup({ fallback = "default" })
require("kitty-scrollback").setup()

-- Sensitive copy -------------------------------------------------------------------------------
local CLEAR_AFTER = 45 -- seconds, as pass -c (PASSWORD_STORE_CLIP_TIME)

-- The text goes to the shell on stdin (never in argv), and the shell is detached so the clear
-- still runs after the overlay quits. The clipboard is cleared only if it still holds the text.
local CLIP_SCRIPT = [[
s=$(cat)
printf '%s' "$s" | wl-copy --sensitive || exit 1
sleep "$1"
[ "$(wl-paste --no-newline 2>/dev/null)" = "$s" ] && wl-copy --clear
exit 0
]]

local function copy_sensitive(lines)
  local text = table.concat(lines, "\n")
  if text == "" then
    return
  end
  vim.system({ "sh", "-c", CLIP_SCRIPT, "ksb-sensitive-copy", tostring(CLEAR_AFTER) }, {
    stdin = text,
    detach = true,
  })
  -- ksb closes after a clipboard yank (close_after_yank); do the same.
  vim.defer_fn(function()
    require("kitty-scrollback.api").quit_all()
  end, 100)
end

local function region(from, to, regtype)
  return vim.fn.getregion(vim.fn.getpos(from), vim.fn.getpos(to), { type = regtype })
end

function _G.ksb_sensitive_operator(kind)
  local regtype = ({ line = "V", block = "\22" })[kind] or "v"
  copy_sensitive(region("'[", "']", regtype))
end

vim.keymap.set("n", "<leader>s", function()
  vim.o.operatorfunc = "v:lua.ksb_sensitive_operator"
  return "g@"
end, { expr = true, desc = "Copy as sensitive (no cliphist; cleared after 45 s)" })
vim.keymap.set("n", "<leader>ss", function()
  vim.o.operatorfunc = "v:lua.ksb_sensitive_operator"
  return "g@_"
end, { expr = true, desc = "Copy line as sensitive" })
vim.keymap.set("x", "<leader>s", function()
  local lines = region("v", ".", vim.fn.mode())
  vim.api.nvim_feedkeys(vim.keycode("<Esc>"), "nx", false)
  copy_sensitive(lines)
end, { desc = "Copy selection as sensitive (no cliphist; cleared after 45 s)" })
