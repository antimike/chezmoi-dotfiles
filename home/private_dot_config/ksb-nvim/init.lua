-- ksb-nvim: the Neovim config kitty-scrollback.nvim runs in (chz-8bg.18). kitty.conf's
-- action_alias starts it with --env NVIM_APPNAME=ksb-nvim, so none of the main LazyVim config
-- loads: no dashboard flash, LSP, treesitter, noice or image.nvim, and no lazy.nvim either.
-- The plugins come from the main config's lazy.nvim install (kitty-scrollback.nvim, tinted-nvim;
-- lazy-lock.json pins them); the main config dir is on the runtimepath for the shared amo theme
-- (lua/amo-theme.lua, colors/base24-amontillado.lua) and holds nothing that auto-loads.
--
-- Scrollback can hold secrets (`pass` output), so nothing from here is kept on disk:
-- no ShaDa (registers and search history), no swap or undo files. Plain `y` stays in nvim's
-- unnamed register and opens ksb's paste window; only the keys below reach the clipboard.
--   <leader>y{motion}, visual <leader>y   copy to the clipboard (cliphist keeps it)  [ksb default]
--   <leader>s{motion}, visual <leader>s,  copy as sensitive: `wl-copy --sensitive`, which cliphist
--   <leader>ss                            skips; cleared after 45 s unless replaced (like pass -c)
-- Both copy without trailing line breaks, flash the text, show a desktop toast (counts only) and
-- close the overlay. Shift+Enter pastes at the prompt, Ctrl+Enter runs it, q quits. which-key
-- lists the <leader> keys (ksb's paste-window footer shows only its own, hard-coded).

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

-- Clipboard: wl-copy without trailing line breaks. `v$` and `V` yank the line's end, and a
-- trailing newline pasted at a shell prompt runs the command. Plain `y` keeps vim's register
-- semantics; only what reaches the system clipboard is trimmed.
local function trim(lines)
  return (table.concat(lines, "\n"):gsub("\n+$", ""))
end

vim.g.clipboard = {
  name = "wl-copy (ksb-nvim, trimmed)",
  copy = {
    ["+"] = function(lines)
      vim.system({ "wl-copy", "--type", "text/plain" }, { stdin = trim(lines) }):wait()
    end,
    ["*"] = function(lines)
      vim.system({ "wl-copy", "--primary", "--type", "text/plain" }, { stdin = trim(lines) }):wait()
    end,
  },
  paste = {
    ["+"] = { "wl-paste", "--no-newline" },
    ["*"] = { "wl-paste", "--no-newline", "--primary" },
  },
}

-- Plugins and theme ----------------------------------------------------------------------------
vim.opt.runtimepath:prepend(vim.fs.joinpath(lazy, "kitty-scrollback.nvim"))
vim.opt.runtimepath:prepend(vim.fs.joinpath(lazy, "tinted-nvim"))
vim.opt.runtimepath:prepend(vim.fs.joinpath(lazy, "which-key.nvim"))
vim.opt.runtimepath:append(vim.fs.joinpath(config, "nvim"))

require("amo-theme").setup({ fallback = "default" })
-- Global options (the first, keyless entry). We close after a clipboard yank ourselves, below,
-- so the copy is confirmed instead of the overlay vanishing silently.
require("kitty-scrollback").setup({ { close_after_yank = false } })
require("which-key").setup({ preset = "helix" })
require("which-key").add({
  { "<leader>y", desc = "Copy to clipboard (cliphist)" },
  { "<leader>yy", desc = "Copy line to clipboard" },
  { "<leader>Y", desc = "Copy to end of line / lines" },
  { "<leader>s", desc = "Copy as sensitive (no cliphist, 45 s)" },
  { "<leader>ss", desc = "Copy line as sensitive" },
})

-- Copy confirmation ----------------------------------------------------------------------------
-- A flash on the copied text, then a desktop toast (counts only, never the text), then quit.
local function confirm_and_quit(summary)
  vim.system({ "notify-send", "--app-name=kitty-scrollback", "--expire-time=2500", "Copied", summary })
  vim.defer_fn(function()
    require("kitty-scrollback.api").quit_all()
  end, 200)
end

local function describe(text)
  local n = select(2, text:gsub("\n", "")) + 1
  return n == 1 and ("%d characters"):format(#text) or ("%d lines"):format(n)
end

vim.api.nvim_create_autocmd("TextYankPost", {
  group = vim.api.nvim_create_augroup("KsbCopyConfirm", { clear = true }),
  callback = function()
    local ev = vim.v.event
    if ev.operator ~= "y" or ev.regname ~= "+" then
      return -- a plain `y` goes to ksb's paste window, not the clipboard
    end
    vim.hl.on_yank({ higroup = "IncSearch", timeout = 200 })
    confirm_and_quit(describe(trim(ev.regcontents)) .. " to the clipboard")
  end,
})

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

local function region(from, to, regtype)
  return vim.fn.getregion(vim.fn.getpos(from), vim.fn.getpos(to), { type = regtype })
end

local function copy_sensitive(lines, from, to, regtype)
  local text = trim(lines)
  if text == "" then
    return
  end
  vim.system({ "sh", "-c", CLIP_SCRIPT, "ksb-sensitive-copy", tostring(CLEAR_AFTER) }, {
    stdin = text,
    detach = true,
  })
  local ns = vim.api.nvim_create_namespace("ksb-sensitive-flash")
  vim.hl.range(0, ns, "IncSearch", from, to, { regtype = regtype })
  confirm_and_quit(("%s as sensitive: not in cliphist, cleared in %d s"):format(describe(text), CLEAR_AFTER))
end

function _G.ksb_sensitive_operator(kind)
  local regtype = ({ line = "V", block = "\22" })[kind] or "v"
  copy_sensitive(region("'[", "']", regtype), "'[", "']", regtype)
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
  local mode = vim.fn.mode()
  local lines = region("v", ".", mode)
  vim.api.nvim_feedkeys(vim.keycode("<Esc>"), "nx", false)
  copy_sensitive(lines, "'<", "'>", mode)
end, { desc = "Copy selection as sensitive (no cliphist; cleared after 45 s)" })
