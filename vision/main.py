def main():
    try:
        from ui import run_ui
    except ImportError as error:
        raise SystemExit(
            "The Tkinter UI runtime is unavailable. Install a Tcl/Tk runtime and retry."
        ) from error

    run_ui()


if __name__ == "__main__":
    main()
