return {
  {
    "williamboman/mason-lspconfig.nvim",
    config = function()
      require("mason-lspconfig").setup({
        ensure_installed = {
          "bashls",
          "html",
          "jsonls",
          "lua_ls",
          "purescriptls",
        },
      })
    end,
  },
}
