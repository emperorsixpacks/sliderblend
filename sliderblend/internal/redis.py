import json
from uuid import UUID

from meetup.utils.global_errors import FailedToCreateRedisJobError
from redis import Redis

from sliderblend.pkg import RedisSettings
from sliderblend.pkg.types import PROCESS_STATE, RedisJob


def _create_client(settings: RedisSettings):
    """Initialize Redis connection."""
    _client = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password,
        db=settings.redis_db,
        decode_responses=True,  # Ensures Redis returns strings instead of bytes
    )
    return _client


class RedisClient:
    _client = None

    def __new__(cls, settings: RedisSettings):
        if cls._client is None:
            cls._client = super(RedisClient, cls).__new__(cls)
            cls._instance = _create_client(settings)
        return cls._client

    def new_job(self, redis_job: RedisJob) -> RedisJob:
        """Creates a new job entry in Redis."""
        job_id = str(redis_job.job_id)
        job_data = redis_job.model_dump_json()

        success = self._client.set(job_id, job_data)
        if not success:
            raise FailedToCreateRedisJobError(f"Failed to create job with id {job_id}")

        return redis_job

    def get_job(self, job_id: UUID) -> RedisJob | None:
        """Retrieves a job by its ID."""
        job_data = self._client.get(str(job_id))
        if job_data is None:
            return None  # Return None if job does not exist

        job_dict = json.loads(job_data)
        return RedisJob(**job_dict)

    def update_job(self, job: RedisJob) -> RedisJob | None:
        """Updates an existing job."""
        job_id_str = str(job.job_id)
        job_data = job.model_dump_json()

        success = self._client.set(
            job_id_str, job_data
        )  # Consider using `hset` if needed
        if not success:
            return None  # Could raise a custom exception here

        return job

    def delete_job(self, job_id: UUID) -> bool:
        """Deletes a job by ID."""
        deleted_count = self._client.delete(str(job_id))
        return deleted_count > 0  # Returns True if a key was deleted

    def get_job_status(self, job_id: UUID) -> bool:
        """Checks if a job is complete."""
        job = self.get_job(job_id)
        return job.process_state if job else False

    def update_job_state(self, job_id: UUID, state: PROCESS_STATE) -> bool:
        """Updates the state of a job."""
        job = self.get_job(job_id)
        if not job:
            return False

        job.job_state = state
        return bool(self.update_job(job))
