import datetime
import json
import time
from collections import deque

import yaml
from awslogs import exceptions
from awslogs.core import AWSLogs
from pydantic import BaseModel, Field, computed_field, field_validator

from lucid_log.aws_utils import parse_delta


class AWSLogConfig(BaseModel):
    """AWS Log Config"""

    log_group_name: str
    log_stream_name: str
    aws_region: str
    filter_pattern: str | None = None
    duration: str = Field(exclude=True, default="1h")

    @computed_field
    @property
    def start(self) -> str:
        """Start time"""
        return (datetime.datetime.now() - parse_delta(self.duration)).isoformat()

    @computed_field
    @property
    def end(self) -> str:
        """End time"""
        return datetime.datetime.now().isoformat()


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
                        try:
                            actual_event = json.loads(event["message"])
                            message = actual_event.pop("message", event["message"])
                            actual_event["event"] = message
                            actual_event["timestamp"] = event["timestamp"]
                            yield json.dumps(actual_event)
                        except json.JSONDecodeError:
                            actual_event = {}
                            actual_event["level"] = "Info"
                            actual_event["event"] = event["message"]
                            actual_event["timestamp"] = event["timestamp"]
                            yield json.dumps(actual_event)

                if "nextToken" in response:
                    kwargs["nextToken"] = response["nextToken"]
                else:
                    yield None
                    time.sleep(1)

        return generator()

    @classmethod
    def get_parser(cls, **kwargs):
        """Get a LucidAWSLogs instance and return the log generator."""
        # TODO Add other parameters
        logs = cls(**kwargs)
        return logs.list_logs()

    @classmethod
    def parse_config_file(cls, config_file):
        """Parse the config file and return the config."""
        # TODO Add other parameters
        if config_file:
            try:
                with open(config_file, "r") as file:
                    config_data = yaml.safe_load(file)
                    return config_data
            except FileNotFoundError:
                raise Exception(f"Error: File not found - {config_file}")
            except yaml.YAMLError as e:
                raise Exception(f"Error while parsing YAML file: {e}")
            except Exception as e:
                raise Exception(f"An unexpected error occurred: {e}")
        return {}
