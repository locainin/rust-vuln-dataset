from pathlib import Path

from Verification.main import build_parser


def test_interactive_short_flag_and_no_color_are_parsed():
    parser = build_parser(Path("/tmp/verification"))

    args = parser.parse_args(["-i", "--no-color"])

    assert args.interactive is True
    assert args.no_color is True


def test_interactive_long_flag_is_parsed():
    parser = build_parser(Path("/tmp/verification"))

    args = parser.parse_args(["--interactive"])

    assert args.interactive is True
