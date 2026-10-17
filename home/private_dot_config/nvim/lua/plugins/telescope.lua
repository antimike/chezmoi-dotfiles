-- telescope-fzf-native sorter (native fzf matching for performance).
-- Preserved from this repo's former example.lua during the BOCO merge.
return {
  {
    "nvim-telescope/telescope.nvim",
    dependencies = {
      "nvim-telescope/telescope-fzf-native.nvim",
      build = "make",
      config = function()
        require("telescope").load_extension("fzf")
      end,
    },
  },
}
