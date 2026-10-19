import time
import json
import os
import signal
import sys
import random
import traceback
import socket
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import database
from database import Database

WEBSITES = [
    # websites of your choice
    "https://cse.buet.ac.bd/moodle/",
    "https://google.com",
    "https://prothomalo.com",
]

TRACES_PER_SITE = 1251
FINGERPRINTING_URL = "http://localhost:5000" 
OUTPUT_PATH = "dataset.json"

# Initialize the database to save trace data reliably
database.db = Database(WEBSITES)

""" Signal handler to ensure data is saved before quitting. """
def signal_handler(sig, frame):
    print("\nReceived termination signal. Exiting gracefully...")
    try:
        database.db.export_to_json(OUTPUT_PATH)
    except:
        pass
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)


"""
Some helper functions to make your life easier.
"""

def is_server_running(host='127.0.0.1', port=5000):
    """Check if the Flask server is running."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def setup_webdriver():
    """Set up the Selenium WebDriver with Chrome options."""
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1920,1080")
    # Use the correct path to chromedriver (replace with your actual path)
    chromedriver_path = "/usr/local/bin/chromedriver"  
    # Set up the Chrome service with the path to chromedriver
    service = Service(chromedriver_path)
    # Initialize the WebDriver with the service and options
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def retrieve_traces_from_backend(driver):
    """Retrieve traces from the backend API."""
    traces = driver.execute_script("""
        return fetch('/api/get_results')
            .then(response => response.ok ? response.json() : {traces: []})
            .then(data => data.traces || [])
            .catch(() => []);
    """)
    
    count = len(traces) if traces else 0
    print(f"  - Retrieved {count} traces from backend API" if count else "  - No traces found in backend storage")
    return traces or []

def clear_trace_results(driver, wait):
    """Clear all results from the backend by pressing the button."""
    clear_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Clear all results')]")
    clear_button.click()

    wait.until(EC.text_to_be_present_in_element(
        (By.XPATH, "//div[@role='alert']"), "Cleared"))
    
def is_collection_complete():
    """Check if target number of traces have been collected."""
    current_counts = database.db.get_traces_collected()
    remaining_counts = {website: max(0, TRACES_PER_SITE - count) 
                      for website, count in current_counts.items()}
    return sum(remaining_counts.values()) == 0

"""
Your implementation starts here.
"""

def collect_single_trace(driver, wait, website_url):
    """ Implement the trace collection logic here. 
    1. Open the fingerprinting website
    2. Click the button to collect trace
    3. Open the target website in a new tab
    4. Interact with the target website (scroll, click, etc.)
    5. Return to the fingerprinting tab and close the target website tab
    6. Wait for the trace to be collected
    7. Return success or failure status
    """
    try:
        # 1. Open the fingerprinting website
        driver.get(FINGERPRINTING_URL)
        time.sleep(random.uniform(1.5, 2.5))

        # 2. Click the button to collect trace
        collect_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Collect trace')]")
        collect_button.click()

        # 3. Open the target website in a new tab
        driver.execute_script("window.open('about:blank', '_blank');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(website_url)
        time.sleep(random.uniform(2.5, 4.0))

        # 4. Interact with the target website (scroll down fixed 7 times)
        for _ in range(7):
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
            time.sleep(random.uniform(0.3, 0.8))

        # 5. Return to the fingerprinting tab and close the target website tab
        driver.switch_to.window(driver.window_handles[0])
        driver.switch_to.window(driver.window_handles[1])
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        # 6. Wait for the trace to be collected
        wait.until(EC.text_to_be_present_in_element((By.XPATH, "//div[@role='alert']"), "Trace collected"))
        time.sleep(random.uniform(0.8, 1.5))

        # Fetch traces
        traces = driver.execute_script('''
            return fetch('/download_traces')
                .then(r => r.ok ? r.json() : [])
                .catch(() => []);
        ''')

        # 7. Return success or failure status
        return (traces[-1], True) if isinstance(traces, list) and traces else (None, False)

    except Exception as e:
        print(f"Error collecting trace for {website_url}: {e}")
        traceback.print_exc()
        return None, False


def collect_fingerprints(driver, target_counts=None):
    wait = WebDriverWait(driver, 30)
    total_collected = 0
    
    for website in WEBSITES:
        current_index = 0
        # 1. Calculate the number of traces remaining for each website
        traces_to_collect = TRACES_PER_SITE
        if target_counts and website in target_counts:
            traces_to_collect = target_counts[website]

        # 3. Collect traces for each website until the target number is reached
        for trace_num in range(traces_to_collect):
            print(f"Collecting trace {trace_num + 1} / {traces_to_collect} for {website}")
            # 2. Open the fingerprinting website
            trace_data, is_successful = collect_single_trace(driver, wait, website)

            if is_successful and trace_data:
                # 4. Save the traces to the database
                database.db.save_trace(website, current_index, trace_data)

                print(f"Trace {trace_num + 1} for {website} collected successfully.")
                current_index = current_index + 1
                total_collected = total_collected + 1
            else:
                print(f"Failed to collect trace for {website} (attempt {trace_num + 1})")

    # 5. Return the total number of new traces collected
    return total_collected


def main():
    # Implement the main function to start the collection process.

    # 1. Check if the Flask server is running
    if not is_server_running():
        print("Flask server is not running.")
        return

    # 2. Initialize the database
    database.db.init_database()

    # 3. Set up the WebDriver
    driver = setup_webdriver()

    # 4. Start the collection process, continuing until the target number of traces is reached
    try:
        print("Starting fingerprint collection process...")

        total_required = sum([TRACES_PER_SITE for _ in WEBSITES])
        total_collected = 0

        # Check the collection status
        current_counts = database.db.get_traces_collected()

        # Calculate remaining traces to collect only for websites in the WEBSITES list
        remaining_counts = {
            website: max(0, TRACES_PER_SITE - current_counts.get(website, 0))
            for website in WEBSITES
        }

        # Loop to collect only the remaining traces
        while sum(remaining_counts.values()) > 0:
            print(f"Remaining traces to collect: {remaining_counts}")

            # Collect traces for each website
            collected_this_round = collect_fingerprints(driver, remaining_counts)
            total_collected += collected_this_round

            # Update remaining_counts after collecting the traces
            current_counts = database.db.get_traces_collected()
            remaining_counts = {
                website: max(0, TRACES_PER_SITE - current_counts.get(website, 0))
                for website in WEBSITES
            }

            print(f"Total collected so far: {total_collected}/{total_required}")

            # Retry if the collection is not complete
            if sum(remaining_counts.values()) > 0:
                print("Retrying to collect remaining traces...")

        print("Collection process complete.")

    except Exception as e:
        # 5. Handle any exceptions and ensure the WebDriver is closed at the end
        print(f"Error during collection: {e}")
        traceback.print_exc()

    # 6. Export the collected data to a JSON file
    finally:
        database.db.export_to_json(OUTPUT_PATH)
        driver.quit()
        print("Finished.")


if __name__ == "__main__":
    main()
