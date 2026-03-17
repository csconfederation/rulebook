#!/usr/bin/env python3

from __future__ import annotations

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

import format_markdown


class FormatMarkdownGuardrailsTest(unittest.TestCase):
    def test_formatting_changes_preserve_visible_wording(self) -> None:
        original = """# Example

#### Membership

- **7.1.10**&emsp;The league will make use of Discord (https://discord.com/) as per [8.1.1](#Preseason)

&emsp;
"""
        formatted = format_markdown.format_markdown(original)

        self.assertNotEqual(formatted, original)
        format_markdown.ensure_preserves_visible_wording(Path("docs/example.md"), original, formatted)
        self.assertEqual(
            format_markdown.wording_tokens(original),
            format_markdown.wording_tokens(formatted),
        )

    def test_guard_rejects_word_or_number_changes(self) -> None:
        original = (
            "- **4.5.4**&emsp;Refer to [Section 5.6](5_transactions.md#56-promotionrelegation) "
            "for promotion and demotion rules.\n"
        )
        changed = (
            "- **4.5.4**&emsp;Refer to [Section 5.9](5_transactions.md#59-promotiondemotion) "
            "for promotion and demotion rules.\n"
        )

        with self.assertRaises(ValueError):
            format_markdown.ensure_preserves_visible_wording(Path("docs/example.md"), original, changed)


if __name__ == "__main__":
    unittest.main()
