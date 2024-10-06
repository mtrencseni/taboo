# Python Taboo Game Server

A simple Python3-based Taboo game server using `asyncio` to provide a customizable multiplayer experience via Telnet.

## How to Run the Taboo Server

Running your custom Taboo server is straightforward. Follow these steps to set it up and start playing:

### 1. Clone the Repository and Navigate to the Directory

```bash
git clone https://github.com/yourusername/taboo_game_server.git
cd taboo_game_server
```

### 2. Prepare the `challenges.txt` File

Create a `challenges.txt` file containing Taboo words and their forbidden words in CSV format. For example:

```
Python,programming,language,code,snake
Eiffel Tower,Paris,France,landmark,iron
```

### 3. Run the Server

```bash
python3 taboo_server.py <port> <challenge_file> <turns> <turn_length_secs>
```

**Example**:

```bash
python3 taboo_server.py 12345 challenges.txt 10 60
```

- **12345**: The port number the server will listen on.
- **challenges.txt**: The file containing game challenges.
- **10**: The number of turns in the game.
- **60**: The length of each turn in seconds.

### 4. Connect Players

Players can connect to the server using Telnet or any similar terminal-based network client:

```bash
telnet localhost 12345
```

### 5. Start the Game

Once all players are connected, the admin can start the game by typing `start` in the server console.

---

## How to Play

### 1. Enter Your Name

Upon connecting, each player will be prompted to enter their name. The server will automatically assign players to Team A or Team B to keep teams balanced.

### 2. Team Assignments

Players are assigned to teams based on the current team sizes. This ensures fair and balanced gameplay.

### 3. Starting the Game

The admin starts the game by typing `start` in the server console. This initiates the first turn.

### 4. Gameplay Mechanics

- **Cluegiver**: A player is designated as the cluegiver for their team each turn. They receive a word and must describe it without using any forbidden words.
- **Observer**: A player from the opposing team acts as an observer to ensure the cluegiver adheres to the rules.
- **Challenges**: The cluegiver attempts to guide their teammates to guess the word within the allotted time, avoiding forbidden words.
- **Scoring**: After each turn, the observer inputs the number of correct guesses, and the team's score is updated accordingly.

### 5. End of Game

After all turns are completed, the server announces the winning team and closes all player connections.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

This README provides a comprehensive guide to setting up, running, and playing the Python Taboo Game Server. It includes clear instructions, code snippets for better understanding, and a structured flow to ensure users can easily get the server up and running.
