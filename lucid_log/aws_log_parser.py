import json
from collections import deque
import time

from awslogs import exceptions
from awslogs.core import AWSLogs


class LucidAWSLogs(AWSLogs):
    """Lucid AWSLogs class that extends the AWSLogs class from awslogs. Returns the log generator instead of printing the logs."""

    def list_logs(self):
        """List logs from AWS CloudWatch. Return a generator that yields logs."""
        streams = []
        if self.log_stream_name != self.ALL_WILDCARD:
            streams = list(
                self._get_streams_from_pattern(
                    self.log_group_name, self.log_stream_name
                )
            )
            if len(streams) > self.FILTER_LOG_EVENTS_STREAMS_LIMIT:
                raise exceptions.TooManyStreamsFilteredError(
                    self.log_stream_name,
                    len(streams),
                    self.FILTER_LOG_EVENTS_STREAMS_LIMIT,
                )
            if len(streams) == 0:
                raise exceptions.NoStreamsFilteredError(self.log_stream_name)

        # Note: filter_log_events paginator is broken
        # ! Error during pagination: The same next token was received twice

        def generator() -> str | None:
            """Yield events into trying to deduplicate them using a lru queue.
            This is a workaround for the broken pagination.
            The last MAX_EVENTS_PER_CALL events are kept in a queue and
            checked against the current event id. If the event id is already
            in the queue, the event is skipped.

            If no new events are found, the generator yields None and sleeps
            for 1 second before trying again.
            """
            interleaving_sanity = deque(maxlen=self.MAX_EVENTS_PER_CALL)
            kwargs = {"logGroupName": self.log_group_name, "interleaved": True}

            if streams:
                kwargs["logStreamNames"] = streams

            if self.start:
                kwargs["startTime"] = self.start

            if self.end:
                kwargs["endTime"] = self.end

            if self.filter_pattern:
                kwargs["filterPattern"] = self.filter_pattern

            while True:
                response = self.client.filter_log_events(**kwargs)

                for event in response.get("events", []):
                    if event["eventId"] not in interleaving_sanity:
                        interleaving_sanity.append(event["eventId"])
                        yield json.dumps(event)

                if "nextToken" in response:
                    kwargs["nextToken"] = response["nextToken"]
                else:
                    yield None
                    time.sleep(1)
                    
        return generator()

    @classmethod
    def get_parser(cls, log_group_name, log_stream_pattern, region):
        """Get a LucidAWSLogs instance and return the log generator."""
        # TODO Add other parameters
        logs = cls(
            log_group_name=log_group_name,
            log_stream_name=log_stream_pattern,
            aws_region=region,
        )
        return logs.list_logs()
