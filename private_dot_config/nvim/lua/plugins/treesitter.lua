return {
  {
    "nvim-treesitter/nvim-treesitter",
    opts = function(_, opts)
      -- add tsx and treesitter
      vim.list_extend(opts.ensure_installed, {
        "tsx",
        "typescript",
      })
    end,
    config = function()
      require("nvim-treesitter.configs").setup({
        highlight = {
          disable = function()
            -- check if 'filetype' option includes 'chezmoitmpl'
            if string.find(vim.bo.filetype, "chezmoitmpl") then
              return true
            end
          end,
        },
      })
    end,
  },
}
