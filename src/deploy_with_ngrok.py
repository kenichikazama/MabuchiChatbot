"""
Deployment script with ngrok for public access
Run this to deploy both FastAPI and Streamlit with ngrok tunnels
"""
import os
import subprocess
import sys
import time
from pyngrok import ngrok, conf
from dotenv import load_dotenv
import webbrowser

load_dotenv()

def setup_ngrok():
    """Setup ngrok with auth token"""
    auth_token = os.getenv("NGROK_AUTH_TOKEN")
    if auth_token:
        ngrok.set_auth_token(auth_token)
        print("✓ Ngrok authenticated")
    else:
        print("⚠ Warning: NGROK_AUTH_TOKEN not found in .env")
        print("  You can get a free token at: https://dashboard.ngrok.com/get-started/your-authtoken")
        print("  Free tier allows 1 tunnel at a time")

def start_fastapi(port=8000):
    """Start FastAPI server"""
    print(f"\n🚀 Starting FastAPI server on port {port}...")
    fastapi_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)  # Wait for server to start
    print(f"✓ FastAPI server started")
    return fastapi_process

def start_streamlit(port=8501):
    """Start Streamlit app"""
    print(f"\n🎨 Starting Streamlit UI on port {port}...")
    streamlit_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)  # Wait for server to start
    print(f"✓ Streamlit UI started")
    return streamlit_process

def create_ngrok_tunnel(port, name):
    """Create ngrok tunnel"""
    print(f"\n🌐 Creating ngrok tunnel for {name}...")
    try:
        tunnel = ngrok.connect(port, bind_tls=True)
        public_url = tunnel.public_url
        print(f"✓ {name} tunnel created: {public_url}")
        return tunnel, public_url
    except Exception as e:
        print(f"✗ Error creating tunnel: {str(e)}")
        return None, None

def update_streamlit_api_url(api_url):
    """Update API URL in Streamlit app"""
    print(f"\n📝 Updating Streamlit API URL to {api_url}...")
    
    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Replace API_URL
    updated_content = content.replace(
        'API_URL = "http://localhost:8000"',
        f'API_URL = "{api_url}"'
    )
    
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(updated_content)
    
    print("✓ API URL updated")

def main():
    """Main deployment function"""
    print("=" * 60)
    print("🎉 Year-End Party Chatbot - Deployment Script")
    print("=" * 60)
    
    # Check if running in correct directory
    if not os.path.exists("main.py") or not os.path.exists("app.py"):
        print("✗ Error: main.py or app.py not found!")
        print("  Please run this script from the project root directory")
        sys.exit(1)
    
    # Setup ngrok
    setup_ngrok()
    
    # Start FastAPI
    fastapi_process = start_fastapi(port=8000)
    
    # Create ngrok tunnel for FastAPI
    api_tunnel, api_url = create_ngrok_tunnel(8000, "FastAPI")
    
    if not api_url:
        print("✗ Failed to create API tunnel. Exiting...")
        fastapi_process.terminate()
        sys.exit(1)
    
    # Update Streamlit with ngrok API URL
    update_streamlit_api_url(api_url)
    
    # Start Streamlit
    streamlit_process = start_streamlit(port=8501)
    
    # Create ngrok tunnel for Streamlit
    ui_tunnel, ui_url = create_ngrok_tunnel(8501, "Streamlit UI")
    
    if not ui_url:
        print("✗ Failed to create UI tunnel. Exiting...")
        fastapi_process.terminate()
        streamlit_process.terminate()
        ngrok.disconnect(api_tunnel.public_url)
        sys.exit(1)
    
    # Print summary
    print("\n" + "=" * 60)
    print("✅ Deployment Successful!")
    print("=" * 60)
    print(f"\n📍 FastAPI Backend: {api_url}")
    print(f"   - Health check: {api_url}/")
    print(f"   - API docs: {api_url}/docs")
    
    print(f"\n🎨 Streamlit UI: {ui_url}")
    print(f"   - Share this URL with users for testing!")
    
    print("\n" + "=" * 60)
    print("💡 Tips:")
    print("   - Keep this terminal open to keep the services running")
    print("   - Press Ctrl+C to stop all services")
    print("   - Check ngrok dashboard: https://dashboard.ngrok.com/")
    print("=" * 60)
    
    # Open browser
    print("\n🌐 Opening browser...")
    webbrowser.open(ui_url)
    
    try:
        print("\n⏳ Services are running. Press Ctrl+C to stop...\n")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down services...")
        
        # Cleanup
        fastapi_process.terminate()
        streamlit_process.terminate()
        ngrok.kill()
        
        print("✓ All services stopped")
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()