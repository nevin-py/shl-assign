"""
Keep-Alive Script for Render Free Tier Services
Pings backend and frontend every 10 minutes to prevent spin-down
"""

import requests
import time
from datetime import datetime
import sys

# Service URLs
BACKEND_URL = "https://backend-3snj.onrender.com"
FRONTEND_URL = "https://fontend-s557.onrender.com"

# Ping interval in seconds (10 minutes)
PING_INTERVAL = 10 * 60


def ping_service(url, service_name):
    """Ping a service and return status"""
    try:
        start_time = time.time()
        response = requests.get(f"{url}/health" if "backend" in url else url, timeout=30)
        elapsed = time.time() - start_time
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if response.status_code == 200:
            print(f"[{timestamp}] ✅ {service_name}: OK (Status: {response.status_code}, Time: {elapsed:.2f}s)")
            return True
        else:
            print(f"[{timestamp}] ⚠️  {service_name}: Status {response.status_code} (Time: {elapsed:.2f}s)")
            return False
            
    except requests.exceptions.Timeout:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] ⏱️  {service_name}: Timeout after 30s")
        return False
        
    except requests.exceptions.RequestException as e:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] ❌ {service_name}: Error - {str(e)}")
        return False


def main():
    """Main keep-alive loop"""
    print("=" * 80)
    print("🔄 Render Keep-Alive Service Started")
    print("=" * 80)
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Frontend URL: {FRONTEND_URL}")
    print(f"Ping Interval: {PING_INTERVAL / 60:.0f} minutes")
    print("=" * 80)
    print("\nPress Ctrl+C to stop\n")
    
    ping_count = 0
    
    try:
        while True:
            ping_count += 1
            print(f"\n{'='*80}")
            print(f"Ping #{ping_count}")
            print(f"{'='*80}")
            
            # Ping backend
            backend_ok = ping_service(BACKEND_URL, "Backend API")
            
            # Ping frontend
            frontend_ok = ping_service(FRONTEND_URL, "Frontend UI")
            
            # Summary
            status = "✅ All services OK" if (backend_ok and frontend_ok) else "⚠️  Some services down"
            print(f"\nStatus: {status}")
            
            # Wait for next ping
            next_ping = datetime.now().timestamp() + PING_INTERVAL
            next_ping_time = datetime.fromtimestamp(next_ping).strftime("%Y-%m-%d %H:%M:%S")
            print(f"Next ping at: {next_ping_time}")
            
            time.sleep(PING_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("🛑 Keep-Alive Service Stopped")
        print(f"Total pings sent: {ping_count}")
        print("="*80)
        sys.exit(0)


if __name__ == "__main__":
    main()
