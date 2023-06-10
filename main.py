import asyncio
import random
from datetime import datetime

SERVER_HOST = 'localhost'
SERVER_PORT = 8888
NUMBER_OF_CLIENTS = 2 # Кол-во клиентов
MIN_CLIENT_INTERVAL = 0.3  # 300 мс
MAX_CLIENT_INTERVAL = 3.0  # 3000 мс
MIN_SERVER_INTERVAL = 0.1  # 100 мс
MAX_SERVER_INTERVAL = 1.0  # 1000 мс
KEEPALIVE_INTERVAL = 5  # 5 секунд
PROGRAM_DURATION = 300  # 5 минут (в секундах)

class Server:
    def __init__(self):
        self.clients = set()
        self.message_count = 0
        self.log_file = open('server.log', 'a')

    async def handle_client(self, reader, writer):
        client_id = len(self.clients) + 1
        self.clients.add(writer)
        while True:
            data = await reader.readline()
            if not data:
                break

            message = data.decode().strip()
            if random.random() < 0.1:
                # Игнорируем запрос
                log = f'{datetime.now()};{message};(проигнорировано)\n'
                self.log_file.write(log)
            else:
                # Отвечаем на запрос
                interval = random.uniform(MIN_SERVER_INTERVAL, MAX_SERVER_INTERVAL)
                await asyncio.sleep(interval)
                response = f'[{self.message_count}.{self.message_count}] PONG ({client_id})\n'
                log = f'{datetime.now()};{message};{datetime.now()};{response}'
                self.log_file.write(log)

                writer.write(response.encode())

                self.message_count += 1

        self.clients.remove(writer)
        writer.close()

    async def send_keepalive(self):
        while True:
            await asyncio.sleep(KEEPALIVE_INTERVAL)
            response = f'[{self.message_count}] keepalive\n'
            log = f'{datetime.now()};;{datetime.now()};{response}'
            self.log_file.write(log)

            for writer in self.clients:
                writer.write(response.encode())

            self.message_count += 1

    async def run(self):
        server = await asyncio.start_server(
            self.handle_client, SERVER_HOST, SERVER_PORT)

        asyncio.create_task(self.send_keepalive())

        async with server:
            await server.serve_forever()


class Client:
    def __init__(self, client_id):
        self.client_id = client_id
        self.log_file = open(f'client{client_id}.log', 'a')

    async def run(self):
        reader, writer = await asyncio.open_connection(SERVER_HOST, SERVER_PORT)
        count = 0

        while True:
            interval = random.uniform(MIN_CLIENT_INTERVAL, MAX_CLIENT_INTERVAL)
            await asyncio.sleep(interval)
            message = f'[{count}] PING\n'
            log = f'{datetime.now()};{message}'
            self.log_file.write(log)

            writer.write(message.encode())

            try:
                data = await asyncio.wait_for(reader.readline(), timeout=1)
                response = data.decode().strip()
            except asyncio.TimeoutError:
                response = '(таймаут)'

            log = f'{datetime.now()};{message};{datetime.now()};{response}\n'
            self.log_file.write(log)

            count += 1


async def stop_program():
    await asyncio.sleep(PROGRAM_DURATION)
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    for task in tasks:
        task.cancel()


async def main():
    server = Server()
    clients = [Client(i + 1) for i in range(NUMBER_OF_CLIENTS)]

    server_task = asyncio.create_task(server.run())
    client_tasks = [asyncio.create_task(client.run()) for client in clients]
    stop_program_task = asyncio.create_task(stop_program())

    await asyncio.gather(server_task, *client_tasks, stop_program_task, return_exceptions=True)

    server.log_file.close()
    for client in clients:
        client.log_file.close()


if __name__ == '__main__':
    asyncio.run(main())
