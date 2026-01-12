return {
  -- GitHub Copilot (official plugin)
  {
    "github/copilot.vim",
    event = "InsertEnter",
    config = function()
      -- Tab to accept suggestion
      vim.g.copilot_no_tab_map = false

      -- Enable for specific filetypes
      vim.g.copilot_filetypes = {
        ["*"] = true,
        ["markdown"] = true,
        ["gitcommit"] = true,
        ["yaml"] = true,
      }

      -- Keymaps
      vim.keymap.set("i", "<C-j>", 'copilot#Accept("\\<CR>")', {
        expr = true,
        replace_keycodes = false,
        desc = "Accept Copilot suggestion",
      })
      vim.keymap.set("i", "<C-]>", "<Plug>(copilot-next)", { desc = "Next Copilot suggestion" })
      vim.keymap.set("i", "<C-[>", "<Plug>(copilot-previous)", { desc = "Previous Copilot suggestion" })
      vim.keymap.set("i", "<C-\\>", "<Plug>(copilot-dismiss)", { desc = "Dismiss Copilot suggestion" })
    end,
  },
}
