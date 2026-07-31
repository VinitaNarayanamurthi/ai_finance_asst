# AI Finance Assistant - Deployment Guide

## ⚠️ Docker Not Installed?

**If you see "'docker' is not recognized" error, you have two options:**

### Option A: Run Without Docker (Recommended for Quick Testing)

You already have Python working! Simply run:

```cmd
cd C:\Users\vinit\Documents\agentic_ai\capstone_project\ai_finance_asst

# Ensure .env file exists with your API keys
# OPENAI_API_KEY=your_key_here
# ALPHA_VANTAGE_API_KEY=your_key_here

# Run the orchestrator
python agent\orchestrator.py

# Or test individual agents
python agent\finance_qa_agent.py
python agent\portfolio_agent.py
python agent\market_analysis_agent.py
python agent\news_synthesizer_agent.py
```

**No Docker installation needed!** Your Python environment is already configured.

### Option B: Install Docker Desktop (For Containerized Deployment)

Follow the installation steps below.

---

## Prerequisites (For Docker Deployment)

- **Docker Desktop for Windows** (version 20.10+)
  - Download from: https://www.docker.com/products/docker-desktop/
  - After installation, restart your computer
  - Verify installation: `docker --version` and `docker compose version`
- API Keys: OpenAI and Alpha Vantage

### Installing Docker Desktop on Windows

**Complete Step-by-Step Installation Guide:**

#### Step 1: Check System Requirements
- Windows 10 64-bit: Pro, Enterprise, or Education (Build 19041 or higher)
- OR Windows 11 64-bit
- Hardware virtualization enabled in BIOS (usually enabled by default)

#### Step 2: Download Docker Desktop
1. Open your web browser
2. Go to: **https://www.docker.com/products/docker-desktop/**
3. Click the **"Download for Windows"** button
4. Save the file (Docker Desktop Installer.exe) - approximately 500MB

#### Step 3: Install Docker Desktop
1. **Locate** the downloaded file (usually in Downloads folder)
2. **Right-click** on `Docker Desktop Installer.exe`
3. **Select** "Run as administrator"
4. In the installation wizard:
   - ✅ Check **"Use WSL 2 instead of Hyper-V"** (recommended)
   - ✅ Check **"Add shortcut to desktop"**
   - Click **"OK"** to begin installation
5. **Wait** for installation to complete (5-10 minutes)
6. Click **"Close and restart"** when prompted

#### Step 4: Complete Windows Restart
- **Important**: You MUST restart your computer for Docker to work
- Save all your work before restarting
- After restart, Docker Desktop may start automatically

#### Step 5: Start Docker Desktop
1. **Find Docker Desktop** in Start Menu or Desktop
2. **Click** to launch (may take 1-2 minutes first time)
3. **Accept** the Docker Subscription Service Agreement
4. **Choose** configuration:
   - Select "Use recommended settings"
   - Click "Finish"

#### Step 6: Wait for Docker Engine to Start
- Look for the **whale icon** in system tray (bottom-right corner)
- Wait until it shows "Docker Desktop is running" (green status)
- This may take 2-3 minutes the first time

#### Step 7: Verify Installation
Open **Command Prompt** and run these commands:

```cmd
docker --version
```
Expected output: `Docker version 24.x.x, build xxxxxxx`

```cmd
docker compose version
```
Expected output: `Docker Compose version v2.x.x`

```cmd
docker run hello-world
```
Expected output: `Hello from Docker!` message

#### Step 8: Configure Docker (Optional)
1. **Right-click** the Docker whale icon in system tray
2. **Click** "Settings"
3. Recommended settings:
   - **General**: Enable "Start Docker Desktop when you log in"
   - **Resources**: Allocate at least 4GB RAM and 2 CPUs
   - **Docker Engine**: Leave default settings

#### Troubleshooting Installation

**Issue: "WSL 2 installation is incomplete"**
- Solution: Install WSL 2 by running in PowerShell (as Administrator):
  ```powershell
  wsl --install
  ```
- Restart computer and try Docker Desktop again

**Issue: "Hardware assisted virtualization is disabled"**
- Solution: Enable virtualization in BIOS:
  1. Restart computer
  2. Press F2/F10/DEL during startup (varies by manufacturer)
  3. Find "Virtualization Technology" or "Intel VT-x" or "AMD-V"
  4. Enable it
  5. Save and exit BIOS

**Issue: Docker Desktop won't start**
- Solution 1: Restart Docker Desktop from Start Menu
- Solution 2: Restart your computer
- Solution 3: Uninstall and reinstall Docker Desktop

**Issue: "Docker daemon is not running"**
- Solution: Open Docker Desktop application - it must be running for commands to work

**Need Help?**
- Docker Desktop Documentation: https://docs.docker.com/desktop/install/windows-install/
- WSL 2 Installation Guide: https://docs.microsoft.com/en-us/windows/wsl/install

---

#### After Successful Installation

Once Docker is installed and verified, you can proceed with building and running the AI Finance Assistant:

```cmd
cd C:\Users\vinit\Documents\agentic_ai\capstone_project\ai_finance_asst
docker build -t ai-finance-asst:test .
docker compose up
```

### Alternative: Run Without Docker

If you prefer not to use Docker, you can run the application directly:

```bash
# Install dependencies
pip install -r requirements_new.txt
pip install langchain-openai pandas numpy matplotlib seaborn openpyxl requests python-dotenv

# Set environment variables (create .env file with your API keys)
# Then run the orchestrator
python agent/orchestrator.py
```

## Quick Start

### 1. Set Environment Variables

Create a `.env` file in the `ai_finance_asst` directory:

```bash
OPENAI_API_KEY=your_openai_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
```

### 2. Build and Run with Docker Compose

**For Docker Compose V2 (modern Docker Desktop - recommended):**
```bash
# Build the Docker image
docker compose build

# Start the container
docker compose up -d

# View logs
docker compose logs -f

# Stop the container
docker compose down
```

**For Docker Compose V1 (older installations):**
```bash
# Build the Docker image
docker-compose build

# Start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### 3. Alternative: Build and Run with Docker

```bash
# Build the image
docker build -t ai-finance-asst .

# Run the container
docker run -d \
  --name ai-finance-assistant \
  -e OPENAI_API_KEY=your_openai_api_key \
  -e ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key \
  -v $(pwd)/analysis_output:/app/analysis_output \
  -v $(pwd)/chroma_langchain_db:/app/chroma_langchain_db \
  -v $(pwd)/docs:/app/docs \
  -v $(pwd)/tools:/app/tools \
  -p 8000:8000 \
  ai-finance-asst

# View logs
docker logs -f ai-finance-assistant

# Stop and remove
docker stop ai-finance-assistant
docker rm ai-finance-assistant
```

## Directory Structure

The following directories are mounted as volumes:

- `analysis_output/` - Portfolio analysis results and charts
- `chroma_langchain_db/` - Vector database for RAG
- `docs/` - Financial documents for knowledge base
- `tools/` - Portfolio analyzer and sample data

## Accessing the Application

Once running, the orchestrator will execute with the default query. To customize:

1. Modify `agent/orchestrator.py` with your query
2. Rebuild and restart the container

## Troubleshooting

### Check container status
```bash
docker ps
docker compose ps
```

### View container logs
```bash
docker logs ai-finance-assistant
docker compose logs
```

### Execute commands inside container
```bash
docker exec -it ai-finance-assistant bash
```

### Rebuild after code changes
```bash
docker compose down
docker compose build --no-cache
docker compose up -d
```

## Production Considerations

1. **Security**: Never commit `.env` file with real API keys
2. **Volumes**: Ensure proper permissions for mounted volumes
3. **Resources**: Monitor container memory/CPU usage
4. **Logging**: Configure proper log rotation
5. **Updates**: Regularly update base images for security patches

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| OPENAI_API_KEY | Yes | OpenAI API key for LLM |
| ALPHA_VANTAGE_API_KEY | Yes | Alpha Vantage API key for market data |

## Port Mapping

- `8000` - Main application port (for future API/web interface)

## Testing Locally with Docker

### Step-by-Step Local Testing

1. **Ensure Docker Desktop is running**:
   - Open Docker Desktop application
   - Wait for the whale icon to show "Docker Desktop is running"

2. **Navigate to the project directory**:
   ```cmd
   cd C:\Users\vinit\Documents\agentic_ai\capstone_project\ai_finance_asst
   ```

3. **Create .env file** (if not exists):
   ```cmd
   # Create .env file in the ai_finance_asst directory
   echo OPENAI_API_KEY=your_key_here > .env
   echo ALPHA_VANTAGE_API_KEY=your_key_here >> .env
   ```

4. **Build the Docker image**:
   ```cmd
   docker build -t ai-finance-asst:test .
   ```
   This may take 5-10 minutes the first time.

5. **Run the container**:
   ```cmd
   docker run --rm ^
     --name ai-finance-test ^
     -e OPENAI_API_KEY=%OPENAI_API_KEY% ^
     -e ALPHA_VANTAGE_API_KEY=%ALPHA_VANTAGE_API_KEY% ^
     -v %cd%\analysis_output:/app/analysis_output ^
     -v %cd%\chroma_langchain_db:/app/chroma_langchain_db ^
     -v %cd%\docs:/app/docs ^
     -v %cd%\tools:/app/tools ^
     ai-finance-asst:test
   ```

   Or with docker compose:
   ```cmd
   docker compose up
   ```

6. **View the output**:
   - The orchestrator will run and display results in the terminal
   - Check `analysis_output/` folder for generated charts

7. **Test different queries**:
   - Edit `agent/orchestrator.py` line ~265 to change the user_input
   - Rebuild: `docker build -t ai-finance-asst:test .`
   - Rerun: `docker compose up` or the docker run command above

8. **Access container logs**:
   ```cmd
   # If running in detached mode (-d flag)
   docker logs ai-finance-test -f
   ```

9. **Execute commands inside container**:
   ```cmd
   docker exec -it ai-finance-test bash
   # Inside container:
   python agent/finance_qa_agent.py
   python agent/portfolio_agent.py
   ```

10. **Stop and cleanup**:
    ```cmd
    # Stop container
    docker stop ai-finance-test
    
    # Remove container
    docker rm ai-finance-test
    
    # Remove image
    docker rmi ai-finance-asst:test
    ```

### Quick Test Commands

**Test Finance QA Agent**:
```cmd
docker run --rm -e OPENAI_API_KEY=%OPENAI_API_KEY% ai-finance-asst:test python agent/finance_qa_agent.py
```

**Test Portfolio Agent**:
```cmd
docker run --rm -e OPENAI_API_KEY=%OPENAI_API_KEY% -v %cd%\tools:/app/tools ai-finance-asst:test python agent/portfolio_agent.py
```

**Test Market Analysis Agent**:
```cmd
docker run --rm -e OPENAI_API_KEY=%OPENAI_API_KEY% -e ALPHA_VANTAGE_API_KEY=%ALPHA_VANTAGE_API_KEY% ai-finance-asst:test python agent/market_analysis_agent.py
```

**Test News Synthesizer Agent**:
```cmd
docker run --rm -e OPENAI_API_KEY=%OPENAI_API_KEY% -e ALPHA_VANTAGE_API_KEY=%ALPHA_VANTAGE_API_KEY% ai-finance-asst:test python agent/news_synthesizer_agent.py
```

### Troubleshooting Local Testing

**Issue: "Docker daemon is not running"**
- Solution: Start Docker Desktop application

**Issue: "Cannot connect to Docker daemon"**
- Solution: Ensure Docker Desktop is fully started (green whale icon)

**Issue: Build fails with "no space left on device"**
- Solution: Clean up Docker: `docker system prune -a`

**Issue: Volume mount errors**
- Solution: Ensure paths exist and use absolute paths in Windows format

**Issue: Environment variables not loading**
- Solution: Check .env file exists and has correct format (no quotes around values)

### Verify Docker Installation

```cmd
docker --version
docker compose version
docker info
docker run hello-world
```
