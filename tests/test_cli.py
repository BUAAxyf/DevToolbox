from devtoolbox.main import parse_cli_args, run_cli


def test_parse_cli_args_defaults() -> None:
    args = parse_cli_args([])

    assert args.host == "127.0.0.1"
    assert args.port == 8000
    assert args.reload is False


def test_run_cli_passes_options_to_uvicorn_runner() -> None:
    calls = []

    def fake_runner(app_ref: str, **kwargs: object) -> None:
        calls.append((app_ref, kwargs))

    run_cli(["--host", "127.0.0.1", "--port", "8010", "--reload"], runner=fake_runner)

    assert calls == [
        (
            "devtoolbox.main:app",
            {
                "host": "127.0.0.1",
                "port": 8010,
                "reload": True,
            },
        )
    ]
