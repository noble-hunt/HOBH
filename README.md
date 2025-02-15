git clone https://github.com/noble-hunt/HOBH.git
cd HOBH
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your API keys and database configuration
```

4. Start the backend servers
```bash
# Start API server
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Start Streamlit dashboard
streamlit run main.py
```

### iOS Development Setup
1. Open the Xcode project
```bash
cd ios
open OlympicWeightlifting.xcodeproj