"""The SKU parser, which has to agree with the extension's copy exactly.

These are the same cases as tests/storageCode.test.mjs. If one side changes and
the other does not, the extension and the server disagree about which garment is
which — the worst class of bug this project can have.
"""

import pytest

from sixgenbot.core.sku import (
    describeSku,
    formatSku,
    parseSku,
    skuParts,
    withSku,
)


def test_reads_the_sku_from_the_end_of_a_description():
    assert parseSku("Lovely wool coat, barely worn.\n\n13-8 24") == "13-8-24"


def test_accepts_the_spellings_that_occur_in_real_listings():
    for written in ["13-8 24", "13-8-24", "13 - 8 24", "13-8  24", "13-8 24.", "13–8 24"]:
        assert parseSku(f"Nice jumper. {written}") == "13-8-24", written


def test_leading_zeros_do_not_make_a_different_box():
    assert parseSku("Coat 03-08 04") == parseSku("Coat 3-8 4") == "3-8-4"


def test_five_digit_item_numbers_are_ordinary():
    """Numbers are never recycled, so they climb. EXPLAINED section 7.7."""
    assert parseSku("Vintage silk blouse. 5-6 17735") == "5-6-17735"
    assert parseSku("Coat 13-8 99999") == "13-8-99999"


def test_only_reads_a_sku_at_the_end():
    assert parseSku("Fits size 10-12 nicely, lovely fabric") == ""
    assert parseSku("Waist 30-32 34 inches, see photos for the hem") == ""


def test_nothing_in_nothing_out():
    for text in ["", None, "Just a plain description"]:
        assert parseSku(text) == ""


def test_formatting_is_the_reverse_of_parsing():
    assert formatSku("13-8-24") == "13-8 24"
    assert parseSku(f"Anything. {formatSku('5-6-17735')}") == "5-6-17735"
    assert formatSku("nonsense") == ""


def test_describing_one_for_a_screen():
    assert describeSku("13-8-24") == "column 13, box 8, item 24"
    assert describeSku("") == ""


def test_adding_a_sku_to_a_description_that_has_none():
    assert withSku("Navy wool coat", "13-8-24").endswith("13-8 24")
    assert "Navy wool coat" in withSku("Navy wool coat", "13-8-24")


def test_replacing_a_sku_never_leaves_two():
    changed = withSku("Navy wool coat. 13-8 24", "14-2-7")
    assert parseSku(changed) == "14-2-7"
    assert "13-8" not in changed


def test_a_description_keeps_its_words_when_the_sku_changes():
    changed = withSku("Crushed velvet lining, small mark on the hem. 13-8 24", "14-2-7")
    assert "Crushed velvet lining" in changed
    assert "small mark on the hem" in changed


def test_parts_come_back_for_sorting_a_picking_route():
    assert skuParts("13-8-24") == (13, 8, 24)
    assert skuParts("rubbish") is None

    boxes = ["13-8-24", "2-1-5", "13-2-1"]
    assert sorted(boxes, key=skuParts) == ["2-1-5", "13-2-1", "13-8-24"]


def test_the_pattern_matches_the_extensions_copy():
    """Read the JavaScript and check the two regexes are still the same shape."""
    from pathlib import Path

    from sixgenbot.core.sku import TRAILING_SKU

    javascript = (
        Path(__file__).resolve().parents[2] / "source" / "core" / "storageCode.js"
    ).read_text(encoding="utf-8")

    assert TRAILING_SKU.pattern in javascript, (
        "the Python and JavaScript SKU patterns have drifted apart — "
        "change one, change the other"
    )
