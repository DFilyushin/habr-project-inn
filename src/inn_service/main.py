import typer
from core.application import Application
from app_container import ApplicationContainer


def main():
    try:
        application = Application(ApplicationContainer)
        application.run()
    except BaseException as exc:
        typer.echo(f'Error starting application. Details: {str(exc)}')


if __name__ == "__main__":
    typer.run(main)
