import json
import sqlite3

from typing import Generator, Any
from .common import config


def get_products(conn: sqlite3.Connection) -> Generator[dict[str, Any], None, None]:
    db = conn.cursor()
    db.execute(
        """
        SELECT id, parent, name, data
        FROM entities WHERE type = 'subset'
        -- AND parent IN (SELECT id FROM entities WHERE type = 'asset')
        -- AND id IN (SELECT parent FROM entities WHERE type = 'version')
        """
    )
    for row in db.fetchall():
        subset_id = row[0]
        parent_id = row[1]
        subset_name = row[2]
        subset_data = json.loads(row[3])

        families = subset_data.pop("families", [])
        if (family := subset_data.pop("family", None)) is None:
            if families:
                family = families[0]
            else:
                family = "unknown"

        # this is a hack to make it work with OP2 projects
        # shouldn't be needed for OP3
        family = family.replace(".", "_")

        # TODO: any attributes?

        yield {
            "type": "create",
            "entityType": "product",
            "entityId": subset_id,
            "data": {
                "name": subset_name,
                "folderId": parent_id,
                "productType": family,
                "status": config.default_status,
            },
        }
