from collections import deque
import json
import re
from awslogs.core import AWSLogs
from awslogs import exceptions

class LucidAWSLogs(AWSLogs):
    """Lucid AWSLogs class that extends the AWSLogs class from awslogs. Returns the log generator instead of printing the logs."""

    def list_logs(self):
        streams = []
        if self.log_stream_name != self.ALL_WILDCARD:
            streams = list(self._get_streams_from_pattern(self.log_group_name, self.log_stream_name))
            if len(streams) > self.FILTER_LOG_EVENTS_STREAMS_LIMIT:
                raise exceptions.TooManyStreamsFilteredError(
                     self.log_stream_name,
                     len(streams),
                     self.FILTER_LOG_EVENTS_STREAMS_LIMIT
                )
            if len(streams) == 0:
                raise exceptions.NoStreamsFilteredError(self.log_stream_name)

        # Note: filter_log_events paginator is broken
        # ! Error during pagination: The same next token was received twice

        def generator():
            """Yield events into trying to deduplicate them using a lru queue.
            AWS API stands for the interleaved parameter that:
                interleaved (boolean) -- If provided, the API will make a best
                effort to provide responses that contain events from multiple
                log streams within the log group interleaved in a single
                response. That makes some responses return some subsequent
                response duplicate events. In a similar way when awslogs is
                called with --watch option, we need to findout which events we
                have alredy put in the queue in order to not do it several
                times while waiting for new ones and reusing the same
                next_token. The site of this queue is MAX_EVENTS_PER_CALL in
                order to not exhaust the memory.
            """
            interleaving_sanity = deque(maxlen=self.MAX_EVENTS_PER_CALL)
            kwargs = {'logGroupName': self.log_group_name,
                      'interleaved': True}

            if streams:
                kwargs['logStreamNames'] = streams

            if self.start:
                kwargs['startTime'] = self.start

            if self.end:
                kwargs['endTime'] = self.end

            if self.filter_pattern:
                kwargs['filterPattern'] = self.filter_pattern

            while True:
                response = self.client.filter_log_events(**kwargs)

                for event in response.get('events', []):
                    if event['eventId'] not in interleaving_sanity:
                        interleaving_sanity.append(event['eventId'])
                        yield json.dumps(event)

                if 'nextToken' in response:
                    kwargs['nextToken'] = response['nextToken']
                else:
                    yield None

        return generator()

def get_parser(log_group_name, log_stream_pattern, region):
    logs = LucidAWSLogs(log_group_name=log_group_name, log_stream_name=log_stream_pattern, aws_region=region)
    return logs.list_logs()
