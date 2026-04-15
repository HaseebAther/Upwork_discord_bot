"""Application runtime entrypoint for the Upwork bot."""

from module3_polling_loop import main as polling_main


def main() -> None:
    polling_main()


if __name__ == "__main__":
    main()
