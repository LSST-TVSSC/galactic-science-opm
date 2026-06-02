import json

from tom_dataproducts.data_processor import DataProcessor
from tom_dataproducts.exceptions import InvalidFileFormatException

from custom_code.utils.vizier_sed import (
    VIZIER_SED_SOURCE_NAME,
    get_vizier_sed_payload_timestamp,
)


class VizierSEDProcessor(DataProcessor):
    def process_data(self, data_product):
        """
        Process a serialized VizieR SED JSON data product into a ReducedDatum.

        The stored JSON is expected to contain a top-level ``points`` list and
        metadata such as ``queried_at``, ``query_url``, and ``radius_arcsec``.
        """

        try:
            with open(data_product.data.path, encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise InvalidFileFormatException(f"Invalid VizieR SED JSON file: {exc}")

        if not isinstance(payload, dict):
            raise InvalidFileFormatException("VizieR SED data must be a JSON object.")

        if "points" not in payload:
            raise InvalidFileFormatException("VizieR SED JSON is missing the 'points' field.")

        timestamp = get_vizier_sed_payload_timestamp(payload)
        source_id = payload.get("source") or VIZIER_SED_SOURCE_NAME

        return [(timestamp, payload, source_id)]
