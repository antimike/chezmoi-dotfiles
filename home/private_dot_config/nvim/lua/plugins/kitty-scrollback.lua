-- kitty's scrollback in Neovim (chz-8bg.15, trial): kitty's vim copy mode, replacing the
-- kitty_grab kitten. kitty starts it through the kitten in this plugin's python/ directory
-- (the action_alias in kitty.conf); `:KittyScrollbackCheckHealth` checks the setup.
return {
  "mikesmithgh/kitty-scrollback.nvim",
  enabled = true,
  lazy = true,
  cmd = { "KittyScrollbackGenerateKittens", "KittyScrollbackCheckHealth", "KittyScrollbackGenerateCommandLineEditing" },
  event = { "User KittyScrollbackLaunch" },
  version = "^9.0.0", -- major pinned: fixes and features without breaking changes
  config = function()
    require("kitty-scrollback").setup()
  end,
}
