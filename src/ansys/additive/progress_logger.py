import logging

from ansys.api.additive.v0.additive_domain_pb2 import Progress, ProgressState
from tqdm import tqdm


class ProgressLogger:
    def __init__(self, name: str = None) -> None:
        self._log = logging.getLogger(name)
        self._last_percent_complete = 0
        self._last_context = "Initializing"

    def log_progress(self, progress: Progress):
        if not hasattr(self, "_pbar"):
            self._pbar = tqdm(total=100, colour="green", desc=self._last_context, mininterval=0.001)

        if progress.message and "SOLVERINFO" in progress.message:
            self._log.debug(progress.message)
            return

        if progress.state == ProgressState.PROGRESS_STATE_ERROR:
            self._pbar.write(progress.message)
            return

        if progress.context and progress.context != self._last_context:
            if "Solving Layer" not in progress.context or progress.context == "Solving Layer 1":
                self._pbar.reset(total=100)
                self._pbar.set_description(progress.context)
                self._last_context = progress.context
                self._last_percent_complete = 0
            else:
                self._pbar.set_description(progress.context, refresh=False)

        if progress.percent_complete - self._last_percent_complete > 0:
            self._pbar.update(progress.percent_complete - self._last_percent_complete)
        self._last_percent_complete = progress.percent_complete

    def __del__(self):
        if hasattr(self, "_pbar"):
            self._pbar.close()
