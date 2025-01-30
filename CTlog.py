
#import tldextract

#def extract_sld(domain_name):
#    extracted = tldextract.extract(domain_name)
#    return f"{extracted.domain}.{extracted.suffix}" if extracted.suffix else extracted.domain

#This script queries the crt.sh API to retrieve certificate transparency logs for a list of domains. 
#The results include details about certificates, such as the issuer, common name (CN), subject alternative names (SAN), 
#and validity periods. It also identifies where the domain was found in the certificate (CN, SAN, or both).


import requests
import json
import csv
import datetime
import subprocess
import sys

# Check and install colorama if not installed
try:
    from colorama import Fore, Style
except ImportError:
    print("Colorama not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama"])
    from colorama import Fore, Style

# Check and install requests if not installed
try:
    import requests
except ImportError:
    print("Requests library not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

#check and install tldextract if not installed
try:
    import tldextract
except ImportError:
    print("tldextract module not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tldextract"])
    import tldextract

# Input and output file paths
INPUT_FILE = "domains.txt"
OUTPUT_FILE = "certificate_issuers.csv"
ERROR_FILE = "error.txt"

# Function to query crt.sh for certificates of a given domain
def query_certificates(domain):
    url = f"https://crt.sh/?q={domain}&output=json"
    for attempt in range(3):  # Retry up to 3 times
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            elif response.status_code in [502, 503]:
                with open(ERROR_FILE, "a") as error_file:
                    error_file.write(f"{domain} returned HTTP {response.status_code}\n")
                print(f"{Fore.RED}Domain {domain} returned HTTP {response.status_code}{Style.RESET_ALL}")
                return []
            else:
                print(f"{Fore.RED}Attempt {attempt + 1}: Failed to fetch data for domain {domain}: HTTP {response.status_code}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Attempt {attempt + 1}: Error querying crt.sh for domain {domain}: {e}{Style.RESET_ALL}")
        if attempt < 2:
            print(f"Retrying for domain {domain}...")
    print(f"{Fore.RED}All attempts failed for domain {domain}. Continuing with the next domain.{Style.RESET_ALL}")
    return []

# Function to filter active certificates and extract details
def extract_active_cert_details(certificates):
    active_cert_details = []
    current_date = datetime.datetime.utcnow()
    for cert in certificates:
        if 'not_after' in cert:
            not_after = datetime.datetime.strptime(cert['not_after'], "%Y-%m-%dT%H:%M:%S")
            if not_after > current_date:  # Exclude expired certificates
                not_before = datetime.datetime.strptime(cert['not_before'], "%Y-%m-%dT%H:%M:%S") if 'not_before' in cert else None
                common_name = cert.get('common_name', '')
                identities = cert.get('name_value', '').split("\n")
                crt_sh_id = cert.get('id', '')
                crt_sh_link = f"https://crt.sh/?id={crt_sh_id}" if crt_sh_id else ""
                serial_number = cert.get('serial_number', '')
                found_in = []
                if domain in common_name:
                    found_in.append("CN")
                if any(domain in san for san in identities):
                    found_in.append("SAN")
                active_cert_details.append({
                    "domain": domain,
                    "logged_at": cert.get('entry_timestamp', ''),
                    "not_before": not_before,
                    "not_after": not_after,
                    "common_name": common_name,
                    "identities": ", ".join(identities),
                    "serial_number": serial_number,
                    "issuer": cert['issuer_name'],
                    "crt_sh_id": crt_sh_link,
                    "found_in": ", ".join(found_in)
                })
    return active_cert_details

def extract_sld(domain_name):
    extracted = tldextract.extract(domain_name)
    return f"{extracted.domain}.{extracted.suffix}" if extracted.suffix else extracted.domain

# Main script
if __name__ == "__main__":
    with open(INPUT_FILE, "r") as file:
        domains = [line.strip() for line in file.readlines()]

    results = []
    successful_writes = 0
    unsuccessful_writes = 0

    for domain in domains:
        print(f"Querying certificates for domain: {domain}")
        certificates = query_certificates(domain)
        active_cert_details = extract_active_cert_details(certificates)

        if active_cert_details:
            print(f"Found {len(active_cert_details)} active certificate(s) for domain: {domain}")
            for cert_detail in active_cert_details:
                results.append({
                    "Domain": cert_detail['domain'],
                    "Logged At": cert_detail['logged_at'],
                    "Issue Date": cert_detail['not_before'],
                    "Expiry Date": cert_detail['not_after'],
                    "CN": cert_detail['common_name'],
                    "SLD": extract_sld(cert_detail['common_name']),
                    "SAN": cert_detail['identities'],
                    "Serial Number": cert_detail['serial_number'],
                    "Issuer": cert_detail['issuer'],
                    "Details": cert_detail['crt_sh_id'],
                    "Found In": cert_detail['found_in']
                })
                successful_writes += 1
        else:
            print(f"No active certificates found for domain: {domain}")
            results.append({
                "Domain": domain,
                "Logged At": "",
                "Issue Date": "",
                "Expiry Date": "",
                "CN": "",
                "SAN": "",
                "Serial Number": "",
                "Issuer": "",
                "Details": "",
                "Found In": ""
            })
            unsuccessful_writes += 1

    # Write results to a CSV file
    with open(OUTPUT_FILE, "w", newline="") as csvfile:
        fieldnames = ["Domain", "Logged At", "Issue Date", "Expiry Date", "CN", "SLD", "SAN", "Serial Number", "Issuer", "Details", "Found In"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(results)

    print(f"Results saved to {OUTPUT_FILE}")
    print(f"Number of successful writes: {successful_writes}")
    print(f"Number of unsuccessful writes: {unsuccessful_writes}")
