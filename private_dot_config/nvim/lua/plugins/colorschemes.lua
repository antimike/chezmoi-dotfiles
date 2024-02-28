return {
  "sjl/badwolf",
  -- TreeSitter colorschemes
  {
    "ChristianChiarulli/nvcode-color-schemes.vim",
  },
  {
    "metalelf0/jellybeans-nvim",
  },
  { "ellisonleao/gruvbox.nvim" },
  { "shaunsingh/nord.nvim", after = "nvcode-colorschemes" },
  { "wuelnerdotexe/vim-enfocado" },
  {
    "lalitmee/cobalt2.nvim",
  },
  {
    "shaeinst/roshnivim-cs",
  },
  {
    "sainnhe/sonokai",
  },
  {
    "sainnhe/edge",
  },
  {
    "sainnhe/everforest",
  },
  {
    "rafamadriz/neon",
    config = function()
      local opts = {
        style = "default",
        italic_comment = true,
        italic_keyword = false,
        italic_boolean = false,
        italic_function = false,
        italic_variable = false,
        bold = false,
        transparent = true,
      }

      for k, v in pairs(opts) do
        vim.g["neon_" .. k] = v
      end
    end,
  },
  {
    "folke/tokyonight.nvim",
  },
  {
    "theniceboy/nvim-deus",
  },
  {
    "rockerBOO/boo-colorscheme-nvim",
  },
  -- {
  -- 	"glepnir/zephyr-nvim",
  -- },
  {
    "mhartington/oceanic-next",
  },
  {
    "kyazdani42/blue-moon",
  },
  {
    "bluz71/vim-moonfly-colors",
  },
  {
    "bluz71/vim-nightfly-guicolors",
  },
  {
    "ray-x/aurora",
  },
  {
    "savq/melange",
  },
  {
    "shaunsingh/moonlight.nvim",
  },
  {
    "lourenci/github-colors",
  },
  {
    "mcchrish/zenbones.nvim",
  },
  {
    "frenzyexists/aquarium-vim",
  },
  {
    "EdenEast/nightfox.nvim",
  },
  {
    "kvrohit/substrata.nvim",
  },
  {
    "tiagovla/tokyodark.nvim",
  },
  {
    "tanvirtin/monokai.nvim",
  },
}
