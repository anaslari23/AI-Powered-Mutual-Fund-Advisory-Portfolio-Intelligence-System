import json
import os
from typing import Dict, Any, Optional, List


PROFILES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "profiles")


def ensure_profiles_dir():
    os.makedirs(PROFILES_DIR, exist_ok=True)


def save_profile(user_id: str, data: Dict[str, Any]) -> bool:
    try:
        ensure_profiles_dir()
        profile_path = os.path.join(PROFILES_DIR, f"{user_id}.json")
        with open(profile_path, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving profile: {e}")
        return False


def load_profile(user_id: str) -> Optional[Dict[str, Any]]:
    try:
        profile_path = os.path.join(PROFILES_DIR, f"{user_id}.json")
        if os.path.exists(profile_path):
            with open(profile_path, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading profile: {e}")
    return None


def list_profiles() -> List[str]:
    try:
        ensure_profiles_dir()
        files = os.listdir(PROFILES_DIR)
        return [f.replace(".json", "") for f in files if f.endswith(".json")]
    except Exception:
        return []


def delete_profile(user_id: str) -> bool:
    try:
        profile_path = os.path.join(PROFILES_DIR, f"{user_id}.json")
        if os.path.exists(profile_path):
            os.remove(profile_path)
            return True
    except Exception:
        pass
    return False


def profile_exists(user_id: str) -> bool:
    profile_path = os.path.join(PROFILES_DIR, f"{user_id}.json")
    return os.path.exists(profile_path)


if __name__ == "__main__":
    test_profile = {
        "name": "Test User",
        "age": 35,
        "income": 1200000,
        "risk_score": 6.5,
    }

    save_profile("test_user", test_profile)
    loaded = load_profile("test_user")
    print("Profile loaded:", loaded)
    print("All profiles:", list_profiles())
    delete_profile("test_user")
    print("Profile deleted")
