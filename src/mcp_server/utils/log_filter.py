"""Log filtering utilities for processing container logs."""

import re
from dataclasses import dataclass
from enum import Enum


class LogLevel(str, Enum):
    """Standard log levels."""

    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"


# Patterns to detect log levels in various formats
LOG_LEVEL_PATTERNS = {
    LogLevel.TRACE: re.compile(r"\b(TRACE|trace|TRC)\b"),
    LogLevel.DEBUG: re.compile(r"\b(DEBUG|debug|DBG)\b"),
    LogLevel.INFO: re.compile(r"\b(INFO|info|INF)\b"),
    LogLevel.WARN: re.compile(r"\b(WARN|WARNING|warn|warning|WRN)\b"),
    LogLevel.ERROR: re.compile(r"\b(ERROR|error|ERR)\b"),
    LogLevel.FATAL: re.compile(r"\b(FATAL|fatal|CRITICAL|critical|FTL)\b"),
}

# Log level severity order
LOG_LEVEL_SEVERITY = {
    LogLevel.TRACE: 0,
    LogLevel.DEBUG: 1,
    LogLevel.INFO: 2,
    LogLevel.WARN: 3,
    LogLevel.ERROR: 4,
    LogLevel.FATAL: 5,
}


@dataclass
class FilterOptions:
    """Options for log filtering."""

    min_level: LogLevel | None = None
    pattern: str | None = None
    exclude_pattern: str | None = None
    case_sensitive: bool = False
    context_lines: int = 0


class LogFilter:
    """Filter and process log output."""

    def __init__(self, options: FilterOptions):
        self.options = options
        self._include_regex: re.Pattern | None = None
        self._exclude_regex: re.Pattern | None = None

        flags = 0 if options.case_sensitive else re.IGNORECASE

        if options.pattern:
            self._include_regex = re.compile(options.pattern, flags)

        if options.exclude_pattern:
            self._exclude_regex = re.compile(options.exclude_pattern, flags)

    def filter(self, log_output: str) -> str:
        """Filter log output based on options."""
        lines = log_output.splitlines()
        filtered_lines: list[str] = []
        context_buffer: list[str] = []

        for i, line in enumerate(lines):
            if self._should_include(line):
                # Add context lines before match
                if self.options.context_lines > 0:
                    for ctx_line in context_buffer[-self.options.context_lines :]:
                        if ctx_line not in filtered_lines:
                            filtered_lines.append(ctx_line)

                filtered_lines.append(line)

                # Add context lines after match
                if self.options.context_lines > 0:
                    for j in range(1, self.options.context_lines + 1):
                        if i + j < len(lines):
                            next_line = lines[i + j]
                            if next_line not in filtered_lines:
                                filtered_lines.append(next_line)
            else:
                context_buffer.append(line)
                if len(context_buffer) > self.options.context_lines:
                    context_buffer.pop(0)

        return "\n".join(filtered_lines)

    def _should_include(self, line: str) -> bool:
        """Check if a line should be included based on filters."""
        # Check exclude pattern first
        if self._exclude_regex and self._exclude_regex.search(line):
            return False

        # Check include pattern
        if self._include_regex and not self._include_regex.search(line):
            return False

        # Check log level
        if self.options.min_level:
            line_level = self._detect_log_level(line)
            if line_level:
                min_severity = LOG_LEVEL_SEVERITY[self.options.min_level]
                line_severity = LOG_LEVEL_SEVERITY[line_level]
                if line_severity < min_severity:
                    return False

        return True

    def _detect_log_level(self, line: str) -> LogLevel | None:
        """Detect log level from a log line."""
        for level, pattern in LOG_LEVEL_PATTERNS.items():
            if pattern.search(line):
                return level
        return None


def filter_logs(
    log_output: str,
    min_level: str | None = None,
    pattern: str | None = None,
    exclude_pattern: str | None = None,
    case_sensitive: bool = False,
    context_lines: int = 0,
) -> str:
    """Convenience function to filter logs."""
    options = FilterOptions(
        min_level=LogLevel(min_level) if min_level else None,
        pattern=pattern,
        exclude_pattern=exclude_pattern,
        case_sensitive=case_sensitive,
        context_lines=context_lines,
    )
    return LogFilter(options).filter(log_output)
