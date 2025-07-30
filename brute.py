import requests
import argparse
from urllib.parse import urlparse
import os
import concurrent.futures

def validate_url(url):
    # If URL doesn't contain a scheme, prepend the default 'https://'
    # If URL isn't in a valid format, let the user know and exit
    parsedURL = urlparse(url)
    if not parsedURL.scheme:
        tempURL = "https://" + url
        if not urlparse(tempURL).netloc:
            print(f"{url} is not a valid URL (e.g. google.com)")
            exit()
        return tempURL
    elif not parsedURL.netloc:
        print(f"{url} is not a valid URL (e.g. google.com)")
        exit()
    return url

def get_status(line, targURL):
    # Make a request to the targetURL with the current word from the wordlist appended
    # If successful, return the URL and status code to be handled in the main thread
    # If not successful, raise an error to be handled in the main thread
    try:
        line = line.strip()
        testURL = targURL + "/" + str(line)
        response = requests.get(testURL, timeout=5)
        return testURL, response.status_code
    except requests.exceptions.ConnectionError:
        raise ConnectionError(f"Could not connect to '{testURL}'. Please ensure the URL exists.\n")
    except requests.exceptions.Timeout:
        raise TimeoutError(f"Request to '{testURL}' timed out.\n")
    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(f"An unexpected error occured while checking '{testURL}': {e}\n")
    except Exception as e:
        raise Exception(f"An unknown error occured: {e}\n")

# Define parser object
parser = argparse.ArgumentParser(
    description="A simple program to brute force web directories from a provided wordlist.", formatter_class=argparse.RawTextHelpFormatter)

# Add required arguments to parser object
parser.add_argument("-t", "--target", required=True, help="The target URL.\nIf no schema is supplied, 'https://' will be used as the default.")
parser.add_argument("-w", "--wordlist", required=True, help="The path to the wordlist.")

# Parse inputted arguments
args = parser.parse_args()
# Assign args to variables
targURL = validate_url(args.target)
wordlist = args.wordlist

# Ensure there's a valid path to wordlist
if not os.path.exists(wordlist):
    print(f"File not found: {wordlist}")
    exit()

# Define the thread pool
pool = concurrent.futures.ThreadPoolExecutor(max_workers=2*os.cpu_count()+1)
futures = []

# Calculate the longest word in the wordlist
# So indentation of status code can be standardised
max_len=-1
with open(wordlist, "r") as f:
    for line in f.readlines():
        max_len=max(max_len, len(line.strip()))
    if max_len > 0:
        max_len += len(targURL) + 1
    else:
        print("Wordlist is malformed")
        exit()

# New thread for each word in wordlist that tries to connect to the targetURL
print("Found URLs:\n")
with open(wordlist, "r") as f:
    for line in f.readlines():
        futures.append(pool.submit(get_status, line, targURL))

alignment_val = max_len + 6
# As threads complete
for future in concurrent.futures.as_completed(futures):
    try:
        # Get the output (incl. any errors) from the thread
        # Show output
        resURL, status_code = future.result()
        if status_code != 404:
            pad_num = alignment_val - len(resURL)
            print(f"{resURL}{' ' * pad_num}Status code: {status_code}\n")
    except ConnectionError as e:
        print(f"{e}")
    except TimeoutError as e:
        print(f"{e}")
    except requests.exceptions.RequestException as e:
        print(f"{e}")
    except Exception as e:
        print(f"{e}")

pool.shutdown(wait=True)
print("------------\nScan Complete\n------------")