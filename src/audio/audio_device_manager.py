import logging
from typing import Any

import sounddevice as sd


logger = logging.getLogger(__name__)


class AudioDeviceError(RuntimeError):
    """Errore leggibile durante l'interrogazione dei device audio."""


class AudioDeviceManager:

    def list_input_devices(self) -> list[dict[str, Any]]:
        try:
            devices = sd.query_devices()
            host_apis = sd.query_hostapis()
        except Exception as exc:
            logger.exception("Unable to enumerate audio devices")
            raise AudioDeviceError(
                "Impossibile leggere i dispositivi audio: "
                f"{exc}"
            ) from exc

        input_devices = []

        for device_id, device in enumerate(devices):
            max_input_channels = int(
                device.get("max_input_channels", 0)
            )

            if max_input_channels <= 0:
                continue

            hostapi_id = int(device.get("hostapi", -1))
            hostapi_name = self._hostapi_name(
                host_apis,
                hostapi_id,
            )

            input_devices.append(
                {
                    "id": device_id,
                    "name": str(
                        device.get("name", f"Device {device_id}")
                    ),
                    "max_input_channels": max_input_channels,
                    "default_samplerate": float(
                        device.get("default_samplerate", 0.0)
                    ),
                    "hostapi": hostapi_name,
                }
            )

        logger.debug("Input devices found: %s", input_devices)
        return input_devices

    def get_default_input_device(self) -> dict | None:
        try:
            device_id = self._default_input_id(
                sd.default.device
            )
        except Exception as exc:
            logger.exception("Unable to determine default input device")
            raise AudioDeviceError(
                "Impossibile determinare il microfono predefinito: "
                f"{exc}"
            ) from exc

        if device_id is None:
            return None

        return self.get_device(device_id)

    def get_device(self, device_id: int) -> dict | None:
        if (
            isinstance(device_id, bool)
            or not isinstance(device_id, int)
            or device_id < 0
        ):
            return None

        for device in self.list_input_devices():
            if device["id"] == device_id:
                return device

        return None

    def is_device_available(self, device_id: int) -> bool:
        return self.get_device(device_id) is not None

    @staticmethod
    def format_device_name(device: dict) -> str:
        hostapi = device.get("hostapi") or "Host API sconosciuta"
        return f"{device['name']} — {hostapi}"

    @staticmethod
    def _default_input_id(default_device: Any) -> int | None:
        if isinstance(default_device, (list, tuple)):
            default_device = default_device[0]
        else:
            try:
                default_device = default_device[0]
            except (IndexError, KeyError, TypeError):
                pass

        try:
            device_id = int(default_device)
        except (TypeError, ValueError):
            return None

        return device_id if device_id >= 0 else None

    @staticmethod
    def _hostapi_name(
        host_apis: Any,
        hostapi_id: int,
    ) -> str:
        if hostapi_id < 0:
            return "Host API sconosciuta"

        try:
            return str(
                host_apis[hostapi_id].get(
                    "name",
                    "Host API sconosciuta",
                )
            )
        except (IndexError, KeyError, TypeError):
            return "Host API sconosciuta"
