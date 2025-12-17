#!/usr/bin/env fish

# Keep-Alive Script for Render Services
# Pings backend and frontend every 10 minutes

set BACKEND_URL "https://backend-3snj.onrender.com"
set FRONTEND_URL "https://fontend-s557.onrender.com"
set PING_INTERVAL 600  # 10 minutes in seconds

echo "================================================================================"
echo "🔄 Render Keep-Alive Service Started"
echo "================================================================================"
echo "Backend URL: $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo "Ping Interval: "(math $PING_INTERVAL / 60)" minutes"
echo "================================================================================"
echo ""
echo "Press Ctrl+C to stop"
echo ""

set ping_count 0

while true
    set ping_count (math $ping_count + 1)
    
    echo ""
    echo "================================================================================"
    echo "Ping #$ping_count - "(date '+%Y-%m-%d %H:%M:%S')
    echo "================================================================================"
    
    # Ping backend
    echo "Pinging backend..."
    set backend_status (curl -s -o /dev/null -w "%{http_code}" --max-time 30 $BACKEND_URL/health 2>/dev/null)
    if test "$backend_status" = "200"
        echo "✅ Backend: OK (Status: $backend_status)"
    else
        echo "⚠️  Backend: Status $backend_status"
    end
    
    # Ping frontend
    echo "Pinging frontend..."
    set frontend_status (curl -s -o /dev/null -w "%{http_code}" --max-time 30 $FRONTEND_URL 2>/dev/null)
    if test "$frontend_status" = "200"
        echo "✅ Frontend: OK (Status: $frontend_status)"
    else
        echo "⚠️  Frontend: Status $frontend_status"
    end
    
    # Next ping time
    set next_ping (date -d "+"$PING_INTERVAL" seconds" '+%Y-%m-%d %H:%M:%S' 2>/dev/null; or date -v +"$PING_INTERVAL"S '+%Y-%m-%d %H:%M:%S' 2>/dev/null)
    echo ""
    echo "Next ping at: $next_ping"
    
    # Sleep
    sleep $PING_INTERVAL
end
