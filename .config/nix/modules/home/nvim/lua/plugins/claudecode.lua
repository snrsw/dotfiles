return {
  -- Claude Code integration
  {
    "coder/claudecode.nvim",
    dependencies = {
      "nvim-lua/plenary.nvim",
    },
    config = true,
    keys = {
      { "<leader>ac", "<cmd>ClaudeCode<cr>", desc = "Toggle Claude Code" },
      { "<leader>as", "<cmd>ClaudeCodeSend<cr>", mode = { "n", "v" }, desc = "Send to Claude" },
      { "<leader>ao", "<cmd>ClaudeCodeOpen<cr>", desc = "Open Claude Code" },
      { "<leader>at", "<cmd>ClaudeCodeTreeAdd<cr>", desc = "Add file to Claude context" },
    },
  },
}
