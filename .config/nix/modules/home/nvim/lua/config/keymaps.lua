-- Keymaps are automatically loaded on the VeryLazy event
-- Add any additional keymaps here

local keymap = vim.keymap

-- Better escape
keymap.set("i", "jk", "<ESC>", { desc = "Exit insert mode" })

-- Clear search highlights
keymap.set("n", "<leader>nh", ":nohl<CR>", { desc = "Clear search highlights" })

-- Window navigation (LazyVim already sets these, but kept for reference)
-- <C-h/j/k/l> to move between windows

-- Resize windows with arrows
keymap.set("n", "<C-Up>", ":resize +2<CR>", { desc = "Increase window height" })
keymap.set("n", "<C-Down>", ":resize -2<CR>", { desc = "Decrease window height" })
keymap.set("n", "<C-Left>", ":vertical resize -2<CR>", { desc = "Decrease window width" })
keymap.set("n", "<C-Right>", ":vertical resize +2<CR>", { desc = "Increase window width" })
