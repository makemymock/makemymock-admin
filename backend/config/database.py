import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from config.settings import settings

logger = logging.getLogger(__name__)


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    questions_db: Optional[AsyncIOMotorDatabase] = None


mongo = MongoDB()


async def connect_to_mongo() -> None:
    """Initialize Motor client.

    The admin service is read-mostly: it never owns indexes (the Client
    backend owns those) but it does need its own pool. We open the primary
    `makemymock` database plus the catalog-only `bbd_db` so the questions
    module can browse the catalog directly when it lives in a separate DB.
    """
    logger.info("Connecting to MongoDB (Admin)...")
    mongo.client = AsyncIOMotorClient(
        settings.MONGO_URI,
        maxPoolSize=50,
        minPoolSize=5,
        serverSelectionTimeoutMS=5000,
        uuidRepresentation="standard",
    )
    mongo.db = mongo.client[settings.MONGO_DB_NAME]
    mongo.questions_db = mongo.client[settings.MONGO_QUESTIONS_DB_NAME]

    await mongo.client.admin.command("ping")
    logger.info("Admin MongoDB connection established.")


async def close_mongo_connection() -> None:
    if mongo.client is not None:
        logger.info("Closing MongoDB connection (Admin)...")
        mongo.client.close()
        mongo.client = None
        mongo.db = None
        mongo.questions_db = None


def get_database() -> AsyncIOMotorDatabase:
    if mongo.db is None:
        raise RuntimeError("MongoDB has not been initialized. Call connect_to_mongo().")
    return mongo.db


def get_questions_database() -> AsyncIOMotorDatabase:
    """Return the database that holds the questions catalog.

    If `MONGO_QUESTIONS_DB_NAME` matches the primary db name (single-DB
    setup), this returns the same handle as `get_database()`.
    """
    if mongo.questions_db is None:
        raise RuntimeError("Questions DB has not been initialized.")
    return mongo.questions_db
