from __future__ import annotations

import logging
from typing import List, Optional

from pyenv_inspect import find_pyenv_python_executable
from pyenv_inspect.exceptions import SpecParseError, UnsupportedImplementation
from virtualenv.discovery.discover import Discover
from virtualenv.discovery.py_info import PythonInfo
from virtualenv.discovery.py_spec import PythonSpec


class Pyenv(Discover):
    """pyenv discovery mechanism"""

    def __init__(self, options) -> None:
        super().__init__(options)
        try:
            self._string_specs: List[str] = options.python
        except AttributeError:
            raise RuntimeError("no Python version was provided to virtualenv-pyenv")
        self._app_data = options.app_data

    def __str__(self) -> str:
        if len(self._string_specs) == 1:
            spec = self._string_specs[0]
        else:
            spec = self._string_specs
        return f'{self.__class__.__name__} discover of spec={spec!r}'

    @classmethod
    def add_parser_arguments(cls, parser) -> None:
        parser.add_argument(
            "-p",
            "--python",
            dest="python",
            metavar="py",
            type=str,
            action="append",
            default=[],
            help="interpreter based on what to create environment (path/identifier) "
            "- by default use the interpreter where the tool is installed - first found wins",
        )

    def run(self) -> Optional[PythonInfo]:
        for string_spec in self._string_specs:
            result = self._get_interpreter(string_spec)
            if result is not None:
                return result
        return None

    def _get_interpreter(self, string_spec: str) -> Optional[PythonInfo]:
        logging.debug('find interpreter for spec %s', string_spec)
        spec: PythonSpec = PythonSpec.from_string_spec(string_spec)
        if spec.implementation:
            logging.error('only CPython is currently supported')
            return None
        exec_name = next(spec.generate_names())[0]
        try:
            exec_path = find_pyenv_python_executable(exec_name)
        except SpecParseError:
            logging.error('failed to parse spec %s', string_spec)
            return None
        except UnsupportedImplementation:
            logging.error('only CPython is currently supported')
            return None
        if exec_path is None:
            return None
        return PythonInfo.from_exe(
            str(exec_path), app_data=self._app_data, env=self._env)
