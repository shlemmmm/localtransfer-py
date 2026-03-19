from secrets import choice
from time import perf_counter
from socket import create_connection

class Password:
    CHAR_SET = [
        'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 
        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
        '!', '#', '$', '%', '&', '*', '.', '/', ':', '=', '?', '@', '_'
    ]
    _CHAR_SET_LEN = len(CHAR_SET)

    def __init__(self, length, password=None):
        self.password = self.generate_password(length) if password is None else password
        self.avg_rtt = self.measure_latency()
        self.attacker_speed = int(1 / self.avg_rtt)
        self.time_left_seconds = self.time_until_death(len(self.password), self.attacker_speed)

        # print(f"--- Theoretical Attack Analysis ---")
        # print(f"Generated Password: \t{self.password}")
        # print(f"Local Max Speed:    \t{self.attacker_speed} rq/sec")
        # print(f"Total Combinations: \t{self.calculate_possibilities(len(self.password))}")
        # print(f"Time to Crack:      \t{self.time_left_seconds} seconds")
        
    def measure_latency(self, host="127.0.0.1", port=5000):
        try:
            times = []
            for _ in range(5): 
                start = perf_counter()
                with create_connection((host, port), timeout=0.5):
                    pass
                times.append(perf_counter() - start)
            return sum(times) / len(times)
        except (ConnectionRefusedError, TimeoutError, OSError):
            return 0.0002 

    def generate_password(self, length: int = 8) -> str:
        return ''.join(choice(self.CHAR_SET) for _ in range(length))

    def calculate_possibilities(self, k: int = 8) -> int:
        return self._CHAR_SET_LEN ** k

    def time_until_death(self, password_length: int, attacker_speed: int):
        total_combinations = self.calculate_possibilities(password_length)
        seconds = int((total_combinations/2) / attacker_speed)
    
        MAX_SYSTEM_SECONDS = 3153600000 
        return min(seconds, MAX_SYSTEM_SECONDS)

    def get_analysis(self, password: str): # test
        avg_rtt = self.measure_latency()
        attacker_speed = int(1 / avg_rtt)
        time_left = self.time_until_death(len(password), attacker_speed)
        return time_left