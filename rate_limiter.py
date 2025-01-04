from datetime import datetime, timedelta
import time
from collections import defaultdict
import threading

class RateLimiter:
    def __init__(self):
        self.locks = defaultdict(threading.Lock)
        self.rates = {
            "pubmed": {"calls": 3, "period": 1},      # 3 calls per second
            "uptodate": {"calls": 100, "period": 60}, # 100 calls per minute
            "medscape": {"calls": 50, "period": 60},  # 50 calls per minute
            "clinicaltrials": {"calls": 10, "period": 1}  # 10 calls per second
        }
        self.request_timestamps = defaultdict(list)

    async def wait_if_needed(self, api_name):
        """Check if we need to wait before making another API call"""
        with self.locks[api_name]:
            now = datetime.now()
            # Remove timestamps older than the rate limit period
            period = self.rates[api_name]["period"]
            cutoff = now - timedelta(seconds=period)
            
            self.request_timestamps[api_name] = [
                ts for ts in self.request_timestamps[api_name] 
                if ts > cutoff
            ]
            
            # If we've hit the rate limit, wait
            if len(self.request_timestamps[api_name]) >= self.rates[api_name]["calls"]:
                oldest_timestamp = min(self.request_timestamps[api_name])
                wait_time = (oldest_timestamp + timedelta(seconds=period) - now).total_seconds()
                if wait_time > 0:
                    time.sleep(wait_time)
                    # Clear old timestamps after waiting
                    self.request_timestamps[api_name] = []
            
            # Add current timestamp
            self.request_timestamps[api_name].append(now)

    def update_rate_limit(self, api_name, calls, period):
        """Update rate limit for a specific API"""
        with self.locks[api_name]:
            self.rates[api_name] = {"calls": calls, "period": period} 