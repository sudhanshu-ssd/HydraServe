import time

class RateLimiter():
    def __init__(self,max_rpm = 50,max_rpd = 800,max_tokens_minute = 4000,max_tokens_day = 100000): #i could have used database but lets be real we gonna use redis later 
        self.max_rpm = max_rpm
        self.max_rpd = max_rpd
        self.max_tokens_minute = max_tokens_minute
        self.max_tokens_day = max_tokens_day



    async def is_allowed(self,project_id,freq_dict) -> bool:
        window = freq_dict[project_id]
        start = time.time()

        last_minute = [t for t in window if start - t[0] < 60]

        last_day = [t for t in window if start - t[0] < 86400] #this looks so slow and inefficient

        freq_dict[project_id] = last_day  # Update the frequency dictionary to only keep relevant timestamps

        if len(last_minute) >= self.max_rpm or len(last_day) >= self.max_rpd:
            return False
        if sum(t[1] for t in last_minute) >= self.max_tokens_minute or sum(t[1] for t in last_day) >= self.max_tokens_day:
            return False

        return True
    
    async def update_usage(self,project_id,total_tokens,freq_dict):
        freq_dict[project_id].append((time.time(), total_tokens))