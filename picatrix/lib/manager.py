# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Class that defines the manager for all magics."""

from typing import Callable
from typing import List
from typing import Tuple
from typing import Union

import pandas
from IPython import get_ipython

from picatrix.lib import utils


class MagicManager:
  """Manager class for Picatrix magics."""

  _magics = {}

  @classmethod
  def clear_magics(cls):
    """Clear all magic registration."""
    cls._magics = {}

  @classmethod
  def deregister_magic(cls, magic_name: str):
    """Removes a magic from the registration.

    Args:
      magic_name (str): the name of the magic to remove.

    Raises:
      KeyError: if the magic is not registered.
    """
    if magic_name not in cls._magics:
      raise KeyError(f'Magic [{magic_name}] is not registered.')

    _ = cls._magics.pop(magic_name)

  @classmethod
  def get_magic(cls, magic_name: str) -> Callable[[str, str], str]:
    """Return a magic function from the registration."""
    return cls._magics.get(magic_name)

  @classmethod
  def get_magic_info(cls, as_pandas: bool = False) -> Union[
      pandas.DataFrame, List[Tuple[str, str]]]:
    """Get a list of all magics.

    Args:
      as_pandas (bool): boolean to determine whether to receive the results
          as a list of tuples or a pandas DataFrame. Defaults to False.

    Returns:
      Either a pandas DataFrame or a list of tuples, depending on the as_pandas
      boolean.
    """
    if not as_pandas:
      return [(x.magic_name, x.__doc__.split('\n')[0]) for x in iter(
          cls._magics.values())]

    entries = []
    for magic_name, magic_class in iter(cls._magics.items()):
      description = magic_class.__doc__.split('\n')[0]
      magic_dict = {
          'name': magic_name,
          'cell': f'%%{magic_name}',
          'line': f'%{magic_name}',
          'function': f'{magic_name}_func',
          'description': description}
      entries.append(magic_dict)
    df = pandas.DataFrame(entries)
    return df[
        ['name', 'description', 'line', 'cell', 'function']].sort_values('name')

  @classmethod
  def register_magic(
      cls, function: Callable[[str, str], str],
      conditional: Callable[[], bool] = None):
    """Register magic function as a magic in sstbook.

    Args:
      function (function): the function to register as a line and a
          cell magic.
      conditional (function): a function that should return a bool, used to
          determine whether to register magic or not. This can be used by
          magics to determine whether a magic should be registered or not, for
          instance basing that on whether the notebook is being run in borg
          or local runtime, or whether a connection to a client can be achieved,
          etc. This is optional and if not provided a magic will be registered.

    Raises:
      KeyError: if the magic is already registered.
    """
    if conditional and not conditional():
      return

    magic_name = function.magic_name

    if magic_name in cls._magics:
      raise KeyError(
          f'The magic [{magic_name}] is already registered.')

    ip = get_ipython()
    ip.register_magic_function(
        function, magic_kind='line_cell', magic_name=magic_name)

    cls._magics[magic_name] = function
    function_name = f'{magic_name}_func'

    _ = utils.ipython_bind_global(function_name, function.fn)
