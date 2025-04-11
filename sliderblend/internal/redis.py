import json
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar
from uuid import UUID

from coredis import Redis

from sliderblend.pkg import RedisSettings
from sliderblend.pkg.types import Error, Job, error

T = TypeVar("T")


def _create_client(settings: RedisSettings):
    """Initialize Redis connection."""
    client = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        username=settings.redis_username,
        password=settings.redis_password,
        decode_responses=True,  # Ensures Redis returns strings instead of bytes
    )
    return client


class RedisClient:
    _client = None

    def __new__(cls, settings: Any):
        if cls._client is None:
            cls._client = super(RedisClient, cls).__new__(cls)
            cls._instance = _create_client(settings)  # Connect to Redis
        return cls._client

    def create(self, key: str, data: Any) -> Tuple[bool, error]:
        """
        Create a new object in Redis.

        Args:
            key: The unique identifier/key for the object
            data: The data to store (will be JSON serialized)

        Returns:
            Tuple[bool, error]: Tuple containing success status and error (if any)
        """
        if isinstance(data, dict) or hasattr(data, "model_dump_json"):
            serialized_data = (
                data.model_dump_json()
                if hasattr(data, "model_dump_json")
                else json.dumps(data)
            )
            success = self._instance.set(key, serialized_data)
            return success, None
        return None, Error("Data must be a dictionary or have model_dump_json method")

    def batch_create(self, items: Dict[str, Any]) -> List[bool]:
        """
        Create multiple objects in a batch operation.

        Args:
            items: Dictionary mapping keys to their data objects

        Returns:
            List[bool]: List of success results for each operation
        """
        pipe = self._instance.pipeline()

        for key, data in items.items():
            serialized_data = (
                data.model_dump_json()
                if hasattr(data, "model_dump_json")
                else json.dumps(data)
            )
            pipe.set(key, serialized_data)

        return pipe.execute()

    def retrieve(
        self, key: str, object_class: Type[T] = None
    ) -> Tuple[Optional[T], error]:
        """
        Retrieve an object from Redis.

        Args:
            key: The unique identifier/key for the object
            object_class: Optional class to deserialize the data into

        Returns:
            Tuple[Optional[T], error]: Tuple containing the retrieved object (or None) and error (if any)
        """
        data = self._instance.get(key)

        if data is None:
            return None, Error("Not found")

        deserialized_data = json.loads(data)

        if object_class:
            return object_class(**deserialized_data), None
        return deserialized_data, None

    def retrieve_many(
        self, keys: List[str], object_class: Type[T] = None
    ) -> List[Optional[T]]:
        """
        Retrieve multiple objects from Redis.

        Args:
            keys: List of keys to retrieve
            object_class: Optional class to deserialize the data into

        Returns:
            List[Optional[T]]: List of retrieved objects (None for keys that don't exist)
        """
        pipe = self._instance.pipeline()

        for key in keys:
            pipe.get(key)

        results = pipe.execute()
        objects = []

        for data in results:
            if data is None:
                objects.append(None)
            else:
                deserialized_data = json.loads(data)
                if object_class:
                    objects.append(object_class(**deserialized_data))
                else:
                    objects.append(deserialized_data)

        return objects

    def retrieve_all(self, pattern: str = "*", object_class: Type[T] = None) -> List[T]:
        """
        Retrieve all objects matching a pattern.

        Args:
            pattern: Redis key pattern to match
            object_class: Optional class to deserialize the data into

        Returns:
            List[T]: List of retrieved objects
        """
        keys = self._instance.keys(pattern)
        return self.retrieve_many(keys, object_class) if keys else []

    def update(self, key: str, data: Any) -> Tuple[bool, error]:
        """
        Update an existing object in Redis.

        Args:
            key: The unique identifier/key for the object
            data: The new data to store

        Returns:
            Tuple[bool, error]: Tuple containing success status and error (if any)
        """
        return self.create(key, data)  # Using create since Redis SET replaces

    def batch_update(self, items: Dict[str, Any]) -> List[bool]:
        """
        Update multiple objects in a batch operation.

        Args:
            items: Dictionary mapping keys to their updated data

        Returns:
            List[bool]: List of success results for each operation
        """
        return self.batch_create(items)  # Same as batch create since SET replaces

    def delete(self, key: str) -> bool:
        """
        Delete an object from Redis.

        Args:
            key: The unique identifier/key for the object

        Returns:
            bool: True if deletion was successful
        """
        deleted_count = self._instance.delete(key)
        return deleted_count > 0

    def delete_many(self, keys: List[str]) -> int:
        """
        Delete multiple objects from Redis.

        Args:
            keys: List of keys to delete

        Returns:
            int: Number of objects successfully deleted
        """
        if not keys:
            return 0

        return self._instance.delete(*keys)

    def delete_all(self, pattern: str = "*") -> int:
        """
        Delete all objects matching a pattern.

        Args:
            pattern: Redis key pattern to match

        Returns:
            int: Number of objects deleted
        """
        keys = self._instance.keys(pattern)
        if not keys:
            return 0

        return self._instance.delete(*keys)


class Jobs(RedisClient):
    """Class to manage job objects in Redis, inheriting from RedisClient."""

    def __init__(self, settings: Any):
        """Initialize the Jobs client."""
        super().__new__(self.__class__, settings)
        self.job_prefix = "job:"

    def create_job(self, redis_job: Job) -> Tuple[Optional[Job], error]:
        """
        Create a new job in Redis.

        Args:
            redis_job: The job object to create

        Returns:
            Tuple[Optional[Job], error]: Tuple containing the created job (or None) and error (if any)
        """
        job_id = str(redis_job.job_id)
        key = f"{self.job_prefix}{job_id}"
        _, err = self.create(key, redis_job)

        if err:
            return None, err

        return redis_job, None

    def get_job(self, job_id: UUID) -> Tuple[Optional[Job], error]:
        """
        Retrieve a job by its ID.

        Args:
            job_id: The unique identifier of the job

        Returns:
            Tuple[Optional[Job], error]: Tuple containing the job (or None) and error (if any)
        """
        key = f"{self.job_prefix}{str(job_id)}"
        return self.retrieve(key, Job)

    def get_jobs(self, job_ids: List[UUID]) -> List[Optional[Job]]:
        """
        Retrieve multiple jobs by their IDs.

        Args:
            job_ids: List of job IDs to retrieve

        Returns:
            List[Optional[Job]]: List of jobs (None for IDs that don't exist)
        """
        keys = [f"{self.job_prefix}{str(job_id)}" for job_id in job_ids]
        return self.retrieve_many(keys, Job)

    def get_all_jobs(self) -> List[Job]:
        """
        Retrieve all jobs.

        Returns:
            List[Job]: List of all jobs
        """
        pattern = f"{self.job_prefix}*"
        return self.retrieve_all(pattern, Job)

    def update_job(self, job: Job) -> Tuple[bool, error]:
        """
        Update an existing job.

        Args:
            job: The job with updated data

        Returns:
            Tuple[bool, error]: Tuple containing success status and error (if any)
        """
        job_id = str(job.job_id)
        key = f"{self.job_prefix}{job_id}"
        return self.update(key, job)

    def delete_job(self, job_id: UUID) -> bool:
        """
        Delete a job by its ID.

        Args:
            job_id: The unique identifier of the job

        Returns:
            bool: True if deletion was successful
        """
        key = f"{self.job_prefix}{str(job_id)}"
        return self.delete(key)

    def delete_jobs(self, job_ids: List[UUID]) -> int:
        """
        Delete multiple jobs by their IDs.

        Args:
            job_ids: List of job IDs to delete

        Returns:
            int: Number of jobs successfully deleted
        """
        keys = [f"{self.job_prefix}{str(job_id)}" for job_id in job_ids]
        return self.delete_many(keys)

    def get_jobs_by_state(self, state: str) -> List[Job]:
        """
        Get all jobs with a specific state.

        Args:
            state: The state value to filter by

        Returns:
            List[Job]: List of jobs with the specified state
        """
        all_jobs = self.get_all_jobs()
        return [job for job in all_jobs if job.job_state == state]

    def count_jobs_by_state(self) -> Dict[Any, int]:
        """
        Count jobs by their state.

        Returns:
            Dict[Any, int]: Dictionary mapping states to counts
        """
        all_jobs = self.get_all_jobs()
        counts = {}

        for job in all_jobs:
            state = job.job_state
            counts[state] = counts.get(state, 0) + 1

        return counts
