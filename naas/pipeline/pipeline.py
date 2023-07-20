from pyvis.network import Network
import uuid
import threading
import papermill as pm
from enum import Enum
import time

from typing import Literal

from IPython.display import clear_output, display
from IPython.core.display import HTML

import os
import random
import datetime

from rich.progress import (
    Progress,
    TextColumn,
    SpinnerColumn,
)


class PipelineAlreadyRan(Exception):
    """An exception that will be raised if you try to re run a pipeline.

    Args:
        Exception (Exception): The exception being raised.
    """

    pass


class ExecutionContext:
    """A class that is passed to each step when running to provide informations about the pipeline."""

    execution_id: str = None
    timestamp: str = None
    output_dir: str = None
    output_path: str = None

    def __init__(self, output_dir: str = "pipeline_executions"):
        self.execution_id = str(uuid.uuid4())
        self.output_dir = output_dir
        self.timestamp = datetime.datetime.now()

        self.output_path = os.path.join(
            self.output_dir,
            f'{self.timestamp.strftime("%Y-%m-%d_%H-%M-%S")}-{self.execution_id}',
        )

        os.makedirs(self.output_path, exist_ok=True)


class StepStatus(Enum):
    """Enum used to define the status of a Step

    Args:
        Enum (integer): The value of the status
    """

    INITIALIZED = 1
    RUNNING = 2
    COMPLETED = 3
    ERRORED = 4


status_color_rel = {
    StepStatus.INITIALIZED: "#9EA7AC",
    StepStatus.RUNNING: "#64C9FA",
    StepStatus.COMPLETED: "#5DE191",
    StepStatus.ERRORED: "#FF3938",
}


class Step:
    """This is the core class that embed all the logic to run a step.

    Returns:
        Step: the step
    """

    next_steps: list = []
    steps: list = []
    name: str = ""
    node_color: str = "#9EA7AC"
    node_mass: int = 5
    node_shape: str = "box"
    node_image: str = None
    status: StepStatus = StepStatus.INITIALIZED
    output: any = None

    def __init__(self, name: str = "", error_step: bool = False):
        self.name = name
        self.next_steps = []
        self.on_error_next_steps = []
        self.steps = []
        self.status = StepStatus.INITIALIZED
        self.node_image = None
        self.output = None
        self.error_step = error_step
        if error_step is False:
            self.on_error = Step(f"{self.name}@on_error", error_step=True)
        else:
            self.on_error = None

    def run_next_steps(self, ctx: ExecutionContext):
        """This function will call all `run` functions of steps in self.next_steps.

        Args:
            ctx (ExecutionContext): This is the execution context which should be passed to all steps when running them.
        """
        for step in self.next_steps:
            step.run(ctx)

    def run(self, ctx: ExecutionContext):
        """Default run function for a step.

        Args:
            ctx (ExecutionContext): Execution context needed for the steps to get informations about the pipeline.
        """
        self.status = StepStatus.COMPLETED
        self.run_next_steps(ctx)

    def get_all_steps(self, depth: int = 0):
        """Return all steps starting at this specific step.

        Args:
            depth (int, optional): Depth between the start and the actual step. Defaults to 0.

        Returns:
            list: The list of tasks
        """
        tasks = []
        for s in self.steps:
            tasks += s.get_all_steps(depth + 1)
        for s in self.next_steps:
            tasks += s.get_all_steps(
                depth + 2 if isinstance(self, ParallelStep) else depth + 1
            )
        if self.on_error is not None and (
            len(self.on_error.steps) > 0 or len(self.on_error.next_steps) > 0
        ):
            tasks += self.on_error.get_all_steps(depth + 1)
        tasks.append(
            {
                "type": self.__class__,
                "name": self.name,
                "status": self.status,
                "depth": depth,
            }
        )
        return tasks

    def show_dag(
        self,
        depth: int = 0,
        net: Network = None,
        height: str = "1000px",
        width: str = "100%",
    ):
        """Return a Pyvis Network representing the whole Pipeline.

        This is a recursive function.

        Args:
            depth (int, optional): Depth of the actual step. Defaults to 0.
            net (Network, optional): The Pyvis Network to which we need to add node. Defaults to None.

        Returns:
            Network: Pyvis Network
        """
        if net is None:
            net = Network(
                directed=True,
                notebook=True,
                bgcolor="#212121",
                font_color="#ffffff",
                layout=True,
                height=height,
                width=width,
            )
            net.toggle_physics(False)
        if isinstance(self, ParallelStep):
            node_label = "Parallel Step"
            color = status_color_rel[self.status]
        else:
            # if isinstance(self, End) or isinstance(self, Pipeline):
            color = status_color_rel[self.status]
            node_label = self.name
        if self.node_image:
            net.add_node(
                self.name,
                x=depth,
                y=0,
                level=depth,
                color=color,
                label=node_label,
                mass=self.node_mass,
                image=self.node_image,
                shape=self.node_shape,
            )
        else:
            net.add_node(
                self.name,
                x=depth,
                y=0,
                level=depth,
                color=color,
                label=node_label,
                mass=self.node_mass,
                shape=self.node_shape,
            )
        if not isinstance(self, ParallelStep):
            for step in self.next_steps:
                step.show_dag(depth=depth + 1, net=net)
                net.add_edge(self.name, step.name)
        else:
            for step in self.steps:
                step.show_dag(depth=depth + 1, net=net)
                net.add_edge(self.name, step.name)
            for step in self.next_steps:
                step.show_dag(depth=depth + 2, net=net)
                for s in self.steps:
                    net.add_edge(s.name, step.name)
        if self.on_error is not None and (
            len(self.on_error.steps) > 0 or len(self.on_error.next_steps) > 0
        ):
            self.on_error.show_dag(depth=depth + 1, net=net)
            net.add_edge(self.name, self.on_error.name)

        return net

    def __rshift__(self, other):
        """This function is used to construct the pipeline.

        Should be called like this:

        Step('One') >> Step('Two')

        Args:
            other (Step): The Step add to next steps of the `self` Step.

        Returns:
            Step: The actual Step
        """
        if isinstance(other, Step):
            self.next_steps.append(other)
            return other
        elif isinstance(other, list):
            ps = ParallelStep()
            self.next_steps.append(ps)
            for step in other:
                if isinstance(step, Step):
                    ps.steps.append(step)
                else:
                    print(f"{step} is not a valid step!")
            return ps
        else:
            print("dunno")
            print(self.__class__)
        return self

    def _repr_html_(self):
        """Generate an HTML representation of the Pyvis Network.

        Returns:
            str: Html content
        """
        net = self.show_dag()
        html_content = net.generate_html(notebook=False)
        return html_content

    def export_html(
        self,
        filename: str = "diagram_export.html",
        width: str = "100%",
        height: str = "1000px",
    ):
        net = self.show_dag(width=width, height=height)
        html_content = net.generate_html(notebook=False)
        with open(filename, "w") as f:
            f.write(html_content)


class ParallelStep(Step):
    """A specific type of step that will start all it's `Steps` in parrallel using threads.

    Args:
        Step (ParallelStep): The ParallelStep
    """

    def __init__(self, name: str = None):
        if name is None:
            name = f"ParallelStep-{str(uuid.uuid4())}"
        super().__init__(name)

        # self.node_color = '#FFFFFF'
        self.node_shape = "circularImage"
        self.node_mass = 20
        self.node_image = "parallel.png"

    def run(self, ctx: ExecutionContext):
        """Run the ParallelStep which will start Threads for each steps in it.

        Args:
            ctx (ExecutionContext): The pipeline execution context.
        """
        self.status = StepStatus.RUNNING
        processes = []
        for step in self.steps:
            p = threading.Thread(target=step.run, args=[ctx])
            processes.append(p)
            p.start()

        for p in processes:
            p.join()

        self.status = StepStatus.COMPLETED

        errored = False
        for step in self.steps:
            if step.status == StepStatus.ERRORED:
                step.on_error.run(ctx)
                errored = True

        if errored is False:
            self.run_next_steps(ctx)


class Pipeline(Step):
    """This must be the first step of the pipeline.
    It will give a lot of feedback when running the Pipeline but also setup the ExecutionContext.

    Args:
        Step (Step): The base Step class

    Raises:
        PipelineAlreadyRan: Will be raised if you rerun the pipeline while it have already ran.
    """

    monitors: [threading.Thread] = None
    execution_ctx: ExecutionContext = None

    def __init__(self, name: str = None):
        if name is None:
            name = "Start"
        super().__init__(name)

        self.node_shape = "circularImage"
        self.node_image = "start-end.png"
        self.monitors = []
        self.execution_ctx = None

    def display_pipeline(self):
        """Will display the pipeline to the current IPywidget output."""
        clear_output(wait=True)
        net = self.show_dag()
        html_content = net.generate_html(notebook=False)
        net.prep_notebook()
        display(HTML(html_content))

    def monitor_status(self):
        """Display pipeline execution status using progress bars."""
        import ipywidgets as widgets

        out = widgets.Output(layout={"border": "1px solid black"})
        display(out)
        with out:
            progress = Progress(
                TextColumn("[bold white]{task.fields[name]}", justify="right"),
                "•",
                SpinnerColumn(finished_text="Done"),
                # BarColumn(bar_width=None, style='bar.pulse'),
                "•",
                # TextColumn("[bold]{task.fields[type]}", justify="right"),
                # TextColumn("[bold]{task.fields[depth]}", justify="right"),
                TextColumn("{task.fields[status]}", justify="right"),
            )
            with progress:
                steps = self.get_all_steps()
                steps.sort(key=lambda x: x["depth"])
                task_ids = {}
                for step in steps:
                    name = (
                        step.get("name")
                        if "ParallelStep" not in step.get("name")
                        else "ParallelStep"
                    )
                    task_ids[step.get("name")] = progress.add_task(
                        step.get("name"),
                        name=name,
                        status=step.get("status").name,
                        start=False,
                        total=100,
                    )

                status_style = {
                    StepStatus.INITIALIZED: "grey",
                    StepStatus.RUNNING: "dodger_blue1",
                    StepStatus.ERRORED: "bright_red",
                    StepStatus.COMPLETED: "bright_green",
                }

                last_run = 0
                while self.status != StepStatus.COMPLETED or last_run < 2:
                    steps = self.get_all_steps()
                    steps.sort(key=lambda x: x["depth"])

                    for step in steps:
                        progress.update(
                            task_id=task_ids[step.get("name")],
                            status=f'[{status_style[step.get("status")]}] {step.get("status").name}',
                        )

                    if self.status == StepStatus.COMPLETED:
                        last_run += 1
                    time.sleep(0.2)

    def monitor_diagram(self):
        """Display pipeline execution status using HTML diagram."""
        while self.status != StepStatus.COMPLETED:
            self.display_pipeline()
            time.sleep(3)
        self.display_pipeline()

    def run(
        self,
        style: Literal["diagram", "progess"] = "diagram",
        monitor: bool = True,
        outputs_path="",
    ):
        """Start the execution of the pipeline.

        Args:
            style (Literal[&#39;diagram&#39;, &#39;progess&#39;], optional): Display style. Defaults to 'diagram'.
            monitor (bool, optional): Wether to display in live the status of the execution. Defaults to True.
            outputs_path (str, optional): Path to where we will store the outputs. Defaults to ''.

        Raises:
            PipelineAlreadyRan: Exception raised if you run the same pipeline multiple times.
        """
        if self.execution_ctx is not None:
            raise PipelineAlreadyRan("This pipeline have already been executed.")
        self.execution_ctx = ExecutionContext()
        self.status = StepStatus.RUNNING
        self.monitors = []
        if monitor is True:
            if style == "progress":
                self.monitors.append(
                    threading.Thread(target=self.monitor_status, daemon=True)
                )
            else:
                self.monitors.append(
                    threading.Thread(target=self.monitor_diagram, daemon=True)
                )
            for monitor_process in self.monitors:
                monitor_process.start()
        self.run_next_steps(self.execution_ctx)
        self.status = StepStatus.COMPLETED
        if monitor is True:
            for monitor_process in self.monitors:
                monitor_process.join()


# To make it more usable.
Start: Pipeline = Pipeline


class End(Step):
    """A visual step enhancing the representation of the Diagram view.

    This is not adding any logic.

    Args:
        Step (Step): The base Step class.
    """

    def __init__(self, name: str = None):
        if name is None:
            name = "End"
        super().__init__(name)

        # self.node_color = '#50B0FF'
        self.node_image = "start-end.png"
        self.node_shape = "circularImage"


class DummyStep(Step):
    """A dummy step that can be used to construct pipelines used for showing ideas for example.

    Args:
        Step (Step): The base Step class.
    """

    def __init__(self, name):

        super().__init__(name)
        self.output = None

    def run(self, ctx: ExecutionContext):
        self.status = StepStatus.RUNNING
        time.sleep(random.randrange(2))
        self.status = StepStatus.COMPLETED
        self.run_next_steps(ctx)


class DummyErrorStep(Step):
    """A dummy error step that will fail on purpose.

    Args:
        Step (Step): The base Step class.
    """

    def run(self, ctx: ExecutionContext):
        self.status = StepStatus.RUNNING
        time.sleep(random.randrange(3))
        self.status = StepStatus.ERRORED
        if self.on_error is not None and (
            len(self.on_error.steps) > 0 or len(self.on_error.next_steps) > 0
        ):
            self.on_error.run(ctx)
        # self.run_next_steps(ctx)


class NotebookStep(Step):
    """A Step that can be used to execute a Jupyter Notebook.

    Args:
        Step (Step): The base Step class.
    """

    notebook_path: str = None
    parameters: dict = {}

    def __init__(self, name: str, notebook_path: str, parameters: dict = {}):
        """Constructor of the NotebookStep.

        Args:
            name (str): The name of the step.
            notebook_path (str): Path to the Notebook to execute.
        """
        super().__init__(name)
        if not os.path.exists(notebook_path):
            raise Exception("Your notebook path does not exist.")
        self.notebook_path = notebook_path
        self.parameters = parameters

    def run(self, ctx: ExecutionContext):
        """This will run the Notebook and store the output using the ExecutionContext.output_path

        Args:
            ctx (ExecutionContext): Execution context containing informations about the Pipeline execution.
        """
        self.status = StepStatus.RUNNING
        try:
            sanitized_name = "".join(
                c for c in self.name if c.isalnum() or c in ("_")
            ).rstrip()

            out_file = os.path.join(
                ctx.output_path,
                f"{sanitized_name}.{os.path.basename(self.notebook_path)}",
            )
            pm.execute_notebook(
                self.notebook_path,
                out_file,
                progress_bar=False,
                parameters=self.parameters,
            )
            self.status = StepStatus.COMPLETED
        except Exception as e:
            self.status = StepStatus.ERRORED
            if not self.on_error:
                raise Exception(e)

        if self.status == StepStatus.COMPLETED:
            self.run_next_steps(ctx)
        elif self.on_error is not None and (
            len(self.on_error.steps) > 0 or len(self.on_error.next_steps) > 0
        ):
            self.on_error.run(ctx)
