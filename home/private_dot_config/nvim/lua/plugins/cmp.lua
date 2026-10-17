-- Supertab: use <Tab>/<S-Tab> to drive completion and snippet navigation.
-- LazyVim's completion engine is blink.cmp (see snippets.lua), so this
-- preserves the old nvim-cmp "supertab" preference as blink's super-tab
-- keymap preset during the BOCO merge.
return {
  {
    "saghen/blink.cmp",
    opts = {
      keymap = { preset = "super-tab" },
    },
  },
}
