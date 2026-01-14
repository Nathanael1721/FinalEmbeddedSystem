import requests

BASE_URL = "http://localhost:5000"

def send_log(message: str):
    try:
        # Content wird URL-kodiert automatisch von requests
        url = f"{BASE_URL}/log/add/{message}"
        r = requests.get(url, timeout=2)
    except Exception as e:
        print(f"[EXCEPTION] {e}")

def main():
    full_message = "Testnotification"
    send_log(full_message)

if __name__ == "__main__":
    main()
