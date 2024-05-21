import logging
from datetime import datetime
from typing import Any, cast


from homeassistant.const import ATTR_DEVICE_ID
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import ServiceCall, callback, HomeAssistant
from .coordinator import HyundaiKiaConnectDataUpdateCoordinator
from homeassistant.helpers import device_registry
from hyundai_kia_connect_api import ClimateRequestOptions, ScheduleChargingClimateRequestOptions

from .const import DOMAIN

SERVICE_UPDATE = "update"
SERVICE_FORCE_UPDATE = "force_update"
SERVICE_LOCK = "lock"
SERVICE_UNLOCK = "unlock"
SERVICE_STOP_CLIMATE = "stop_climate"
SERVICE_START_CLIMATE = "start_climate"
SERVICE_START_CHARGE = "start_charge"
SERVICE_STOP_CHARGE = "stop_charge"
SERVICE_SET_CHARGE_LIMIT = "set_charge_limits"
SERVICE_OPEN_CHARGE_PORT = "open_charge_port"
SERVICE_CLOSE_CHARGE_PORT = "close_charge_port"
SERVICE_SCHEDULE_CHARGE_CLIMATE = "schedule_charge_climate"

SUPPORTED_SERVICES = (
    SERVICE_UPDATE,
    SERVICE_FORCE_UPDATE,
    SERVICE_LOCK,
    SERVICE_UNLOCK,
    SERVICE_STOP_CLIMATE,
    SERVICE_START_CLIMATE,
    SERVICE_START_CHARGE,
    SERVICE_STOP_CHARGE,
    SERVICE_SET_CHARGE_LIMIT,
    SERVICE_OPEN_CHARGE_PORT,
    SERVICE_CLOSE_CHARGE_PORT,
)

_LOGGER = logging.getLogger(__name__)


@callback
def async_setup_services(hass: HomeAssistant) -> bool:
    """Set up services for Hyundai Kia Connect"""

    async def async_handle_force_update(call):
        coordinator = _get_coordinator_from_device(hass, call)
        await coordinator.async_force_update_all()

    async def async_handle_update(call):
        _LOGGER.debug(f"Call:{call.data}")
        coordinator = _get_coordinator_from_device(hass, call)
        await coordinator.async_update_all()

    async def async_handle_start_climate(call):
        coordinator = _get_coordinator_from_device(hass, call)
        vehicle_id = _get_vehicle_id_from_device(hass, call)
        duration = call.data.get("duration")
        set_temp = call.data.get("temperature")
        climate = call.data.get("climate")
        heating = call.data.get("heating")
        defrost = call.data.get("defrost")
        front_left_seat = call.data.get("flseat")
        front_right_seat = call.data.get("frseat")
        rear_left_seat = call.data.get("rlseat")
        rear_right_seat = call.data.get("rrseat")

        # Confirm values are correct datatype
        if front_left_seat is not None:
            front_left_seat = int(front_left_seat)
        if front_right_seat is not None:
            front_right_seat = int(front_right_seat)
        if rear_left_seat is not None:
            rear_left_seat = int(rear_left_seat)
        if rear_right_seat is not None:
            rear_right_seat = int(rear_right_seat)

        climate_request_options = ClimateRequestOptions(
            duration=duration,
            set_temp=set_temp,
            climate=climate,
            heating=heating,
            defrost=defrost,
            front_left_seat=front_left_seat,
            front_right_seat=front_right_seat,
            rear_left_seat=rear_left_seat,
            rear_right_seat=rear_right_seat,
        )
        await coordinator.async_start_climate(vehicle_id, climate_request_options)

    async def async_handle_stop_climate(call):
        coordinator = _get_coordinator_from_device(hass, call)
        vehicle_id = _get_vehicle_id_from_device(hass, call)
        await coordinator.async_stop_climate(vehicle_id)

    async def async_handle_lock(call):
        coordinator = _get_coordinator_from_device(hass, call)
        vehicle_id = _get_vehicle_id_from_device(hass, call)
        await coordinator.async_lock_vehicle(vehicle_id)

    async def async_handle_unlock(call):
        coordinator = _get_coordinator_from_device(hass, call)
        vehicle_id = _get_vehicle_id_from_device(hass, call)
        await coordinator.async_unlock_vehicle(vehicle_id)

    async def async_handle_open_charge_port(call):
        coordinator = _get_coordinator_from_device(hass, call)
        vehicle_id = _get_vehicle_id_from_device(hass, call)
        await coordinator.async_open_charge_port(vehicle_id)

    async def async_handle_close_charge_port(call):
        coordinator = _get_coordinator_from_device(hass, call)
        vehicle_id = _get_vehicle_id_from_device(hass, call)
        await coordinator.async_close_charge_port(vehicle_id)

    async def async_handle_start_charge(call):
        coordinator = _get_coordinator_from_device(hass, call)
        vehicle_id = _get_vehicle_id_from_device(hass, call)
        await coordinator.async_start_charge(vehicle_id)

    async def async_handle_stop_charge(call):
        coordinator = _get_coordinator_from_device(hass, call)
        vehicle_id = _get_vehicle_id_from_device(hass, call)
        await coordinator.async_stop_charge(vehicle_id)

    async def async_handle_set_charge_limit(call):
        coordinator = _get_coordinator_from_device(hass, call)
        vehicle_id = _get_vehicle_id_from_device(hass, call)
        ac = call.data.get("ac_limit")
        dc = call.data.get("dc_limit")

        if ac is not None and dc is not None:
            await coordinator.set_charge_limits(vehicle_id, int(ac), int(dc))
        else:
            _LOGGER.error(
                f"{DOMAIN} - Enable to set charge limits.  Both AC and DC value required, but not provided."
            )

    async def async_handle_schedule_charge_climate(call):
        coordinator = _get_coordinator_from_device(hass, call)
        vehicle_id = _get_vehicle_id_from_device(hass, call)

        def parse_departure_options(departure_data: dict):
            departure = ScheduleChargingClimateRequestOptions.DepartureOptions()
            departure.enabled = departure_data.get('enabled')
            departure.days = departure_data.get('days')
            departure.time = datetime.strptime(departure_data.get('time'), '%I%M').time()
            return departure

        first_departure = parse_departure_options(call.data.get("first_departure"))
        second_departure = parse_departure_options(call.data.get("second_departure"))
        charging_enabled = call.data.get("charging_enabled")
        off_peak_start_time = call.data.get("off_peak_start_time")
        off_peak_end_time = call.data.get("off_peak_end_time")
        off_peak_charge_only_enabled = call.data.get("off_peak_charge_only_enabled")
        climate_enabled = call.data.get("climate_enabled")
        temperature = call.data.get("temperature")
        temperature_unit = call.data.get("temperature_unit")
        defrost = call.data.get("defrost")

        schedule_charging_climate_request_options = ScheduleChargingClimateRequestOptions(
            first_departure=ScheduleChargingClimateRequestOptions.DepartureOptions(
                enabled=first_departure.enabled,
                days=first_departure.days,
                time=first_departure.time,
            ),
            second_departure=ScheduleChargingClimateRequestOptions.DepartureOptions(
                enabled=second_departure.enabled,
                days=second_departure.days,
                time=second_departure.time,
            ),
            charging_enabled=charging_enabled,
            off_peak_start_time=off_peak_start_time,
            off_peak_end_time=off_peak_end_time,
            off_peak_charge_only_enabled=off_peak_charge_only_enabled,
            climate_enabled=climate_enabled,
            temperature=temperature,
            temperature_unit=temperature_unit,
            defrost=defrost,
        )
        await coordinator.async_schedule_charge(vehicle_id, schedule_charging_climate_request_options)

    services = {
        SERVICE_FORCE_UPDATE: async_handle_force_update,
        SERVICE_UPDATE: async_handle_update,
        SERVICE_START_CLIMATE: async_handle_start_climate,
        SERVICE_STOP_CLIMATE: async_handle_stop_climate,
        SERVICE_LOCK: async_handle_lock,
        SERVICE_UNLOCK: async_handle_unlock,
        SERVICE_START_CHARGE: async_handle_start_charge,
        SERVICE_STOP_CHARGE: async_handle_stop_charge,
        SERVICE_SET_CHARGE_LIMIT: async_handle_set_charge_limit,
        SERVICE_OPEN_CHARGE_PORT: async_handle_open_charge_port,
        SERVICE_CLOSE_CHARGE_PORT: async_handle_close_charge_port,
        SERVICE_SCHEDULE_CHARGE_CLIMATE: async_handle_schedule_charge_climate,
    }

    for service in SUPPORTED_SERVICES:
        hass.services.async_register(DOMAIN, service, services[service])
    return True


@callback
def async_unload_services(hass) -> None:
    for service in SUPPORTED_SERVICES:
        hass.services.async_remove(DOMAIN, service)


def _get_vehicle_id_from_device(hass: HomeAssistant, call: ServiceCall) -> str:
    coordinators = list(hass.data[DOMAIN].keys())
    if len(coordinators) == 1:
        coordinator = hass.data[DOMAIN][coordinators[0]]
        vehicles = coordinator.vehicle_manager.vehicles
        if len(vehicles) == 1:
            return list(vehicles.keys())[0]

    device_entry = device_registry.async_get(hass).async_get(call.data[ATTR_DEVICE_ID])
    for entry in device_entry.identifiers:
        if entry[0] == DOMAIN:
            vehicle_id = entry[1]
    return vehicle_id


def _get_coordinator_from_device(
    hass: HomeAssistant, call: ServiceCall
) -> HyundaiKiaConnectDataUpdateCoordinator:
    coordinators = list(hass.data[DOMAIN].keys())
    if len(coordinators) == 1:
        return hass.data[DOMAIN][coordinators[0]]
    else:
        device_entry = device_registry.async_get(hass).async_get(
            call.data[ATTR_DEVICE_ID]
        )
        config_entry_ids = device_entry.config_entries
        config_entry_id = next(
            (
                config_entry_id
                for config_entry_id in config_entry_ids
                if cast(
                    ConfigEntry,
                    hass.config_entries.async_get_entry(config_entry_id),
                ).domain
                == DOMAIN
            ),
            None,
        )
        config_entry_unique_id = hass.config_entries.async_get_entry(
            config_entry_id
        ).unique_id
        return hass.data[DOMAIN][config_entry_unique_id]
