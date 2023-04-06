import datetime
import json
import logging
import traceback

from collections import OrderedDict


class AppLogger:

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def _is_jsonible(self, object_type) -> bool:
        return isinstance(object_type, (list, tuple, str, int, float, bool, type(None)))

    def _format_kwargs(self, kwargs):
        _kwargs = {}
        for k, v in kwargs.items():
            if self._is_jsonible(v):
                _kwargs[k] = v
            elif isinstance(v, (set, frozenset)):
                _kwargs[k] = list(v)
            elif isinstance(v, (dict, OrderedDict)):
                _kwargs[k] = self._format_kwargs(v)
            elif isinstance(v, (datetime.datetime, datetime.date)):
                _kwargs[k] = v.isoformat()
            else:
                try:
                    _kwargs[k] = str(v)
                except Exception as e:
                    _kwargs[k] = f'format_error: {e}'
        return _kwargs

    def _format(self, msg: str, level, **kwargs):
        try:
            extras = {
                **self._format_kwargs(kwargs),
            }
            extras_json = json.dumps(extras, ensure_ascii=False, default=str)
        except Exception as e:
            extras_json = json.dumps({"logger_error": str(e)}, ensure_ascii=False)

        return json.dumps(
            {
                "app": self._logger.name,
                "timestamp": str(datetime.datetime.utcnow()),
                "event": msg,
                "level": level,
                "extra": extras_json,
            },
            ensure_ascii=False,
        )

    def critical(self, msg: str, **kwargs):
        self._logger.critical(self._format(msg, level="critical", **kwargs))

    def error(self, msg: str, **kwargs):
        self._logger.error(self._format(msg, level="error", **kwargs))

    def warning(self, msg: str, **kwargs):
        self._logger.warning(self._format(msg, level="warning", **kwargs))

    def info(self, msg: str, **kwargs):
        self._logger.info(self._format(msg, level="info", **kwargs))

    def debug(self, msg: str, **kwargs):
        self._logger.debug(self._format(msg, level="debug", **kwargs))

    def exception(self, msg: str, **kwargs):
        self._logger.error(
            self._format(
                msg,
                level="exception",
                traceback=traceback.format_exc(),
                **kwargs,
            )
        )
