"""Account input preparation even when a normal mapper deadline cancels it."""
from concurrent.futures import CancelledError
from contextlib import contextmanager
import time

from mapper_execution_guard import MappingBoundaryReached


@contextmanager
def input_preparation(runtime, arrival, timing, *, start, clock=time.monotonic,
                      synchronize=lambda: None):
    try:
        yield
    except (MappingBoundaryReached, CancelledError) as error:
        runtime.worker.raise_on_error()
        guard = runtime.guard
        report = guard.report()
        # A close race is expected only at the actual deadline admission
        # boundary. An early close or a worker failure remains an error.
        deadline_reached = (guard.deadline is not None
                            and clock() >= guard.deadline - guard.reserve_seconds)
        deadline_rejected = any(r['reason'] == 'deadline' for r in report['rejections'])
        if not (deadline_reached and (runtime.worker.report()['closed'] or deadline_rejected)):
            raise
        runtime.close()
        arrival['preparation_cancelled'] = str(error) or type(error).__name__
    finally:
        # Packet copies may have been queued before submit rejected the packet.
        # Their completion belongs to the mapping budget, including on failure.
        try:
            synchronize()
        finally:
            timing['end'] = clock()
            arrival['preparation_finished_seconds'] = timing['end'] - start
