import logging
import sqlite3


def run_checks(conn: sqlite3.Connection):
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT count(id) FROM entities WHERE type = 'hero_version'
        AND source_version IS NOT NULL
        AND source_version NOT IN
            (SELECT id FROM entities WHERE type = 'version')
        """
    )
    orphaned_hero_versions = cursor.fetchone()[0]

    # get all hero versions count
    cursor.execute(
        """
        SELECT count(id) FROM entities WHERE type = 'hero_version'
        """
    )
    hero_versions = cursor.fetchone()[0]

    if orphaned_hero_versions:
        logging.warning(
            f"{orphaned_hero_versions} of {hero_versions} hero "
            "versions have no source version"
        )
