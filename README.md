# Certificate Transparency Query Script

This script queries the [crt.sh](https://crt.sh/) API to retrieve certificate transparency logs for a list of domains. The results include details about certificates, such as the issuer, common name (CN), subject alternative names (SAN), and validity periods. It also identifies where the domain was found in the certificate (CN, SAN, or both). Additionally, the script extracts the second-level domain (SLD) from the CN field and includes it in the output.

## Features

- Queries the crt.sh API for a list of domains.
- Extracts and filters certificate details.
- Logs errors (e.g., HTTP 502/503 responses) to an error file.
- Outputs the results to a CSV file.
- Extracts the second-level domain (SLD) from the CN field.
- Automatically installs missing dependencies (`colorama`, `requests`, `tldextract`).

## Prerequisites

- Python 3.x
- Internet connection

## Installation

1. Clone this repository or copy the script to your local machine.
2. Ensure Python 3.x is installed on your system.

## Usage

1. Prepare an input file named `domains.txt` in the same directory as the script. Add one domain per line. For example:
   ```
   example.com
   test.com
   mydomain.org
   ```

2. Run the script:
   ```bash
   python script.py
   ```

3. The script will:
   - Query crt.sh for each domain.
   - Output the results to `certificate_issuers.csv`.
   - Log any errors to `error.txt`.

## Output

### CSV File
The output file `certificate_issuers.csv` contains the following columns:

- **Domain**: The queried domain.
- **Logged At**: The timestamp when the certificate was logged.
- **Issue Date**: The start date of the certificate's validity.
- **Expiry Date**: The end date of the certificate's validity.
- **CN**: The common name field from the certificate.
- **SLD**: The extracted second-level domain from the CN field.
- **SAN**: Subject alternative names from the certificate.
- **Serial Number**: The serial number of the certificate.
- **Issuer**: The name of the issuing certificate authority.
- **Details**: A clickable link to the certificate details on crt.sh.
- **Found In**: Indicates whether the domain was found in CN, SAN, or both.

### Error File
Domains that return HTTP 502 or 503 are logged in `error.txt` along with the HTTP status code.

## Notes

- The script retries failed API queries up to three times before moving to the next domain.
- Expired certificates are excluded from the results.
- The script extracts the second-level domain (SLD) from the CN field for better analysis.

## Example Output

### Input: `domains.txt`
```
example.com
test.com
mydomain.org
```

### Output: `certificate_issuers.csv`
| Domain       | Logged At           | Issue Date  | Expiry Date | CN         | SLD        | SAN               | Serial Number | Issuer               | Details                      | Found In |
|--------------|---------------------|-------------|-------------|------------|------------|-------------------|---------------|----------------------|------------------------------|----------|
| example.com  | 2023-01-01 12:34:56 | 2023-01-01  | 2024-01-01  | example.com | example.com | www.example.com   | 1234567890    | Let's Encrypt        | [crt.sh](https://crt.sh/?id=12345) | CN, SAN |
| test.com     | 2023-02-01 08:12:34 | 2023-02-01  | 2024-02-01  | a.test.com  | test.com    | www.test.com      | 0987654321    | DigiCert Inc         | [crt.sh](https://crt.sh/?id=67890) | CN      |

### Error File: `error.txt`
```
test.com returned HTTP 503
```

## Dependencies

- `requests`
- `colorama`
- `tldextract`

The script automatically installs missing dependencies.

## Troubleshooting

- **No results for a domain:** Ensure the domain has valid certificates in the crt.sh database.
- **Rate limiting issues:** Add a delay between requests or reduce the number of domains queried in one run.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

