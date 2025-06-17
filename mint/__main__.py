from __future__ import annotations

"""Package entry-point for the Mint AI Framework.

Usage::

    python -m mint "Tell me a joke about robots"
    # or after installing:
    mint "Explain the difference between TCP and UDP"
"""

import sys
import argparse

from mint.assistant import Assistant


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mint",
        description="Mint AI – small wrapper CLI around the Assistant class",
    )
    parser.add_argument(
        "prompt",
        nargs=argparse.REMAINDER,
        help="Prompt text to send to the language model.",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        dest="max_length",
        default=None,
        help="Maximum number of tokens to generate (overrides config).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Sampling temperature (overrides config).",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=None,
        help="Top-p nucleus sampling parameter (overrides config).",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.prompt:
        parser.print_help(sys.stderr)
        sys.exit(1)

    prompt_text = " ".join(args.prompt)

    assistant = Assistant()
    response = assistant.generate(
        prompt_text,
        max_length=args.max_length,
        temperature=args.temperature,
        top_p=args.top_p,
    )

    print(response)


if __name__ == "__main__":
    main() 