import sys
import time
import random
import asyncio
from collections import defaultdict

class TabooGameServer:
    def __init__(self, port, challenge_file, num_turns, turn_length_secs=60):
        self.port = port
        self.challenge_file = challenge_file
        self.num_turns = num_turns
        self.players = []
        self.turn_length_secs = turn_length_secs
        self.teams = {"A": [], "B": []}
        self.current_turn = 0
        self.score = defaultdict(int)
        self.challenge_index = 0
        self.challenges = []
        self.load_challenges()
        self.admin_console = sys.stdout

    def load_challenges(self):
        with open(self.challenge_file, 'r') as file:
            for line in file:
                word, *forbidden = line.strip().split(',')
                self.challenges.append((word, forbidden))
        random.shuffle(self.challenges)

    async def handle_player(self, reader, writer):
        try:
            writer.write(b"Enter your name: ")
            await writer.drain()
            data = await reader.read(1024)
            name = data.decode().strip()
        except Exception:
            return
        # Check if this player is reconnecting
        for player in self.players:
            if player["name"] == name:
                player["reader"] = reader
                player["writer"] = writer
                player["connected"] = True
                await self.send_to_player(player, "Welcome back! You have reconnected.")
                await self.broadcast(f"{name} reconnected.")
                return
        player = {"name": name, "writer": writer, "reader": reader, "connected": True}
        team = self.assign_team(player)
        self.players.append(player)
        await self.send_to_player(player, f"You are on team {team}")
        self.send_to_admin(f"{name} joined team {team}")
        await self.broadcast(self.teams_and_users())
        self.send_to_admin("Type 'start' to begin the game.")
        
    def assign_team(self, player):
        team = "A" if len(self.teams["A"]) <= len(self.teams["B"]) else "B"
        self.teams[team].append(player)
        return team

    def send_to_admin(self, message):
        if self.admin_console:
            self.admin_console.write(message)
            self.admin_console.write("\n")
            self.admin_console.flush()

    async def on_disconnect(self, player):
        player["connected"] = False
        await self.broadcast(f"{player['name']} has disconnected.")       

    async def send_to_player(self, player, message):
        try:
            if player["connected"]:
                player["writer"].write((message + "\n").encode())
                await player["writer"].drain()
        except Exception:
            await self.on_disconnect(player)

    async def broadcast(self, message):
        self.send_to_admin(message)
        for player in self.players:
            await self.send_to_player(player, message)
    
    async def read_from_player(self, player):
        try:
            data = await player["reader"].read(1024)
            return data.decode().strip()
        except Exception:
            await self.on_disconnect(player)

    async def get_valid_integer_from_player(self, player, prompt):
        while True:
            await self.send_to_player(player, prompt)
            try:
                response = await self.read_from_player(player)
                number = int(response)
                if number >= 0:
                    return number
                else:
                    await self.send_to_player(player, "Please enter a positive number.")
            except ValueError:
                await self.send_to_player(player, "Invalid input. Please enter a number.")

    def player_name(self, player):
        name = player["name"]
        if not player["connected"]:
            name += " (offline)"
        return name

    def teams_and_users(self):
        s = "Current teams and players:\n"
        s +=  "\n".join([
            f"Team {team} - Score: {self.score[team]} - Players: " + ", ".join(
                [self.player_name(player) for player in players]) for team, players in self.teams.items()])
        return s

    async def start_game(self):
        for turn in range(self.num_turns):
            self.current_turn += 1
            for team in ["A", "B"]:
                await self.play_turn(team)
        await self.end_game()

    async def setup_turn(self, team):
        cluegiver = self.teams[team][self.current_turn % len(self.teams[team])]
        observer = random.choice(self.teams["A"] if team == "B" else self.teams["B"])
        await self.broadcast(f"Round {self.current_turn} for team {team}: Cluegiver is {cluegiver['name']}, {observer['name']} from the other team is observing.")
        await self.broadcast(f"Waiting for {cluegiver['name']} to start the turn...")
        await self.send_to_player(observer, "You are the observer!")
        await self.send_to_player(observer, "Make sure the cluegiver does not use forbidden words!")
        await self.send_to_player(cluegiver, "You are the Cluegiver!")
        await self.send_to_player(cluegiver, f"You have {self.turn_length_secs} seconds to go through as many challenges as you can.")
        return cluegiver, observer

    async def wait_for_cluegiver_to_start(self, cluegiver, team):
        await self.send_to_player(cluegiver, "Type 'start' if you're ready...")
        while await self.read_from_player(cluegiver) != "start":
            await self.send_to_player(cluegiver, "Type 'start' if you're ready...")
        await self.broadcast(f"Round {self.current_turn} for team {team} has started!")

    async def execute_challenges(self, cluegiver, observer):
        start_time = time.time()
        while time.time() - start_time < self.turn_length_secs:
            challenge = self.challenges[self.challenge_index]
            word, forbidden = challenge
            await self.send_to_player(observer, f"Observer: The word is {word}. Forbidden: {', '.join(forbidden)}.")
            await self.send_to_player(cluegiver, f"Cluegiver: The word is {word}. Forbidden: {', '.join(forbidden)}.")
            await self.send_to_player(cluegiver, "Hit <enter> for next challenge.")
            try:
                data = await asyncio.wait_for(cluegiver["reader"].read(100), timeout=self.turn_length_secs - (time.time() - start_time))
                response = data.decode().strip()
            except asyncio.TimeoutError:
                break
            except Exception:
                await self.on_disconnect(cluegiver)
            finally:
                self.challenge_index += 1
                self.challenge_index %= len(self.challenges)        

    async def end_turn(self, cluegiver, observer, team):
        await self.send_to_player(cluegiver, "Time's up!")
        await self.send_to_player(observer, "Time's up!")
        await self.broadcast(f"Waiting for {observer['name']} to input the number of correct guesses...")
        correct_guesses = await self.get_valid_integer_from_player(observer, prompt="Please enter the number of correct guesses:")
        await self.broadcast(f"In round {self.current_turn} team {team} guessed {correct_guesses} correctly.")
        self.score[team] += correct_guesses
        await self.broadcast(self.teams_and_users())

    async def play_turn(self, team):
        cluegiver, observer = await self.setup_turn(team)
        await self.wait_for_cluegiver_to_start(cluegiver, team)
        await self.execute_challenges(cluegiver, observer)
        await self.end_turn(cluegiver, observer, team)

    async def end_game(self):
        result = "It's a tie"
        if self.score["A"] > self.score["B"]:
            result = "Team A won"
        elif self.score["B"] > self.score["A"]:
            result = "Team B won"
        await self.broadcast(f"The game is over - {result}! Thank you for playing!")
        for player in self.players:
            player["writer"].close()
        self.server_task.cancel()
        self.console_task.cancel()

    async def start_admin_console(self):
        self.send_to_admin("Admin console ready. Waiting for players to connect...")
        while self.current_turn == 0:
            line = await asyncio.to_thread(sys.stdin.readline)
            command = line.strip()
            if command == "start":
                await self.start_game()

    async def background_task(self):
        server = await asyncio.start_server(self.handle_player, "0.0.0.0", self.port)
        try:
            await server.serve_forever()
        except asyncio.CancelledError:
            server.close()
            await server.wait_closed()

    async def main(self):
        self.console_task = asyncio.create_task(self.start_admin_console())
        self.server_task = asyncio.create_task(self.background_task())
        try:
            await self.server_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python3 taboo_server.py <port> <challenge_file> <turns> <turn_length_secs>")
        sys.exit(1)
    port = int(sys.argv[1])
    challenge_file = sys.argv[2]
    num_turns = int(sys.argv[3])
    turn_length_secs = int(sys.argv[4])
    tgs = TabooGameServer(port, challenge_file, num_turns, turn_length_secs)
    asyncio.run(tgs.main())
