# Captain of Industry - AI Mod

This project integrates Captain of Industry with an external Python AI brain. The C# mod sends game state data (currently, a list of all products and their stored quantities) to a Python server, which can then send commands back to the game.

## Components

1.  **C# Mod (`src/CoI_AI_Mod`):** The in-game component that runs as a Captain of Industry mod. It gathers data and communicates with the Python server.
2.  **Python Server (`python_ai`):** A simple Flask server that listens for data from the mod. This is where you will implement your AI logic.

## Prerequisites

### For the Mod (C#):

*   [.NET 6 SDK](https://dotnet.microsoft.com/en-us/download/dotnet/6.0) or newer.
*   A copy of Captain of Industry.
*   An environment variable named `COI_ROOT` pointing to your game's root directory (e.g., `C:/Steam/steamapps/common/Captain of Industry`). This is required for the project to find the game's DLLs for compilation.

### For the AI Server (Python):

*   [Python 3.8+](https://www.python.org/downloads/)
*   `pip` for installing packages.

## Step 1: Build the C# Mod

1.  Open a terminal or command prompt.
2.  Navigate to the C# project directory:
    ```sh
    cd CoI_AI_Project/src/CoI_AI_Mod
    ```
3.  Build the project in `Release` mode. This will compile your mod into a DLL file.
    ```sh
    dotnet build -c Release
    ```
    This command reads the `.csproj` file, restores dependencies (like the game's own libraries, located via the `COI_ROOT` variable), and compiles the code.

## Step 2: Install the Mod

1.  After a successful build, find the compiled DLL at `CoI_AI_Project/src/CoI_AI_Mod/bin/Release/net471/CoI_AI_Mod.dll`.
2.  Navigate to your Captain of Industry mods directory. It is typically located at:
    *   **Windows:** `%APPDATA%/Captain of Industry/Mods`
    *   **Linux:** `~/.config/Captain of Industry/Mods`
3.  Inside the `Mods` directory, create a new folder named `CoI_AI_Mod`.
4.  Copy the `CoI_AI_Mod.dll` file into this new folder. The final path should look like:
    `.../Mods/CoI_AI_Mod/CoI_AI_Mod.dll`
5.  Launch Captain of Industry, go to `Settings -> Miscellaneous`, and ensure "Enable mods" is checked. Restart the game if you had to change this setting.
6.  When starting a new game, you should see `Captain of Industry AI Mod` in the list of available mods. Make sure it is enabled.

## Step 3: Run the Python AI Server

1.  Open a new terminal.
2.  Navigate to the Python project directory:
    ```sh
    cd CoI_AI_Project/python_ai
    ```
3.  Install the necessary package:
    ```sh
    pip install -r requirements.txt
    ```
4.  Run the server:
    ```sh
    python main.py
    ```
    The server will start and print that it is running on `http://0.0.0.0:8000/`. Keep this terminal open while you play the game.

## How it Works

1.  With the Python server running and the mod enabled in-game, start a new game.
2.  The mod will automatically attempt to connect to the Python server every 2 seconds (approximately).
3.  The C# mod gathers all product quantities, serializes them to JSON, and POSTs them to the Python server.
4.  The Python server receives the data, prints it to its console, and sends back a JSON response.
5.  The in-game mod receives this response and logs it to the game's console and log file, confirming the two-way communication.

You can now modify `python_ai/main.py` to implement your AI logic based on the data you receive from the game.
