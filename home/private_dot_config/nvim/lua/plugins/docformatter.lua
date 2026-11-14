-- On-demand docstring wrap at 80 columns (chz-nku). docformatter (pipx, python-tools
-- target) runs only from <leader>cD, never on save: it is deliberately absent from
-- formatters_by_ft. A pyproject.toml with a [tool.docformatter] table wins: then the
-- wrap widths come from it, not from here. Comment reflow is gw (textwidth=80 per
-- filetype, config/autocmds.lua).

local WIDTH = "80"

-- The nearest pyproject.toml above the file, if it configures docformatter.
local function project_config(ctx)
  local found = vim.fs.find("pyproject.toml", { path = ctx.dirname, upward = true })[1]
  if not found then
    return nil
  end
  for _, line in ipairs(vim.fn.readfile(found)) do
    if line:match("^%s*%[tool%.docformatter%]") then
      return found
    end
  end
  return nil
end

local function args(ctx)
  local cfg = project_config(ctx)
  local ret = { "--in-place" }
  if cfg then
    vim.list_extend(ret, { "--config", cfg })
  else
    vim.list_extend(ret, { "--wrap-summaries", WIDTH, "--wrap-descriptions", WIDTH })
  end
  if ctx.range then
    vim.list_extend(ret, { "--range", tostring(ctx.range.start[1]), tostring(ctx.range["end"][1]) })
  end
  table.insert(ret, "$FILENAME")
  return ret
end

return {
  {
    "stevearc/conform.nvim",
    keys = {
      {
        "<leader>cD",
        function()
          require("conform").format({ formatters = { "docformatter" }, timeout_ms = 5000 })
        end,
        mode = { "n", "v" },
        ft = "python",
        desc = "Wrap Docstrings (80)",
      },
    },
    opts = {
      formatters = {
        docformatter = {
          -- docformatter skips hidden files (exit 1), and conform's default temp name
          -- starts with a dot.
          tmpfile_format = "conform.$RANDOM.$FILENAME",
          args = function(_, ctx)
            return args(ctx)
          end,
          range_args = function(_, ctx)
            return args(ctx)
          end,
        },
      },
    },
  },
  {
    "folke/which-key.nvim",
    opts = {
      spec = {
        { "gw", desc = "Reflow (textwidth, keeps comment leaders)", mode = { "n", "x" } },
        { "gq", desc = "Format lines (conform)", mode = { "n", "x" } },
      },
    },
  },
}
