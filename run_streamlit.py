#!/usr/bin/env python3
import subprocess
import sys
import time

def run_streamlit():
    """Запуск Streamlit приложения"""
    try:
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            "market_breadth_app.py",
            "--server.port=8501",
            "--server.address=0.0.0.0", 
            "--browser.gatherUsageStats=false",
            "--server.headless=true"
        ]
        
        print("Starting Streamlit on port 8501...")
        process = subprocess.Popen(cmd)
        
        # Держим процесс активным
        try:
            process.wait()
        except KeyboardInterrupt:
            print("Stopping Streamlit...")
            process.terminate()
            process.wait()
            
    except Exception as e:
        print(f"Error starting Streamlit: {e}")
        return False

if __name__ == "__main__":
    run_streamlit()