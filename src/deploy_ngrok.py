"""
Simple deployment script with ngrok
"""
import os
import subprocess
import sys
import time
from pyngrok import ngrok
from dotenv import load_dotenv
import webbrowser

load_dotenv()

def main():
    print("=" * 60)
    print("🎉 Year-End Party Chatbot - Deploy")
    print("=" * 60)
    
    # Setup ngrok
    auth_token = os.getenv("NGROK_AUTH_TOKEN")
    if auth_token:
        ngrok.set_auth_token(auth_token)
        print("✓ Ngrok authenticated")
    else:
        print("\n⚠ Warning: No NGROK_AUTH_TOKEN found")
        print("  Get free token at: https://dashboard.ngrok.com/")
        print("  Or run locally: streamlit run app.py\n")
    
    # Start Streamlit
    print("\n🚀 Starting Streamlit...")
    streamlit_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app_hybrid.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(5)  # Wait for Streamlit to start
    print("✓ Streamlit started")
    
    # Create ngrok tunnel
    if auth_token:
        print("\n🌐 Creating public URL with ngrok...")
        try:
            tunnel = ngrok.connect(8501, bind_tls=True)
            public_url = tunnel.public_url
            
            print("\n" + "=" * 60)
            print("✅ Deployment Successful!")
            print("=" * 60)
            print(f"\n🎨 Public URL: {public_url}")
            print("\n💡 Share this URL with users!")
            print("=" * 60)
            
            # Open browser
            webbrowser.open(public_url)
            
        except Exception as e:
            print(f"\n⚠ Ngrok error: {e}")
            print("Running on local: http://localhost:8501")
            webbrowser.open("http://localhost:8501")
    else:
        print("\n🌐 Running locally: http://localhost:8501")
        webbrowser.open("http://localhost:8501")
    
    try:
        print("\n⏳ Press Ctrl+C to stop...\n")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping...")
        streamlit_process.terminate()
        if auth_token:
            ngrok.kill()
        print("✓ Stopped. Goodbye!")

if __name__ == "__main__":
    main()