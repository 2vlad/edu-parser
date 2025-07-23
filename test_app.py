#!/usr/bin/env python3
"""
Minimal test app to verify Railway deployment works.
"""

import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def test():
    port_env = os.environ.get('PORT', 'not-set')
    web_port_env = os.environ.get('WEB_PORT', 'not-set')
    
    return f"""
    <h1>🚀 RAILWAY TEST APP WORKING! 🚀</h1>
    <p>Version: v2.1.4-test-app</p>
    <p>PORT env var: {port_env}</p>
    <p>WEB_PORT env var: {web_port_env}</p>
    <p>If you see this, Railway deployment is working!</p>
    """

if __name__ == '__main__':
    web_port = os.environ.get('WEB_PORT', '8080')
    port = os.environ.get('PORT', web_port)
    
    print(f"🚀 TEST APP STARTING")
    print(f"🚀 PORT env: {os.environ.get('PORT')}")
    print(f"🚀 WEB_PORT env: {os.environ.get('WEB_PORT')}")
    
    # Try to use a safe port
    try:
        if port == '$PORT' or port == "'$PORT'":
            port = 8080
        else:
            port = int(port)
    except:
        port = 8080
    
    print(f"🚀 Starting on port: {port}")
    app.run(host='0.0.0.0', port=port)