import httpx
import streamlit as st
import os
import logging

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom exception raised for API communication errors."""
    def __init__(self, message: str, status_code: int = None, response_text: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text

class APIClient:
    def __init__(self):
        self.base_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        self.api_v1 = f"{self.base_url}/api/v1"

    def _get_headers(self):
        headers = {}
        if "access_token" in st.session_state:
            headers["Authorization"] = f"Bearer {st.session_state.access_token}"
        return headers

    def register(self, email, password):
        try:
            response = httpx.post(
                f"{self.api_v1}/auth/register",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Registration failed with code {response.status_code}: {response.text}")
                return {"error": f"Registration failed ({response.status_code}): {response.text}"}
        except Exception as e:
            logger.exception("Registration exception occurred")
            return {"error": str(e)}

    def login(self, email, password):
        try:
            response = httpx.post(
                f"{self.api_v1}/auth/login",
                data={"username": email, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                st.session_state.access_token = data["access_token"]
                return data
            else:
                logger.error(f"Login failed with code {response.status_code}: {response.text}")
                return {"error": f"Login failed ({response.status_code}): {response.text}"}
        except Exception as e:
            logger.exception("Login exception occurred")
            return {"error": str(e)}

    def logout(self):
        if "access_token" in st.session_state:
            del st.session_state.access_token

    def get_sessions(self):
        try:
            response = httpx.get(f"{self.api_v1}/sessions/", headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise APIError("Session expired or authentication invalid. Please log in again.", 401)
            else:
                raise APIError(f"Failed to fetch sessions ({response.status_code}): {response.text}", response.status_code, response.text)
        except httpx.RequestError as e:
            logger.error(f"Network error fetching sessions: {e}")
            raise APIError(f"Cannot connect to the backend server: {e}")

    def create_session(self, title, dataset_id=None):
        try:
            response = httpx.post(
                f"{self.api_v1}/sessions/",
                json={"title": title, "dataset_id": dataset_id},
                headers=self._get_headers()
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise APIError("Authentication required to create a session.", 401)
            else:
                raise APIError(f"Failed to create session ({response.status_code}): {response.text}", response.status_code, response.text)
        except httpx.RequestError as e:
            logger.error(f"Network error creating session: {e}")
            raise APIError(f"Cannot connect to the backend server: {e}")

    def get_session_detail(self, session_id):
        try:
            response = httpx.get(f"{self.api_v1}/sessions/{session_id}", headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise APIError("Authentication required.", 401)
            elif response.status_code == 404:
                raise APIError("Analysis session not found.", 404)
            else:
                raise APIError(f"Failed to retrieve session details ({response.status_code}): {response.text}", response.status_code, response.text)
        except httpx.RequestError as e:
            logger.error(f"Network error retrieving session detail: {e}")
            raise APIError(f"Cannot connect to the backend server: {e}")

    def upload_dataset(self, file_content, filename):
        try:
            files = {"file": (filename, file_content, "text/csv")}
            response = httpx.post(
                f"{self.api_v1}/sessions/upload",
                files=files,
                headers=self._get_headers(),
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise APIError("Authentication required to upload datasets.", 401)
            elif response.status_code == 400:
                raise APIError(f"Invalid file format or upload rejected: {response.json().get('detail', response.text)}", 400)
            else:
                raise APIError(f"Failed to upload dataset ({response.status_code}): {response.text}", response.status_code, response.text)
        except httpx.RequestError as e:
            logger.error(f"Network error uploading dataset: {e}")
            raise APIError(f"Cannot connect to the backend server: {e}")

    def list_datasets(self):
        try:
            response = httpx.get(f"{self.api_v1}/sessions/datasets", headers=self._get_headers())
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise APIError("Authentication required.", 401)
            else:
                raise APIError(f"Failed to retrieve datasets ({response.status_code}): {response.text}", response.status_code, response.text)
        except httpx.RequestError as e:
            logger.error(f"Network error listing datasets: {e}")
            raise APIError(f"Cannot connect to the backend server: {e}")

    def query_agent(self, session_id, query):
        import time
        try:
            # 1. Start the task
            response = httpx.post(
                f"{self.api_v1}/sessions/{session_id}/query",
                json={"query": query},
                headers=self._get_headers(),
                timeout=10.0
            )
            if response.status_code == 401:
                return {"error": "Authentication required. Please log in again."}
            elif response.status_code != 200:
                return {"error": f"API returned error {response.status_code}: {response.text}"}
            
            task_id = response.json().get("task_id")
            if not task_id:
                return {"error": "No background task ID returned by the API."}

            # 2. Poll for the result
            max_attempts = 60  # Wait up to 120 seconds
            for _ in range(max_attempts):
                task_res = httpx.get(
                    f"{self.api_v1}/sessions/tasks/{task_id}",
                    headers=self._get_headers(),
                    timeout=10.0
                )
                if task_res.status_code == 200:
                    data = task_res.json()
                    if data["status"] == "completed":
                        return data["result"]
                    elif data["status"] == "failed":
                        return {"error": f"Analysis task failed: {data.get('error', 'Unknown agent error')}"}
                time.sleep(2)
            
            return {"error": "Analysis task timed out after 120 seconds."}
        except httpx.RequestError as e:
            logger.error(f"Network error querying agent: {e}")
            return {"error": f"Cannot connect to the backend server: {e}"}
        except Exception as e:
            logger.exception("General error querying agent")
            return {"error": str(e)}
