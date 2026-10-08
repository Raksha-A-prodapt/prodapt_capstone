import requests

from pathlib import Path
import sys

# try2/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from config.llm_config import (
    OPENROUTER_MODEL,
    OPENROUTER_API_KEYS,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
    LLM_TIMEOUT,
)


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def test_api_key(api_key, key_number):
    """
    Test one OpenRouter API key independently.
    """

    print("\n" + "=" * 60)
    print(f"TESTING API KEY {key_number}")
    print("=" * 60)

    print(f"Model: {OPENROUTER_MODEL}")
    print(f"Key: {api_key[:8]}...{api_key[-4:]}")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Telecom Network RAG",
    }

    payload = {
        "model": OPENROUTER_MODEL,

        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a simple test assistant. "
                    "Reply briefly to the user's message."
                ),
            },
            {
                "role": "user",
                "content": (
                    "This is a test message. "
                    "Reply with: LLM test successful."
                ),
            },
        ],

        "temperature": LLM_TEMPERATURE,
        "max_tokens": LLM_MAX_TOKENS,
    }

    try:

        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=LLM_TIMEOUT,
        )

        print(f"HTTP Status: {response.status_code}")

        # -------------------------------------------------
        # HTTP ERROR
        # -------------------------------------------------

        if not response.ok:

            print("STATUS: FAILED")

            try:
                error_data = response.json()
                print("OpenRouter Error:")
                print(error_data)

            except ValueError:
                print("Response:")
                print(response.text)

            return False

        # -------------------------------------------------
        # PARSE RESPONSE
        # -------------------------------------------------

        try:
            data = response.json()

        except ValueError:
            print("STATUS: FAILED")
            print("Reason: Response was not valid JSON.")
            print("Raw response:")
            print(response.text)

            return False

        # -------------------------------------------------
        # CHECK RESPONSE STRUCTURE
        # -------------------------------------------------

        try:
            answer = data["choices"][0]["message"]["content"]

        except (KeyError, IndexError, TypeError) as e:

            print("STATUS: FAILED")
            print("Reason: Unexpected response structure.")
            print(f"Error: {e}")

            print("\nFull response:")
            print(data)

            return False

        # -------------------------------------------------
        # CHECK EMPTY RESPONSE
        # -------------------------------------------------

        if not answer or not answer.strip():

            print("STATUS: FAILED")
            print("Reason: LLM returned an EMPTY response.")

            print("\nFull response:")
            print(data)

            return False

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        print("STATUS: SUCCESS")
        print("\nLLM Response:")
        print(answer.strip())

        return True

    except requests.exceptions.Timeout:

        print("STATUS: FAILED")
        print("Reason: Request timed out.")

        return False

    except requests.exceptions.ConnectionError as e:

        print("STATUS: FAILED")
        print("Reason: Connection error.")
        print(f"Error: {e}")

        return False

    except requests.exceptions.RequestException as e:

        print("STATUS: FAILED")
        print("Reason: Request error.")
        print(f"Error: {e}")

        return False

    except Exception as e:

        print("STATUS: FAILED")
        print("Reason: Unexpected error.")
        print(f"Error: {e}")

        return False


def main():

    print("\n")
    print("=" * 60)
    print("       OPENROUTER API KEY TEST")
    print("=" * 60)

    # -----------------------------------------------------
    # CHECK API KEYS
    # -----------------------------------------------------

    if not OPENROUTER_API_KEYS:

        print("\nERROR: No OpenRouter API keys found.")

        return

    print(f"\nModel: {OPENROUTER_MODEL}")
    print(f"Total API keys configured: {len(OPENROUTER_API_KEYS)}")

    successful_keys = []
    failed_keys = []

    # -----------------------------------------------------
    # TEST EACH KEY
    # -----------------------------------------------------

    for index, api_key in enumerate(
        OPENROUTER_API_KEYS,
        start=1
    ):

        success = test_api_key(
            api_key,
            index
        )

        if success:

            successful_keys.append(index)

        else:

            failed_keys.append(index)

    # -----------------------------------------------------
    # FINAL SUMMARY
    # -----------------------------------------------------

    print("\n")
    print("=" * 60)
    print("                 TEST SUMMARY")
    print("=" * 60)

    print(
        f"\nTotal keys tested : {len(OPENROUTER_API_KEYS)}"
    )

    print(
        f"Working keys      : {len(successful_keys)}"
    )

    print(
        f"Failed keys       : {len(failed_keys)}"
    )

    if successful_keys:

        print(
            f"\nWorking key numbers: {successful_keys}"
        )

    if failed_keys:

        print(
            f"Failed key numbers : {failed_keys}"
        )

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()