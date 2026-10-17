return {
  {
    "3rd/image.nvim",
    -- Image preview needs a graphics-capable terminal, which is a per-session
    -- property, so gate at runtime: only in a kitty session, and never on WSL
    -- (kitty is awkward there). This also keeps the magick rock from trying to
    -- build on hosts that cannot use image.nvim anyway.
    enabled = function()
      return vim.env.KITTY_WINDOW_ID ~= nil and vim.fn.has("wsl") == 0
    end,
    opts = {
      backend = "kitty",
      -- FFI bindings via the `magick` luarock, installed by lazy's native rocks
      -- from image.nvim's rockspec (rocks.hererocks in lazy.lua). Faster than the
      -- default magick_cli (no per-operation ImageMagick subprocess), which
      -- matters for the jupyter/molten/quarto inline-plot workflow.
      processor = "magick_rock",
      integrations = {
        markdown = {
          enabled = true,
          clear_in_insert_mode = false,
          download_remote_images = true,
          only_render_image_at_cursor = false,
          filetypes = { "markdown", "vimwiki", "quarto" },
        },
      },
      max_width = nil,
      max_height = nil,
      max_width_window_percentage = nil,
      max_height_window_percentage = 50,
      window_overlap_clear_enabled = false,
      window_overlap_clear_ft_ignore = { "cmp_menu", "cmp_docs", "" },
      editor_only_render_when_focused = false,
      tmux_show_only_in_active_window = false,
      hijack_file_patterns = { "*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp" },
    },
  },
}
