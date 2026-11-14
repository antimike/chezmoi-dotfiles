-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
-- Add any additional autocmds here

vim.cmd([[
  autocmd BufNewFile,BufRead *.cshtml set filetype=html.cshtml.razor
]])

-- Disable autoformat for Chezmoi template files (template syntax breaks formatters)
vim.api.nvim_create_autocmd("FileType", {
  pattern = "*.chezmoitmpl",
  callback = function(args)
    vim.b[args.buf].autoformat = false
  end,
})

-- Comment reflow at 80 columns, on demand only (chz-nku): gw{motion} (e.g. gwip)
-- rewraps a comment block with its leaders at textwidth. Remove t and c from
-- formatoptions so nothing wraps while typing; docstrings: <leader>cD
-- (plugins/docformatter.lua).
vim.api.nvim_create_autocmd("FileType", {
  pattern = { "python", "lua", "sh", "bash", "zsh", "c", "cpp", "rust", "go", "javascript", "typescript" },
  callback = function()
    vim.opt_local.textwidth = 80
    vim.opt_local.formatoptions:remove({ "t", "c" })
  end,
})
