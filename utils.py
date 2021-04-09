import os
import exceptions


def get_env_variable(name: str):
    try:
        return os.environ[name]
    except KeyError:
        raise exceptions.MissingEnvironmentVariable(
            f'"{name}" is not set in the environment. Check your .env file or'
            f"create one if you don't have it."
        )
