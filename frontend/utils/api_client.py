import httpx
import streamlit as st
import os

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
            return response.json() if response.status_code == 200 else {"error": response.text}
        except Exception as e:
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
            return {"error": response.text}
        except Exception as e:
            return {"error": str(e)}

    def logout(self):
        if "access_token" in st.session_state:
            del st.session_state.access_token

    def get_sessions(self):
        try:
            response = httpx.get(f"{self.api_v1}/sessions/", headers=self._get_headers())
            return response.json() if response.status_code == 200 else []
        except Exception:
            return []

    def create_session(self, title, dataset_id=None):
        try:
            response = httpx.post(
                f"{self.api_v1}/sessions/",
                json={"title": title, "dataset_id": dataset_id},
                headers=self._get_headers()
            )
            return response.json() if response.status_code == 200 else None
        except Exception:
            return None

    def get_session_detail(self, session_id):
        try:
            response = httpx.get(f"{self.api_v1}/sessions/{session_id}", headers=self._get_headers())
            return response.json() if response.status_code == 200 else None
        except Exception:
            return None

    def upload_dataset(self, file_content, filename):
        try:
            files = {"file": (filename, file_content, "text/csv")}
            response = httpx.post(
                f"{self.api_v1}/sessions/upload",
                files=files,
                headers=self._get_headers()
            )
            return response.json() if response.status_code == 200 else None
        except Exception:
            return None

    def list_datasets(self):
        try:
            response = httpx.get(f"{self.api_v1}/sessions/datasets", headers=self._get_headers())
            return response.json() if response.status_code == 200 else []
        except Exception:
            return []

    def query_agent(self, session_id, query):
        try:
            response = httpx.post(
                f"{self.api_v1}/sessions/{session_id}/query",
                json={"query": query},
                headers=self._get_headers(),
                timeout=60.0 # Agent tasks might take time
            )
            return response.json() if response.status_code == 200 else {"error": response.text}
        except Exception as e:
            return {"error": str(e)}
