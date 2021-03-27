# -*- coding: utf-8 -*-

import copy
from naas.runner.env_var import cpath
import nbformat
from pathlib import Path

from papermill.log import logger
from papermill.iorw import (
    get_pretty_path,
    local_file_io_cwd,
    load_notebook_node,
    write_ipynb,
)
from papermill.engines import papermill_engines
from papermill.execute import (
    prepare_notebook_metadata,
    remove_error_markers,
    raise_for_execution_errors,
)
from papermill.utils import chdir
from papermill.parameterize import (
    add_builtin_parameters,
    parameterize_notebook,
    parameterize_path,
)
import json


def execute_notebook(
    uid,
    runtime,
    input_path,
    output_path,
    parameters=None,
    engine_name=None,
    request_save_on_cell_execute=True,
    prepare_only=False,
    kernel_name=None,
    progress_bar=True,
    log_output=False,
    stdout_file=None,
    stderr_file=None,
    start_timeout=60,
    report_mode=False,
    cwd=None,
    **engine_kwargs,
):
    """Executes a single notebook locally.
    Parameters
    ----------
    input_path : str or Path
        Path to input notebook
    output_path : str or Path
        Path to save executed notebook
    parameters : dict, optional
        Arbitrary keyword arguments to pass to the notebook parameters
    engine_name : str, optional
        Name of execution engine to use
    request_save_on_cell_execute : bool, optional
        Request save notebook after each cell execution
    autosave_cell_every : int, optional
        How often in seconds to save in the middle of long cell executions
    prepare_only : bool, optional
        Flag to determine if execution should occur or not
    kernel_name : str, optional
        Name of kernel to execute the notebook against
    progress_bar : bool, optional
        Flag for whether or not to show the progress bar.
    log_output : bool, optional
        Flag for whether or not to write notebook output to the configured logger
    start_timeout : int, optional
        Duration in seconds to wait for kernel start-up
    report_mode : bool, optional
        Flag for whether or not to hide input.
    cwd : str or Path, optional
        Working directory to use when executing the notebook
    **kwargs
        Arbitrary keyword arguments to pass to the notebook engine
    Returns
    -------
    nb : NotebookNode
       Executed notebook object
    """
    if isinstance(input_path, Path):
        input_path = str(input_path)
    if isinstance(output_path, Path):
        output_path = str(output_path)
    if isinstance(cwd, Path):
        cwd = str(cwd)

    path_parameters = add_builtin_parameters(parameters)
    input_path = parameterize_path(input_path, path_parameters)
    output_path = parameterize_path(output_path, path_parameters)

    logger.info("Input Notebook:  %s" % get_pretty_path(input_path))
    logger.info("Output Notebook: %s" % get_pretty_path(output_path))
    with local_file_io_cwd():
        if cwd is not None:
            logger.info("Working directory: {}".format(get_pretty_path(cwd)))

        nb = load_notebook_node(input_path)

        # Parameterize the Notebook.
        if parameters:
            nb = parameterize_notebook(nb, parameters, report_mode)

        nb = prepare_notebook_metadata(nb, input_path, output_path, report_mode)
        # clear out any existing error markers from previous papermill runs
        nb = remove_error_markers(nb)
        # add naas code to make naas feature act differently in production
        nb = prepare_notebook_naas(nb, input_path, uid, runtime)
        if not prepare_only:
            # Fetch the kernel name if it's not supplied
            kernel_name = kernel_name or nb.metadata.kernelspec.name

            # Execute the Notebook in `cwd` if it is set
            with chdir(cwd):
                nb = papermill_engines.execute_notebook_with_engine(
                    engine_name,
                    nb,
                    input_path=input_path,
                    output_path=output_path if request_save_on_cell_execute else None,
                    kernel_name=kernel_name,
                    progress_bar=progress_bar,
                    log_output=log_output,
                    start_timeout=start_timeout,
                    stdout_file=stdout_file,
                    stderr_file=stderr_file,
                    **engine_kwargs,
                )

            # Check for errors first (it saves on error before raising)
            raise_for_execution_errors(nb, output_path)

        # Write final output in case the engine didn't write it on cell completion.
        write_ipynb(nb, output_path)
        return nb


def prepare_notebook_naas(nb, input_path, uid, runtime):
    """Prepare notebook and inject cell with  naas env config
    Parameters
    ----------
    nb : NotebookNode
       Executable notebook object
    input_path : str
        Path to input notebook
    uid : str
       uid of executed notebook
    """
    # Copy the nb object to avoid polluting the input
    nb = copy.deepcopy(nb)
    language = nb.metadata.kernelspec.language
    if language == "python":
        current_data = {
            "uid": uid,
            "path": cpath(input_path),
            "env": "RUNNER",
            "runtime": runtime,
        }
        param_content = (
            f"import naas\nnaas.n_env.current = {json.dumps(current_data, indent=4)}"
        )
        newcell = nbformat.v4.new_code_cell(source=param_content)
        newcell.metadata["tags"] = ["naas-injected"]
        nb.cells = [newcell] + nb.cells
    return nb
