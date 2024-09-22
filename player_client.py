# player_client.py
import asyncio
import websockets
import arcade
import json

class PlayerClient(arcade.Window):
    def __init__(self):
        super().__init__(800, 600, "Player Client")
        self.websocket = None
        self.loop = asyncio.get_event_loop()
        self.connected = False
        self.player_id = None

    async def connect(self):
        try:
            self.websocket = await websockets.connect('ws://localhost:12345')
            await self.websocket.send(json.dumps({'action': 'authenticate', 'role': 'player'}))
            self.connected = True
            asyncio.ensure_future(self.listen())
        except Exception as e:
            print(f"Connection error: {e}")

    async def listen(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.process_message(data)
        except websockets.ConnectionClosed:
            print("Connection closed")

    async def process_message(self, data):
        action = data.get('action')
        if action == 'authenticated':
            self.player_id = data.get('player_id')
            print(f"Authenticated as Player {self.player_id}.")
        elif action == 'error':
            print(f"Error: {data.get('message')}")
        # Handle other actions and game updates

    def on_draw(self):
        arcade.start_render()
        # Draw the player interface here

    def on_mouse_press(self, x, y, button, modifiers):
        # Handle player actions and send to server
        pass

    def run(self):
        self.loop.run_until_complete(self.connect())
        arcade.run()

if __name__ == "__main__":
    client = PlayerClient()
    client.run()
