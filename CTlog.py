import requests
import json
import csv
import datetime
import subprocess
import sys
import tldextract

# Ensure `tldextract` is installed
try:
    import tldextract
except ImportError:
    print("tldextract module not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tldextract"])
    import tldextract

# Check and install colorama if not installed
try:
    from colorama import Fore, Style
except ImportError:
    print("Colorama not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama"])
    from colorama import Fore, Style

# Ensure requests is installed
try:
    import requests
except ImportError:
    print("Requests library not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

# Input and output file paths
INPUT_FILE = "domains.txt"
OUTPUT_FILE = "certificate_issuers.csv"
ERROR_FILE = "error.txt"

# Function to remove duplicate serial numbers but keep empty ones
def remove_duplicate_serial_numbers(records):
    unique_records = []
    seen_serials = set()
    for record in records:
        serial = record.get("Serial Number", "")
        if serial:  # Only deduplicate if serial number is not empty
            if serial not in seen_serials:
                seen_serials.add(serial)
                unique_records.append(record)
        else:
            unique_records.append(record)  # Keep all records with empty serial numbers
    return unique_records

# Function to extract the second-level domain (SLD)
def extract_sld(domain_name):
    extracted = tldextract.extract(domain_name)
    return f"{extracted.domain}.{extracted.suffix}" if extracted.suffix else extracted.domain

# Function to ensure "Not Found" and "Error" entries are added
def ensure_output_entry(domain, found_status):
    return {
        "Domain": domain,
        "Logged At": "",
        "Issue Date": "",
        "Expiry Date": "",
        "CN": "",
        "SLD": "",
        "SAN": "",
        "Serial Number": "",
        "Issuer": "",
        "Details": "",
        "Found In": found_status
    }

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
def extract_active_cert_details(certificates, domain):
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
                    "Domain": domain,
                    "Logged At": cert.get('entry_timestamp', ''),
                    "Issue Date": not_before,
                    "Expiry Date": not_after,
                    "CN": common_name,
                    "SLD": extract_sld(common_name),
                    "SAN": ", ".join(identities),
                    "Serial Number": serial_number,
                    "Issuer": cert['issuer_name'],
                    "Details": crt_sh_link,
                    "Found In": ", ".join(found_in)
                })
    return active_cert_details

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
        active_cert_details = extract_active_cert_details(certificates, domain)

        if active_cert_details:
            print(f"Found {len(active_cert_details)} active certificate(s) for domain: {domain}")
            for cert_detail in active_cert_details:
                results.append({
                    "Domain": cert_detail['Domain'],
                    "Logged At": cert_detail['Logged At'],
                    "Issue Date": cert_detail['Issue Date'],
                    "Expiry Date": cert_detail['Expiry Date'],
                    "CN": cert_detail['CN'],
                    "SLD": cert_detail['SLD'],
                    "SAN": cert_detail['SAN'],
                    "Serial Number": cert_detail['Serial Number'],
                    "Issuer": cert_detail['Issuer'],
                    "Details": cert_detail['Details'],
                    "Found In": cert_detail['Found In']
                })
                successful_writes += 1
        else:
            print(f"No active certificates found for domain: {domain}, marking as 'Not Found' in output.")
            results.append(ensure_output_entry(domain, "Not Found"))
            unsuccessful_writes += 1

    # Remove duplicate serial numbers before saving, but keep empty ones
    results = remove_duplicate_serial_numbers(results)

    # Write results to a CSV file
    with open(OUTPUT_FILE, "w", newline="") as csvfile:
        fieldnames = ["Domain", "Logged At", "Issue Date", "Expiry Date", "CN", "SLD", "SAN", "Serial Number", "Issuer", "Details", "Found In"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(results)

    print(f"Results saved to {OUTPUT_FILE}")
    print(f"Number of successful writes: {successful_writes}")
    print(f"Number of unsuccessful writes: {unsuccessful_writes}")
