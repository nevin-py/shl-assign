# Keep-Alive Scripts for Render Services

These scripts prevent Render's free tier services from spinning down due to inactivity by pinging them every 10 minutes.

## Files

- `keep_alive.py` - Python version (cross-platform)
- `keep_alive.fish` - Fish shell version (for Fish users)

## Setup

### Update Frontend URL

Before running, update the `FRONTEND_URL` in the script with your actual frontend URL from Render.

**In `keep_alive.py`:**
```python
FRONTEND_URL = "https://your-frontend-url.onrender.com"
```

**In `keep_alive.fish`:**
```fish
set FRONTEND_URL "https://your-frontend-url.onrender.com"
```

## Usage

### Python Version

```bash
# Run in foreground
python keep_alive.py

# Run in background (Linux/Mac)
nohup python keep_alive.py > keep_alive.log 2>&1 &

# Run in background (Fish shell)
nohup python keep_alive.py > keep_alive.log 2>&1 &
disown
```

### Fish Shell Version

```bash
# Run in foreground
./keep_alive.fish

# Run in background
nohup ./keep_alive.fish > keep_alive.log 2>&1 &
disown
```

## What It Does

- Pings backend health endpoint: `https://backend-3snj.onrender.com/health`
- Pings frontend homepage: `https://your-frontend.onrender.com`
- Interval: Every 10 minutes (600 seconds)
- Displays status with timestamps
- Shows next ping time

## Output Example

```
================================================================================
🔄 Render Keep-Alive Service Started
================================================================================
Backend URL: https://backend-3snj.onrender.com
Frontend URL: https://shl-frontend.onrender.com
Ping Interval: 10 minutes
================================================================================

Press Ctrl+C to stop

================================================================================
Ping #1 - 2025-12-17 08:00:00
================================================================================
✅ Backend: OK (Status: 200, Time: 1.23s)
✅ Frontend: OK (Status: 200, Time: 0.85s)

Status: ✅ All services OK
Next ping at: 2025-12-17 08:10:00
```

## Notes

- **Render Free Tier**: Services spin down after 15 minutes of inactivity
- **Cold Start**: When spun down, first request takes 30-60 seconds to wake up
- **Keep-Alive**: This prevents spin-down by keeping services active
- **Cost**: Still free - you're just using the free tier continuously
- **Alternative**: Consider upgrading to paid tier to avoid this entirely

## Stopping the Script

Press `Ctrl+C` to stop the script gracefully.

If running in background:
```bash
# Find the process
ps aux | grep keep_alive

# Kill it
kill <PID>
```
